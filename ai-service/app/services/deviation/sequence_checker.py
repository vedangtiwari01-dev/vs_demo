from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict
from .rule_parser import RuleParser

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
    def _compare_sequences(
        case_id: str,
        officer_id: str,
        expected: List[str],
        actual: List[str],
        logs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Compare expected and actual sequences"""
        deviations = []

        # Extract case start time (timestamp of first log entry)
        case_start_time = logs[0]['timestamp'] if logs else None

        # Check if case has reached disbursement (completion marker)
        # Only check for missing steps if case is complete (has disbursement)
        has_disbursement = any('disbursement' in log['step_name'].lower() for log in logs)

        # Check for missing steps (only for completed cases)
        missing_steps = set(expected) - set(actual)
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
        expected_idx = {step: idx for idx, step in enumerate(expected)}
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
