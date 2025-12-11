from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict

class RuleValidator:
    """Validates logs against all SOP rules"""

    @staticmethod
    def validate_all(logs: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate all rules"""
        deviations = []

        # Group logs by case
        cases = defaultdict(list)
        for log in logs:
            cases[log['case_id']].append(log)

        for case_id, case_logs in cases.items():
            case_logs.sort(key=lambda x: datetime.fromisoformat(x['timestamp']))

            # Check approval rules
            approval_deviations = RuleValidator._check_approval_rules(case_id, case_logs, rules)
            deviations.extend(approval_deviations)

            # Check timing rules
            timing_deviations = RuleValidator._check_timing_rules(case_id, case_logs, rules)
            deviations.extend(timing_deviations)

        return deviations

    @staticmethod
    def _check_approval_rules(case_id: str, logs: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check if approval rules are followed"""
        deviations = []
        approval_rules = [r for r in rules if r.get('type') == 'approval']

        if not approval_rules:
            return deviations

        # Check if approval steps exist
        step_names = [log['step_name'].lower() for log in logs]
        has_manager_approval = any('manager' in step and 'approval' in step for step in step_names)
        has_final_approval = any('final' in step and 'approval' in step for step in step_names)

        officer_id = logs[0]['officer_id'] if logs else 'unknown'

        if not has_manager_approval:
            deviations.append({
                'case_id': case_id,
                'officer_id': officer_id,
                'deviation_type': 'missing_approval',
                'severity': 'critical',
                'description': 'Missing manager approval',
                'expected_behavior': 'Manager approval required before final approval',
                'actual_behavior': 'Manager approval step not found',
                'context': {
                    'approval_type': 'manager',
                    'steps_performed': step_names
                }
            })

        if not has_final_approval:
            deviations.append({
                'case_id': case_id,
                'officer_id': officer_id,
                'deviation_type': 'missing_approval',
                'severity': 'critical',
                'description': 'Missing final approval',
                'expected_behavior': 'Final approval required to complete case',
                'actual_behavior': 'Final approval step not found',
                'context': {
                    'approval_type': 'final',
                    'steps_performed': step_names
                }
            })

        return deviations

    @staticmethod
    def _check_timing_rules(case_id: str, logs: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check if timing constraints are met"""
        deviations = []
        timing_rules = [r for r in rules if r.get('type') == 'timing']

        if not timing_rules or len(logs) < 2:
            return deviations

        officer_id = logs[0]['officer_id']

        # Calculate time between first and last step
        first_timestamp = datetime.fromisoformat(logs[0]['timestamp'])
        last_timestamp = datetime.fromisoformat(logs[-1]['timestamp'])
        duration_hours = (last_timestamp - first_timestamp).total_seconds() / 3600

        # Check if process is too rushed (completed in less than 1 hour)
        if duration_hours < 1:
            deviations.append({
                'case_id': case_id,
                'officer_id': officer_id,
                'deviation_type': 'timing_violation',
                'severity': 'medium',
                'description': 'Process completed too quickly',
                'expected_behavior': 'Proper review time required for each step',
                'actual_behavior': f'Process completed in {duration_hours:.1f} hours',
                'context': {
                    'duration_hours': duration_hours,
                    'issue': 'rushed_process'
                }
            })

        # Check for unusually long gaps between steps
        for i in range(len(logs) - 1):
            current_time = datetime.fromisoformat(logs[i]['timestamp'])
            next_time = datetime.fromisoformat(logs[i + 1]['timestamp'])
            gap_days = (next_time - current_time).total_seconds() / 86400

            if gap_days > 7:  # More than 7 days
                deviations.append({
                    'case_id': case_id,
                    'officer_id': officer_id,
                    'deviation_type': 'timing_violation',
                    'severity': 'low',
                    'description': f'Long delay between {logs[i]["step_name"]} and {logs[i+1]["step_name"]}',
                    'expected_behavior': 'Steps should be completed in timely manner',
                    'actual_behavior': f'Gap of {gap_days:.1f} days between steps',
                    'context': {
                        'gap_days': gap_days,
                        'step_1': logs[i]['step_name'],
                        'step_2': logs[i + 1]['step_name']
                    }
                })

        return deviations
