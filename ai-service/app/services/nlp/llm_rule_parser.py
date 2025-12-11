import json
import logging
import re
from typing import List, Dict, Any
from app.services.claude.client import ClaudeClient
from app.services.claude.prompts import format_sop_extraction_prompt
from app.services.nlp.rule_parser import RuleParser

logger = logging.getLogger(__name__)

def extract_json_from_text(text: str) -> str:
    """
    Extract JSON from text that might contain markdown code fences or extra text.

    Handles cases like:
    - ```json {...} ```
    - Some text before {...} some text after
    - Plain JSON: {...}
    """
    text = text.strip()

    # Try to find JSON in markdown code fence
    json_fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_fence_match:
        return json_fence_match.group(1)

    # Try to find JSON object directly (handle both {} and [])
    json_match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
    if json_match:
        return json_match.group(1)

    # Return as-is if no patterns match
    return text

class LLMRuleParser:
    """
    LLM-powered SOP rule extraction using Claude.
    Falls back to regex-based parser if LLM fails.
    """

    def __init__(self):
        """Initialize LLM rule parser with Claude client and fallback."""
        try:
            self.claude_client = ClaudeClient()
            logger.info("LLMRuleParser initialized with Claude")
        except ValueError as e:
            logger.warning(f"Claude client not available: {str(e)}")
            self.claude_client = None

        # Keep regex parser as fallback
        self.fallback_parser = RuleParser()

    def extract_rules(
        self,
        sop_text: str,
        use_llm: bool = True,
        fallback_on_error: bool = True
    ) -> Dict[str, Any]:
        """
        Extract rules from SOP text using Claude LLM.

        Args:
            sop_text: The full text of the SOP document
            use_llm: Whether to use LLM (True) or go straight to fallback (False)
            fallback_on_error: Whether to use fallback parser if LLM fails

        Returns:
            Dict containing:
                - rules: List of extracted rules
                - extraction_method: "llm" or "regex"
                - confidence: Overall confidence score (0-1)
                - warnings: Any issues encountered
        """
        if not use_llm or not self.claude_client:
            logger.info("Using fallback regex parser (LLM disabled or unavailable)")
            return self._extract_with_fallback(sop_text)

        try:
            logger.info("Extracting SOP rules with Claude LLM")

            # Format prompt
            prompt = format_sop_extraction_prompt(sop_text)

            # Call Claude
            response = self.claude_client.generate(
                prompt=prompt,
                system="You are an expert at analyzing compliance documents and extracting rules.",
                json_mode=True
            )

            # Extract and parse JSON response (handles markdown code fences)
            json_text = extract_json_from_text(response['text'])
            result = json.loads(json_text)

            # Validate response
            if not self._validate_rules(result):
                logger.warning("Invalid rule structure from Claude")
                if fallback_on_error:
                    return self._extract_with_fallback(sop_text)
                return {
                    'rules': [],
                    'extraction_method': 'llm',
                    'confidence': 0.0,
                    'warnings': ['Invalid response structure from LLM']
                }

            # Calculate confidence based on rule completeness
            confidence = self._calculate_confidence(result['rules'])

            logger.info(f"Extracted {len(result['rules'])} rules with confidence {confidence:.2%}")

            return {
                'rules': result['rules'],
                'extraction_method': 'llm',
                'confidence': confidence,
                'warnings': []
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {str(e)}")
            if fallback_on_error:
                return self._extract_with_fallback(sop_text)
            return {
                'rules': [],
                'extraction_method': 'llm',
                'confidence': 0.0,
                'warnings': ['Failed to parse LLM response']
            }

        except Exception as e:
            logger.error(f"Error extracting rules with Claude: {str(e)}")
            if fallback_on_error:
                return self._extract_with_fallback(sop_text)
            return {
                'rules': [],
                'extraction_method': 'llm',
                'confidence': 0.0,
                'warnings': [f'LLM extraction failed: {str(e)}']
            }

    def _extract_with_fallback(self, sop_text: str) -> Dict[str, Any]:
        """
        Extract rules using fallback regex parser.

        Args:
            sop_text: The full text of the SOP document

        Returns:
            Dict with same structure as extract_rules
        """
        logger.info("Using fallback regex-based rule extraction")

        try:
            rules = self.fallback_parser.extract_rules(sop_text)

            return {
                'rules': rules,
                'extraction_method': 'regex',
                'confidence': 0.6,  # Lower confidence for regex extraction
                'warnings': ['Used fallback regex parser instead of LLM']
            }
        except Exception as e:
            logger.error(f"Fallback parser also failed: {str(e)}")
            return {
                'rules': [],
                'extraction_method': 'regex',
                'confidence': 0.0,
                'warnings': ['Both LLM and regex extraction failed']
            }

    def _validate_rules(self, result: Dict[str, Any]) -> bool:
        """
        Validate that the Claude response has valid rule structure.

        Args:
            result: Parsed JSON response from Claude

        Returns:
            True if valid, False otherwise
        """
        if 'rules' not in result or not isinstance(result['rules'], list):
            return False

        # Check that each rule has required fields
        required_fields = ['rule_type', 'rule_description', 'severity']
        for rule in result['rules']:
            if not all(field in rule for field in required_fields):
                return False

            # Validate rule_type
            valid_types = ['sequence', 'approval', 'timing', 'validation']
            if rule['rule_type'] not in valid_types:
                return False

            # Validate severity
            valid_severities = ['low', 'medium', 'high', 'critical']
            if rule['severity'] not in valid_severities:
                return False

        return True

    def _calculate_confidence(self, rules: List[Dict[str, Any]]) -> float:
        """
        Calculate confidence score based on rule completeness.

        Args:
            rules: List of extracted rules

        Returns:
            Confidence score between 0 and 1
        """
        if not rules:
            return 0.0

        # Factors that increase confidence:
        # - Rules have step numbers
        # - Rules have required fields specified
        # - Rules have timing constraints (for timing rules)
        # - Rules have conditional logic

        total_score = 0.0
        for rule in rules:
            rule_score = 0.5  # Base score for having the rule

            if rule.get('step_number'):
                rule_score += 0.15

            if rule.get('required_fields') and len(rule['required_fields']) > 0:
                rule_score += 0.15

            if rule['rule_type'] == 'timing' and rule.get('timing_constraint'):
                rule_score += 0.10

            if rule.get('conditional_logic'):
                rule_score += 0.10

            total_score += min(rule_score, 1.0)

        average_confidence = total_score / len(rules)
        return round(average_confidence, 2)

    def compare_with_fallback(self, sop_text: str) -> Dict[str, Any]:
        """
        Compare LLM and regex extraction side-by-side (useful for testing).

        Args:
            sop_text: The full text of the SOP document

        Returns:
            Dict containing both extractions and comparison
        """
        llm_result = self.extract_rules(sop_text, use_llm=True, fallback_on_error=False)
        regex_result = self._extract_with_fallback(sop_text)

        return {
            'llm': llm_result,
            'regex': regex_result,
            'comparison': {
                'llm_rule_count': len(llm_result['rules']),
                'regex_rule_count': len(regex_result['rules']),
                'llm_confidence': llm_result['confidence'],
                'regex_confidence': regex_result['confidence']
            }
        }
