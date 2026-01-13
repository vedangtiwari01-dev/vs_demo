"""
Temporal Rule Evaluator for Step-to-Step Timing Constraints

Checks timing relationships between specific workflow steps.
Example: "Manager Approval must happen within 48 hours of Risk Assessment"

Author: Claude Code
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime, timedelta


class TemporalRuleEvaluator:
    """
    Evaluates temporal constraints between workflow steps.

    Handles rules like:
    - "Step B must complete within X hours of Step A"
    - Business days vs calendar days
    - Validity period checks
    - Refresh cycle requirements
    """

    @staticmethod
    def evaluate(logs: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Main entry point for temporal rule evaluation.

        Args:
            logs: Workflow logs with timestamps
            rules: SOP rules with temporal_constraint field

        Returns:
            List of temporal deviations
        """
        deviations = []

        # Group logs by case
        cases = defaultdict(list)
        for log in logs:
            cases[log['case_id']].append(log)

        # Get temporal rules (rules with temporal_constraint field)
        temporal_rules = [r for r in rules if r.get('temporal_constraint')]

        for case_id, case_logs in cases.items():
            # Sort by timestamp for sequential analysis
            try:
                def parse_timestamp(log):
                    ts = log['timestamp']
                    # Clean up timestamp format
                    if isinstance(ts, str):
                        ts = ts.replace('.000', '').replace(' +00:00', '+00:00').replace('Z', '+00:00')
                        if '+' not in ts and 'Z' not in ts:
                            ts += '+00:00'
                    return datetime.fromisoformat(ts)

                case_logs.sort(key=parse_timestamp)
            except (ValueError, KeyError) as e:
                continue  # Skip if timestamps are invalid

            for rule in temporal_rules:
                deviation = TemporalRuleEvaluator._check_temporal_rule(
                    case_id, case_logs, rule
                )
                if deviation:
                    deviations.append(deviation)

        return deviations

    @staticmethod
    def _check_temporal_rule(
        case_id: str,
        logs: List[Dict[str, Any]],
        rule: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Check if temporal constraint is violated.

        Rule format:
        {
            "temporal_constraint": {
                "step_a": "Risk Assessment",
                "step_b": "Manager Approval",
                "max_hours": 48,
                "business_days_only": false,
                "exclude_weekends": false
            }
        }

        Args:
            case_id: Case ID
            logs: All logs for the case (already sorted by timestamp)
            rule: The temporal rule

        Returns:
            Deviation dict if violated, None otherwise
        """
        constraint = rule.get('temporal_constraint')

        if not constraint or not isinstance(constraint, dict):
            return None

        step_a_name = constraint.get('step_a')
        step_b_name = constraint.get('step_b')
        max_hours = constraint.get('max_hours')
        business_days_only = constraint.get('business_days_only', False)

        if not step_a_name or not step_b_name or max_hours is None:
            return None

        debug_case = case_id == "CASE-003"

        if debug_case:
            print(f"[TemporalRuleEvaluator] *** CASE-003 DETAILED CHECK ***")
            print(f"[TemporalRuleEvaluator] Checking {case_id} for rule: {step_a_name} -> {step_b_name} within {max_hours}h")
            print(f"[TemporalRuleEvaluator] Available steps: {[log['step_name'] for log in logs]}")

        # Find timestamps for both steps
        step_a_time = None
        step_b_time = None

        for log in logs:
            step_name_lower = log['step_name'].lower()
            if step_a_name.lower() in step_name_lower:
                try:
                    # Handle various timestamp formats
                    ts = log['timestamp']
                    if isinstance(ts, str):
                        # Clean up timestamp format
                        ts = ts.replace('.000', '').replace(' +00:00', '+00:00').replace('Z', '+00:00')
                        if '+' not in ts and 'Z' not in ts:
                            ts += '+00:00'
                    step_a_time = datetime.fromisoformat(ts)
                    if debug_case:
                        print(f"[TemporalRuleEvaluator] Found {step_a_name}: {step_a_time}")
                except (ValueError, TypeError) as e:
                    if debug_case:
                        print(f"[TemporalRuleEvaluator] Failed to parse {step_a_name} timestamp: {e}")
                    continue
            if step_b_name.lower() in step_name_lower:
                try:
                    # Handle various timestamp formats
                    ts = log['timestamp']
                    if isinstance(ts, str):
                        # Clean up timestamp format
                        ts = ts.replace('.000', '').replace(' +00:00', '+00:00').replace('Z', '+00:00')
                        if '+' not in ts and 'Z' not in ts:
                            ts += '+00:00'
                    step_b_time = datetime.fromisoformat(ts)
                    if debug_case:
                        print(f"[TemporalRuleEvaluator] Found {step_b_name}: {step_b_time}")
                except (ValueError, TypeError) as e:
                    if debug_case:
                        print(f"[TemporalRuleEvaluator] Failed to parse {step_b_name} timestamp: {e}")
                    continue

        # Both steps must exist to check timing
        if not step_a_time or not step_b_time:
            if debug_case:
                print(f"[TemporalRuleEvaluator] Missing timestamps: step_a={step_a_time}, step_b={step_b_time}")
            return None

        # Calculate actual time difference
        time_delta = step_b_time - step_a_time
        actual_hours = time_delta.total_seconds() / 3600

        # Adjust for business days if needed
        if business_days_only:
            actual_hours = TemporalRuleEvaluator._calculate_business_hours(
                step_a_time, step_b_time
            )

        if debug_case:
            print(f"[TemporalRuleEvaluator] Time difference: {actual_hours:.1f}h (limit: {max_hours}h)")
            print(f"[TemporalRuleEvaluator] Violation? {actual_hours > max_hours}")

        # Check if violated
        if actual_hours > max_hours:
            # Extract case context from logs (if available)
            first_log = logs[0] if logs else {}
            loan_amount = first_log.get('loan_amount') or first_log.get('loan_amount_sanctioned')
            customer_segment = first_log.get('customer_segment')
            product_type = first_log.get('product_type')

            return {
                'case_id': case_id,
                'officer_id': logs[0].get('officer_id', 'unknown'),
                'timestamp': logs[0].get('timestamp'),
                'deviation_type': 'temporal_sla_breach',
                'severity': rule.get('severity', 'medium'),
                'description': f'{step_b_name} completed {actual_hours:.1f} hours after {step_a_name} (limit: {max_hours} hours)',
                'expected_behavior': f'{step_b_name} must complete within {max_hours} hours of {step_a_name}',
                'actual_behavior': f'Actual time gap: {actual_hours:.1f} hours (breach: {actual_hours - max_hours:.1f} hours)',

                # Rule Context (NEW)
                'rule_id': rule.get('id'),
                'rule_description': rule.get('rule_description'),
                'rule_type': rule.get('rule_type'),
                'rule_severity': rule.get('severity'),

                # Case Context (NEW)
                'loan_amount': loan_amount,
                'customer_segment': customer_segment,
                'product_type': product_type,

                'context': {
                    'rule_id': rule.get('id'),
                    'rule_description': rule.get('rule_description'),
                    'step_a': step_a_name,
                    'step_b': step_b_name,
                    'step_a_time': str(step_a_time),
                    'step_b_time': str(step_b_time),
                    'actual_hours': round(actual_hours, 2),
                    'max_hours': max_hours,
                    'breach_hours': round(actual_hours - max_hours, 2),
                    'business_days_only': business_days_only
                }
            }

        return None

    @staticmethod
    def _calculate_business_hours(start_time: datetime, end_time: datetime) -> float:
        """
        Calculate hours between two timestamps, excluding weekends and non-business hours.
        Business hours: 9 AM to 6 PM, Monday to Friday

        Args:
            start_time: Start timestamp
            end_time: End timestamp

        Returns:
            Number of business hours between timestamps
        """
        BUSINESS_START = 9  # 9 AM
        BUSINESS_END = 18   # 6 PM
        BUSINESS_HOURS_PER_DAY = BUSINESS_END - BUSINESS_START  # 9 hours

        if end_time <= start_time:
            return 0

        business_hours = 0
        current = start_time

        while current < end_time:
            # Skip weekends (Saturday=5, Sunday=6)
            if current.weekday() < 5:  # Monday=0, Friday=4
                # Adjust to business hours for current day
                day_start = current.replace(hour=BUSINESS_START, minute=0, second=0, microsecond=0)
                day_end = current.replace(hour=BUSINESS_END, minute=0, second=0, microsecond=0)

                # If current time is before business hours, move to start of business day
                if current < day_start:
                    current = day_start

                # If current time is during business hours
                if current < day_end:
                    # Calculate end point for this day
                    day_end_point = min(end_time, day_end)
                    if day_end_point > current:
                        hours_today = (day_end_point - current).total_seconds() / 3600
                        business_hours += hours_today
                        current = day_end_point

                # Move to next day
                if current < end_time and current >= day_end:
                    current = current + timedelta(days=1)
                    current = current.replace(hour=BUSINESS_START, minute=0, second=0, microsecond=0)
            else:
                # Skip to next Monday
                days_until_monday = (7 - current.weekday()) % 7
                if days_until_monday == 0:
                    days_until_monday = 1  # If it's Sunday, move to Monday
                current = current + timedelta(days=days_until_monday)
                current = current.replace(hour=BUSINESS_START, minute=0, second=0, microsecond=0)

        return business_hours
