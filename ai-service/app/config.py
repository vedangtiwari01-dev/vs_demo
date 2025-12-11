import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    PORT: int = int(os.getenv('PORT', 8000))

    # Claude API Configuration
    ANTHROPIC_API_KEY: str = os.getenv('ANTHROPIC_API_KEY', '')
    CLAUDE_MODEL: str = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-5-20250929')
    MAX_TOKENS: int = int(os.getenv('MAX_TOKENS', 4096))
    TEMPERATURE: float = float(os.getenv('TEMPERATURE', 0.0))
    MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', 3))
    RETRY_DELAY_MS: int = int(os.getenv('RETRY_DELAY_MS', 1000))
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = int(os.getenv('RATE_LIMIT_REQUESTS_PER_MINUTE', 50))

settings = Settings()
