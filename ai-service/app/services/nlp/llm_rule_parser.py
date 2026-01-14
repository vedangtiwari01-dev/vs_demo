import json
import logging
import re
from typing import List, Dict, Any
from app.services.claude.client import ClaudeClient
from app.services.claude.prompts import format_sop_extraction_prompt
from app.services.nlp.rule_parser import RuleParser
from json_repair import repair_json

logger = logging.getLogger(__name__)

def extract_json_from_text(text: str) -> str:
    """
    Extract JSON from text that might contain markdown code fences or extra text.
    Also cleans up common JSON formatting issues like trailing commas.
    """
    text = text.strip()

    # Try to extract from markdown code fence
    json_fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_fence_match:
        json_text = json_fence_match.group(1)
    else:
        # Try to extract raw JSON
        json_match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
        if json_match:
            json_text = json_match.group(1)
        else:
            json_text = text

    # Clean up common JSON issues:
    # 1. Remove trailing commas before closing brackets/braces
    json_text = re.sub(r',\s*}', '}', json_text)  # Remove trailing comma before }
    json_text = re.sub(r',\s*]', ']', json_text)  # Remove trailing comma before ]

    # 2. Fix multiple commas
    json_text = re.sub(r',\s*,', ',', json_text)

    # 3. Fix missing commas between closing and opening braces (common Claude error)
    #    Example: }{ should be },{
    json_text = re.sub(r'}\s*{', '},{', json_text)
    json_text = re.sub(r'}\s*\[', '},[', json_text)
    json_text = re.sub(r']\s*{', '],{', json_text)
    json_text = re.sub(r']\s*\[', '],[', json_text)

    # 4. Fix missing commas after closing brace/bracket before opening quote
    #    Example: }" should be },"
    json_text = re.sub(r'}(\s*")', r'},\1', json_text)
    json_text = re.sub(r'](\s*")', r'],\1', json_text)

    # 5. Fix missing commas after string before opening brace/bracket
    #    Example: "text"{ should be "text",{
    json_text = re.sub(r'"(\s*[{\[])', r'",\1', json_text)

    # 6. Fix missing commas after closing quote before another quote (key-value pairs)
    #    Example: "value" "key": should be "value", "key":
    json_text = re.sub(r'"(\s+)"(?=[a-zA-Z_])', r'", "', json_text)

    # 7. Fix missing commas after numbers before quote (next key)
    #    Example: 42 "key": should be 42, "key":
    json_text = re.sub(r'(\d)(\s+)"(?=[a-zA-Z_])', r'\1, "', json_text)

    # 8. Fix missing commas after boolean/null before quote (next key)
    #    Example: true "key": should be true, "key":
    json_text = re.sub(r'(true|false|null)(\s+)"(?=[a-zA-Z_])', r'\1, "', json_text)

    # 9. Remove trailing commas in nested objects/arrays (more aggressive)
    json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)

    # 10. Fix missing comma after closing brace/bracket before another field at same level
    #     Example: {"a":{"nested":1}}{"b":2} → {"a":{"nested":1}},{"b":2}
    json_text = re.sub(r'}(\s*)"([a-zA-Z_])', r'},\1"\2', json_text)
    json_text = re.sub(r'](\s*)"([a-zA-Z_])', r'],\1"\2', json_text)

    # 11. Remove comment-like text (Claude sometimes adds // comments)
    json_text = re.sub(r'//[^\n]*\n', '\n', json_text)
    json_text = re.sub(r'/\*.*?\*/', '', json_text, flags=re.DOTALL)

    # 12. Fix trailing text after closing brace
    #     Sometimes Claude adds text after the final }
    last_brace = json_text.rfind('}')
    if last_brace != -1 and last_brace < len(json_text) - 1:
        trailing = json_text[last_brace + 1:].strip()
        if trailing and not trailing.startswith(','):  # Don't truncate if it's part of larger structure
            json_text = json_text[:last_brace + 1]

    return json_text


