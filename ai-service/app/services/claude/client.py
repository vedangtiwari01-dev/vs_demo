import logging
import time
from typing import Dict, Any, Optional, List
from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import settings

logger = logging.getLogger(__name__)

class ClaudeClient:
    """
    Wrapper for Anthropic Claude API with retry logic, rate limiting, and cost tracking.
    """

    # Claude Sonnet pricing (as of Dec 2024)
    INPUT_TOKEN_COST = 0.003 / 1000  # $0.003 per 1K input tokens
    OUTPUT_TOKEN_COST = 0.015 / 1000  # $0.015 per 1K output tokens

    def __init__(self):
        """Initialize Claude client with API key from settings."""
        if not settings.ANTHROPIC_API_KEY or settings.ANTHROPIC_API_KEY == 'your-api-key-here':
            raise ValueError(
                "ANTHROPIC_API_KEY not configured. Please set your Claude API key in the .env file."
            )

        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.CLAUDE_MODEL
        self.max_tokens = settings.MAX_TOKENS
        self.temperature = settings.TEMPERATURE

        # Rate limiting state
        self.request_timestamps: List[float] = []
        self.rate_limit = settings.RATE_LIMIT_REQUESTS_PER_MINUTE

        # Cost tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

        logger.info(f"ClaudeClient initialized with model: {self.model}")

    def _check_rate_limit(self):
        """
        Check and enforce rate limiting using a sliding window.
        Raises RateLimitError if limit exceeded.
        """
        current_time = time.time()
        # Remove timestamps older than 1 minute
        self.request_timestamps = [
            ts for ts in self.request_timestamps if current_time - ts < 60
        ]

        if len(self.request_timestamps) >= self.rate_limit:
            wait_time = 60 - (current_time - self.request_timestamps[0])
            logger.warning(f"Rate limit reached. Waiting {wait_time:.2f} seconds.")
            time.sleep(wait_time)
            self.request_timestamps = []

        self.request_timestamps.append(current_time)

    def _track_usage(self, input_tokens: int, output_tokens: int):
        """Track token usage and calculate costs."""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

        cost = (input_tokens * self.INPUT_TOKEN_COST) + (output_tokens * self.OUTPUT_TOKEN_COST)
        self.total_cost += cost

        logger.info(
            f"Token usage - Input: {input_tokens}, Output: {output_tokens}, Cost: ${cost:.6f}"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((APIConnectionError, RateLimitError)),
        reraise=True
    )
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        json_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a response from Claude with retry logic.

        Args:
            prompt: The user prompt to send to Claude
            system: Optional system prompt for context
            max_tokens: Maximum tokens in response (default: from settings)
            temperature: Sampling temperature (default: from settings)
            json_mode: Whether to request JSON output format

        Returns:
            Dict containing:
                - text: Generated response text
                - input_tokens: Number of input tokens used
                - output_tokens: Number of output tokens generated
                - model: Model used
                - stop_reason: Why generation stopped

        Raises:
            APIError: If API call fails after retries
            RateLimitError: If rate limit is exceeded
        """
        self._check_rate_limit()

        try:
            # Prepare messages
            messages = [{"role": "user", "content": prompt}]

            # Add JSON instruction if requested
            if json_mode and system:
                system += "\n\nYou must respond with valid JSON only. Do not include any text outside the JSON structure."
            elif json_mode:
                system = "You must respond with valid JSON only. Do not include any text outside the JSON structure."

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature if temperature is not None else self.temperature,
                system=system or "",
                messages=messages
            )

            # Extract usage statistics
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            self._track_usage(input_tokens, output_tokens)

            # Extract text content
            text_content = ""
            for block in response.content:
                if block.type == "text":
                    text_content += block.text

            result = {
                "text": text_content,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": response.model,
                "stop_reason": response.stop_reason
            }

            logger.debug(f"Claude response received. Stop reason: {response.stop_reason}")
            return result

        except RateLimitError as e:
            logger.error(f"Rate limit error: {str(e)}")
            raise
        except APIConnectionError as e:
            logger.error(f"Connection error: {str(e)}")
            raise
        except APIError as e:
            logger.error(f"API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Claude: {str(e)}")
            raise

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get cumulative usage statistics.

        Returns:
            Dict containing:
                - total_input_tokens: Total input tokens used
                - total_output_tokens: Total output tokens generated
                - total_tokens: Sum of input and output tokens
                - total_cost: Total cost in USD
        """
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost": round(self.total_cost, 6)
        }

    def reset_usage_stats(self):
        """Reset usage statistics to zero."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        logger.info("Usage statistics reset")
