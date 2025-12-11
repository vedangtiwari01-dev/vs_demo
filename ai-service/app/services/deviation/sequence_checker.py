from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict

class SequenceChecker:
    """Checks workflow sequences against expected order"""

    @staticmethod
    def check_sequence(logs: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check if logs follow expected sequence"""
        deviations = []

        # Extract sequence rules
        sequence_rules = [r for r in rules if r.get('type') == 'sequence']
        if not sequence_rules:
            return deviations

        # Build expected sequence from rules
        expected_sequence = SequenceChecker._build_expected_sequence(sequence_rules)

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
    def _build_expected_sequence(sequence_rules: List[Dict[str, Any]]) -> List[str]:
        """Build expected sequence from rules"""
        # Extract step names from rule descriptions
        expected_steps = []

        for rule in sorted(sequence_rules, key=lambda x: x.get('step_number', 999)):
            desc = rule['description']
            # Extract step name (simple heuristic)
            if 'income verification' in desc.lower():
                expected_steps.append('Income Verification')
            elif 'document verification' in desc.lower() or 'verify documents' in desc.lower():
                expected_steps.append('Document Verification')
            elif 'credit check' in desc.lower():
                expected_steps.append('Credit Check')
            elif 'risk assessment' in desc.lower():
                expected_steps.append('Risk Assessment')
            elif 'manager approval' in desc.lower():
                expected_steps.append('Manager Approval')
            elif 'final approval' in desc.lower():
                expected_steps.append('Final Approval')
            elif 'application received' in desc.lower():
                expected_steps.append('Application Received')

        # Default sequence if no specific steps extracted
        if not expected_steps:
            expected_steps = [
                'Application Received',
                'Document Verification',
                'Income Verification',
                'Credit Check',
                'Risk Assessment',
                'Manager Approval',
                'Final Approval'
            ]

        return expected_steps

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

        # Check for missing steps
        missing_steps = set(expected) - set(actual)
        for step in missing_steps:
            deviations.append({
                'case_id': case_id,
                'officer_id': officer_id,
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

        # Check for unexpected steps
        unexpected_steps = set(actual) - set(expected)
        for step in unexpected_steps:
            deviations.append({
                'case_id': case_id,
                'officer_id': officer_id,
                'deviation_type': 'unexpected_step',
                'severity': 'medium',
                'description': f'Unexpected step performed: {step}',
                'expected_behavior': 'Only standard SOP steps should be performed',
                'actual_behavior': f'Unexpected step "{step}" was performed',
                'context': {
                    'unexpected_step': step
                }
            })

        return deviations
