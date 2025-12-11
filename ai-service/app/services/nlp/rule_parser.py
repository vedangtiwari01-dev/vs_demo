import re
from typing import List, Dict, Any

class RuleParser:
    """Extracts rules from SOP text using pattern matching"""

    def __init__(self):
        # Define patterns for different rule types
        self.sequence_patterns = [
            r'(first|then|next|after|before|finally)',
            r'step\s+\d+',
            r'must\s+be\s+completed\s+before',
            r'proceed\s+to',
            r'following\s+sequence',
        ]

        self.approval_patterns = [
            r'(must|shall|should)\s+be\s+approved\s+by',
            r'requires?\s+approval\s+(from|of)',
            r'authorized\s+by',
            r'manager\s+approval',
            r'senior\s+(officer|analyst|manager)',
        ]

        self.timing_patterns = [
            r'within\s+\d+\s+(days?|hours?|weeks?|months?)',
            r'before\s+\d+\s+(days?|hours?)',
            r'not\s+later\s+than',
            r'immediately',
            r'no\s+more\s+than',
        ]

        self.validation_patterns = [
            r'must\s+verify',
            r'check\s+(for|that)',
            r'validate',
            r'ensure\s+that',
            r'confirm',
            r'review',
        ]

    def extract_rules(self, text: str) -> List[Dict[str, Any]]:
        """Extract rules from SOP text"""
        rules = []
        sentences = self._split_into_sentences(text)

        for idx, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()

            # Check for sequence rules
            if self._matches_patterns(sentence_lower, self.sequence_patterns):
                rules.append({
                    'type': 'sequence',
                    'description': sentence.strip(),
                    'step_number': self._extract_step_number(sentence),
                    'severity': 'high',
                    'condition_logic': None
                })

            # Check for approval rules
            elif self._matches_patterns(sentence_lower, self.approval_patterns):
                rules.append({
                    'type': 'approval',
                    'description': sentence.strip(),
                    'step_number': self._extract_step_number(sentence),
                    'severity': 'critical',
                    'condition_logic': None
                })

            # Check for timing rules
            elif self._matches_patterns(sentence_lower, self.timing_patterns):
                rules.append({
                    'type': 'timing',
                    'description': sentence.strip(),
                    'step_number': self._extract_step_number(sentence),
                    'severity': 'medium',
                    'condition_logic': self._extract_timing_constraint(sentence)
                })

            # Check for validation rules
            elif self._matches_patterns(sentence_lower, self.validation_patterns):
                rules.append({
                    'type': 'validation',
                    'description': sentence.strip(),
                    'step_number': self._extract_step_number(sentence),
                    'severity': 'high',
                    'condition_logic': None
                })

        return rules

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any of the patterns"""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _extract_step_number(self, text: str) -> int:
        """Extract step number if present"""
        match = re.search(r'step\s+(\d+)', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def _extract_timing_constraint(self, text: str) -> Dict[str, Any]:
        """Extract timing constraint details"""
        match = re.search(r'(\d+)\s+(days?|hours?|weeks?|months?)', text, re.IGNORECASE)
        if match:
            return {
                'duration': int(match.group(1)),
                'unit': match.group(2).lower()
            }
        return None