def _aggressive_json_cleanup(json_text: str) -> str:
    """Apply more aggressive cleaning for retry attempts."""
    # Remove ALL trailing commas more aggressively
    json_text = re.sub(r',\s*([}\]])', r'\1', json_text)

    # Remove any text between } and ]
    json_text = re.sub(r'}\s+(?=\])', '}', json_text)

    # Remove any text between ] and }
    json_text = re.sub(r']\s+(?=\})', ']', json_text)

    return json_text

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
                system=("You are an expert at analyzing compliance documents and extracting rules. "
                       "IMPORTANT: Respond with ONLY valid JSON. No markdown, no explanations, no text outside the JSON. "
                       "The entire response must be parseable by json.loads()."),
                json_mode=True
            )

            # Save response text for retry attempts
            response_text = response['text']

            # Retry logic with progressive cleaning
            MAX_PARSE_RETRIES = 3
            last_error = None
            result = None

            for retry_attempt in range(MAX_PARSE_RETRIES):
                logger.info(f"Starting parse attempt {retry_attempt + 1}/{MAX_PARSE_RETRIES}")
                try:
                    # Extract and parse JSON response
                    json_text = extract_json_from_text(response_text)

                    if retry_attempt > 0:
                        logger.info(f"JSON parse retry attempt {retry_attempt}/{MAX_PARSE_RETRIES}")

                        # Retry 1: Aggressive manual cleanup
                        if retry_attempt == 1:
                            json_text = _aggressive_json_cleanup(json_text)

                        # Retry 2: Use json-repair library as fallback
                        elif retry_attempt == 2:
                            logger.info("Attempting JSON repair with json-repair library")
                            try:
                                json_text = repair_json(json_text)
                                logger.info("JSON repaired successfully with library")
                            except Exception as repair_error:
                                logger.warning(f"json-repair failed: {str(repair_error)}")
                                # Continue with original text

                    logger.info(f"Extracted JSON length: {len(json_text)} characters")

                    # Attempt to parse
                    result = json.loads(json_text)

                    # Success! Break out of retry loop
                    logger.info(f"JSON parsed successfully on attempt {retry_attempt + 1}")
                    break

                except json.JSONDecodeError as parse_error:
                    last_error = parse_error
                    error_pos = parse_error.pos if hasattr(parse_error, 'pos') else 0
                    start = max(0, error_pos - 200)
                    end = min(len(json_text), error_pos + 200)

                    logger.warning(f"JSON parsing failed on attempt {retry_attempt + 1}/{MAX_PARSE_RETRIES}")
                    logger.warning(f"Error at position {error_pos}: {parse_error.msg}")
                    logger.warning(f"Context: ...{json_text[start:end]}...")

                    # Last retry? Fall back
                    if retry_attempt == MAX_PARSE_RETRIES - 1:
                        logger.error(f"All retries failed for SOP extraction")
                        raise last_error  # Re-raise to trigger fallback

                    # Otherwise, continue to next retry iteration
                    continue

            # Check if parsing succeeded
            if result is None:
                logger.error("SOP extraction result is None after retry loop")
                raise json.JSONDecodeError("Failed to parse after retries", response_text, 0)

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

            # Phase 2 Enhancement: Post-process rules to split compound rules
            result['rules'] = self._post_process_rules(result['rules'])
            logger.info(f"Post-processing complete: {len(result['rules'])} rules after split")

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

            # Validate rule_type (16 types supported)
            valid_types = [
                'sequence', 'approval', 'timing', 'eligibility', 'credit_risk',
                'kyc', 'aml', 'documentation', 'collateral', 'disbursement',
                'post_disbursement_qc', 'collection', 'restructuring',
                'regulatory', 'data_quality', 'operational'
            ]
            if rule['rule_type'] not in valid_types:
                logger.warning(f"Invalid rule_type '{rule['rule_type']}'. Valid types: {valid_types}")
                return False

            # Validate severity
            valid_severities = ['low', 'medium', 'high', 'critical']
            if rule['severity'] not in valid_severities:
                return False

        return True

    def _post_process_rules(self, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Post-process rules to fix common LLM extraction issues.

        Phase 2 Enhancement: Split compound sequence rules and extract step numbers.

        Args:
            rules: Raw rules from LLM

        Returns:
            Processed rules with compound rules split
        """
        processed = []

        for rule in rules:
            # If not a sequence rule, keep as-is
            if rule.get('rule_type') != 'sequence':
                processed.append(rule)
                continue

            # Check if rule description contains compound step references
            desc = rule.get('rule_description', '')

            # Pattern: "Step X and Step Y before Step Z" or "(Step X) and (Step Y)"
            step_numbers = re.findall(r'Step\s+(\d+)', desc, re.IGNORECASE)

            # If rule has step_number field or no compound steps found, keep as-is
            if rule.get('step_number') is not None or len(step_numbers) <= 1:
                processed.append(rule)
                continue

            # Compound rule detected - try to split it
            logger.info(f"Splitting compound sequence rule: {desc[:100]}...")

            # Extract step names (heuristic approach)
            # Look for patterns like "X (Step N) and Y (Step M)"
            # or "X and Y shall be completed before Z"

            # Simple approach: If we found multiple step numbers but no clear step names,
            # just create a rule for each step number with the full description
            # The Phase 1 defensive checks will filter these out if needed

            for step_num in step_numbers:
                split_rule = rule.copy()
                split_rule['step_number'] = int(step_num)

                # Keep the original description but mark it as auto-split
                if 'context' not in split_rule:
                    split_rule['context'] = {}
                split_rule['context']['auto_split_from_compound'] = True
                split_rule['context']['original_description'] = desc

                processed.append(split_rule)

            logger.info(f"Split into {len(step_numbers)} rules with step numbers: {step_numbers}")

        return processed

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
