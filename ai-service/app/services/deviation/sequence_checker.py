from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict
from .rule_parser import RuleParser
import re
from difflib import SequenceMatcher

class SequenceChecker:
    """
    Checks workflow sequences against expected order and detects process deviations.

    SEQUENCE DEVIATION TYPES DETECTED:
    - missing_step: Required step was skipped
    - wrong_sequence: Steps done in wrong order
    - unexpected_step: Step not allowed for product/segment
    - duplicate_step: Repeated steps where only one allowed (detected by AI)
    - skipped_mandatory_subprocess: No pre-sanction visit/legal opinion (detected by AI)

    This class performs rule-based sequence validation. Additional process-related
    deviations are detected by Claude AI through comprehensive prompt analysis.

    EXTENDED WORKFLOW FIELDS SUPPORTED (80+ fields):
    Core: case_id, officer_id, step_name, action, timestamp, duration_seconds, status, notes
    Entity IDs: application_id, loan_id, customer_id, customer_name, customer_segment, portfolio_id
    Product & Channel: product_type, branch_code, channel
    Amounts & Terms: loan_amount_requested, loan_amount_sanctioned, emi_amount, ltv_ratio
    Risk & Credit: credit_score_bureau, emi_to_income_ratio, risk_grade
    Collateral: collateral_type, collateral_value, security_created_flag
    KYC/AML: kyc_status, sanctions_hit_flag, pep_flag
    Approvals: approver_id, approval_decision, exception_flag
    Disbursement: disbursement_date, disbursement_amount, post_disbursement_qc_flag
    Collections: overdue_days, bucket, restructure_flag
    Audit: created_by, source_system, audit_trail_id
    """

    @staticmethod
    def check_sequence(logs: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check if logs follow expected sequence.

        STRICT MODE: Only validates if SOP explicitly defines sequence rules.
        If no sequence rules exist, returns empty list (no validation, no false positives).
        """
        deviations = []

        # Extract expected sequence from SOP rules
        expected_sequence = RuleParser.extract_sequence_steps(rules)

        # STRICT MODE: If no explicit sequence defined in SOP, skip validation
        if expected_sequence is None or len(expected_sequence) == 0:
            return deviations

        # Group logs by case_id
        cases = defaultdict(list)
        for log in logs:
            cases[log['case_id']].append(log)

        # Check each case
        for case_id, case_logs in cases.items():
            # Sort by timestamp
            case_logs.sort(key=lambda x: datetime.fromisoformat(x['timestamp']))

            # Extract actual sequence
            actual_sequence = [log['step_name'] for log in case_logs]
            officer_id = case_logs[0]['officer_id'] if case_logs else 'unknown'

            # Compare sequences
            case_deviations = SequenceChecker._compare_sequences(
                case_id,
                officer_id,
                expected_sequence,
                actual_sequence,
                case_logs
            )
            deviations.extend(case_deviations)

        return deviations


    @staticmethod
    def _is_valid_step_name(step_name: str) -> bool:
        """
        Validate if step name is reasonable (not a compound rule description).

        Phase 1 Defensive Check: Skip malformed rules to prevent false positives.

        Returns False if:
        - Step name is too long (> 80 chars, likely a rule description)
        - Contains multiple step numbers (compound rule like "Step 13 and 14")
        - Contains conjunction patterns suggesting compound rule
        """
        if not step_name or len(step_name) > 80:
            return False

        # Count step number references (e.g., "Step 13", "Step 14")
        step_numbers = re.findall(r'Step\s+\d+', step_name, re.IGNORECASE)
        if len(step_numbers) > 1:
            return False  # Compound rule like "Step 13 and Step 14"

        # Check for conjunctions suggesting compound rules
        # Pattern: "X and Y shall be" or "X and Y before Z"
        if re.search(r'\b(and|or)\b.*\b(shall|before|after|within)\b', step_name, re.IGNORECASE):
            return False

        return True

    @staticmethod
    def _normalize_step_name(step_name: str) -> str:
        """
        Normalize step name for fuzzy matching.

        Phase 3 Enhancement: Remove common variations to enable better matching.

        Normalization:
        - Remove step number prefixes: "Step 13: X" → "X"
        - Remove parenthetical info: "X (NACH/SI)" → "X"
        - Lowercase and trim whitespace
        - Remove punctuation

        Args:
            step_name: Original step name

        Returns:
            Normalized step name for comparison
        """
        if not step_name:
            return ""

        # Remove step number prefix: "Step 13: " or "13. " or "Step 13 - "
        normalized = re.sub(r'^(?:Step\s+)?\d+[\.\:\-\)]\s*', '', step_name, flags=re.IGNORECASE)

        # Remove parenthetical info: "X (NACH/SI)" → "X"
        normalized = re.sub(r'\([^)]*\)', '', normalized)

        # Remove common suffixes like "(Step N)"
        normalized = re.sub(r'\s*\(Step\s+\d+\)\s*', '', normalized, flags=re.IGNORECASE)

        # Remove conditional phrases that describe relationships between steps
        # These phrases don't help with matching actual step names
        conditional_patterns = [
            r'\s+shall\s+be\s+\w+\s+before\s+.*$',  # "shall be completed before X"
            r'\s+shall\s+be\s+\w+\s+after\s+.*$',   # "shall be completed after X"
            r'\s+must\s+be\s+\w+\s+before\s+.*$',   # "must be completed before X"
            r'\s+must\s+be\s+\w+\s+after\s+.*$',    # "must be completed after X"
            r'\s+should\s+be\s+\w+\s+before\s+.*$', # "should be completed before X"
            r'\s+before\s+proceeding\s+to\s+.*$',   # "before proceeding to X"
        ]
        for pattern in conditional_patterns:
            normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)

        # Lowercase
        normalized = normalized.lower()

        # Remove punctuation and extra whitespace
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)

        return normalized.strip()

    @staticmethod
    def _steps_match(expected_step: str, actual_step: str, threshold: float = 0.60) -> bool:
        """
        Check if two step names match using fuzzy string comparison.

        Phase 3 Enhancement: Use SequenceMatcher for similarity scoring.

        Args:
            expected_step: Expected step name from SOP
            actual_step: Actual step name from workflow logs
            threshold: Similarity threshold (0-1), default 0.60 (lowered from 0.75 to reduce false positives)

        Returns:
            True if steps match (similarity >= threshold)
        """
        # Normalize both step names
        norm_expected = SequenceChecker._normalize_step_name(expected_step)
        norm_actual = SequenceChecker._normalize_step_name(actual_step)

        # Exact match after normalization
        if norm_expected == norm_actual:
            return True

        # Subset match: if one is contained in the other, consider it a match
        # e.g., "document verification" matches "document collection and verification"
        if norm_expected in norm_actual or norm_actual in norm_expected:
            return True

        # Fuzzy match using SequenceMatcher
        similarity = SequenceMatcher(None, norm_expected, norm_actual).ratio()

        return similarity >= threshold

    @staticmethod
    def _find_matching_step(expected_step: str, actual_steps: List[str]) -> bool:
        """
        Check if expected step exists in actual steps using fuzzy matching.

        Args:
            expected_step: Expected step name
            actual_steps: List of actual step names

        Returns:
            True if a match is found
        """
        return any(SequenceChecker._steps_match(expected_step, actual) for actual in actual_steps)

    @staticmethod
    def _compare_sequences(
        case_id: str,
        officer_id: str,
        expected: List[str],
        actual: List[str],
        logs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Compare expected and actual sequences"""
        deviations = []

        # Phase 1 Fix: Filter out invalid step names to prevent false positives
        valid_expected = [step for step in expected if SequenceChecker._is_valid_step_name(step)]

        # DEBUG: Log filtering results for first 3 cases
        if case_id in ['SPL-001', 'SPL-002', 'SPL-003']:
            print(f"\n[DEBUG {case_id}] Sequence Validation:")
            print(f"  Expected rules (raw): {len(expected)}")
            for i, step in enumerate(expected[:5]):  # Show first 5
                is_valid = SequenceChecker._is_valid_step_name(step)
                print(f"    {i+1}. [{len(step)} chars] {'✓' if is_valid else '✗'} {step[:80]}...")
            print(f"  Valid rules after filtering: {len(valid_expected)}")

        if len(valid_expected) == 0:
            # No valid sequence rules, skip validation
            return deviations

        # Extract case start time (timestamp of first log entry)
        case_start_time = logs[0]['timestamp'] if logs else None

        # Check if case has reached disbursement (completion marker)
        # Only check for missing steps if case is complete (has disbursement)
        has_disbursement = any('disbursement' in log['step_name'].lower() for log in logs)

        # Check for missing steps (only for completed cases)
        # Phase 1 Fix: Use valid_expected instead of expected to avoid false positives
        # Phase 3 Fix: Use fuzzy matching instead of exact set comparison
        missing_steps = []
        for expected_step in valid_expected:
            found = SequenceChecker._find_matching_step(expected_step, actual)

            # DEBUG: Log fuzzy matching details for first 3 cases
            if case_id in ['SPL-001', 'SPL-002', 'SPL-003']:
                norm_expected = SequenceChecker._normalize_step_name(expected_step)
                print(f"\n  Checking: '{expected_step[:60]}...'")
                print(f"    Normalized: '{norm_expected}'")
                print(f"    Found match: {found}")
                if not found and len(actual) > 0:
                    # Show best match attempt
                    from difflib import SequenceMatcher
                    best_score = 0
                    best_match = None
                    for actual_step in actual[:10]:  # Check first 10 actual steps
                        norm_actual = SequenceChecker._normalize_step_name(actual_step)
                        score = SequenceMatcher(None, norm_expected, norm_actual).ratio()
                        if score > best_score:
                            best_score = score
                            best_match = actual_step
                    print(f"    Best match: '{best_match[:60]}...' (score: {best_score:.2f}, threshold: 0.60)")

            if not found:
                missing_steps.append(expected_step)

        for step in missing_steps:
            # Skip missing-step detection if case hasn't reached disbursement yet
            if not has_disbursement:
                continue
            deviations.append({
                'case_id': case_id,
                'officer_id': officer_id,
                'timestamp': case_start_time,
                'deviation_type': 'missing_step',
                'severity': 'high',
                'description': f'Missing required step: {step}',
                'expected_behavior': f'Step "{step}" should be completed',
                'actual_behavior': f'Step "{step}" was skipped',
                'context': {
                    'missing_step': step,
                    'actual_sequence': actual
                }
            })

        # Check for wrong order
        # Phase 1 Fix: Use valid_expected instead of expected
        expected_idx = {step: idx for idx, step in enumerate(valid_expected)}
        for i in range(len(actual) - 1):
            current_step = actual[i]
            next_step = actual[i + 1]

            if current_step in expected_idx and next_step in expected_idx:
                if expected_idx[current_step] > expected_idx[next_step]:
                    deviations.append({
                        'case_id': case_id,
                        'officer_id': officer_id,
                        'timestamp': case_start_time,
                        'deviation_type': 'wrong_sequence',
                        'severity': 'high',
                        'description': f'Wrong step order: {next_step} before {current_step}',
                        'expected_behavior': f'{current_step} should come before {next_step}',
                        'actual_behavior': f'{next_step} was performed before {current_step}',
                        'context': {
                            'step_1': current_step,
                            'step_2': next_step,
                            'actual_sequence': actual
                        }
                    })

        # REMOVED: unexpected_step detection (STRICT MODE)
        # In strict mode, we only validate the sequence defined in SOP.
        # We do NOT flag steps that aren't in the sequence as "unexpected"
        # because the sequence might be partial. The SOP might only define
        # critical ordering constraints, not every possible step.

        return deviations
