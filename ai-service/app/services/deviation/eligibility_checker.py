from typing import List, Dict, Any
from collections import defaultdict
import re

class EligibilityChecker:
    """
    Checks eligibility deviations (age, tenor, EMI-to-income).

    DEVIATION TYPES DETECTED:
    - ineligible_age: Customer age outside policy limits
    - ineligible_tenor: Loan tenor exceeds maximum allowed
    - emi_to_income_breach: EMI-to-Income ratio exceeds policy limit
    - low_score_approved_without_exception: Low credit score approved without documented exception

    DEFENSIVE: Gracefully handles missing fields/rules.
    Only validates when required fields are present in workflow logs.
    """

    @staticmethod
    def check_eligibility(logs: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check eligibility deviations across workflow logs.

        Args:
            logs: Workflow logs with optional fields (customer_age, tenor_months, emi_to_income_ratio, credit_score)
            rules: SOP rules (may contain eligibility thresholds)

        Returns:
            List of eligibility deviations detected
        """
        deviations = []

        # Extract eligibility rules (with defaults if not in SOP)
        eligibility_rules = [r for r in rules if r.get('rule_type') == 'eligibility']
        credit_rules = [r for r in rules if r.get('rule_type') == 'credit_risk']

        # Default thresholds (industry standard) - used if not extracted from SOP
        min_age = 18
        max_age = 65
        max_tenor = 360  # 30 years
        max_emi_to_income = 0.5  # 50%
        min_credit_score = 650

        # Override with SOP rules if available
        for rule in eligibility_rules:
            desc = rule.get('rule_description', '').lower()
            if 'age' in desc and 'minimum' in desc:
                # Try to extract min age
                match = re.search(r'(\d+)\s*year', desc)
                if match:
                    min_age = int(match.group(1))
            elif 'age' in desc and 'maximum' in desc:
                match = re.search(r'(\d+)\s*year', desc)
                if match:
                    max_age = int(match.group(1))
            elif 'tenor' in desc or 'loan term' in desc:
                match = re.search(r'(\d+)\s*(month|year)', desc)
                if match:
                    value = int(match.group(1))
                    max_tenor = value if 'month' in desc else value * 12

        for rule in credit_rules:
            desc = rule.get('rule_description', '').lower()
            if 'emi' in desc and 'income' in desc:
                match = re.search(r'(\d+)%', desc)
                if match:
                    max_emi_to_income = int(match.group(1)) / 100.0
            elif 'credit score' in desc:
                match = re.search(r'(\d+)', desc)
                if match:
                    min_credit_score = int(match.group(1))

        # Group logs by case_id
        cases = defaultdict(list)
        for log in logs:
            if 'case_id' in log:  # DEFENSIVE: Skip logs without case_id
                cases[log['case_id']].append(log)

        # Check each case
        for case_id, case_logs in cases.items():
            officer_id = case_logs[0].get('officer_id', 'unknown')
            timestamp = case_logs[0].get('timestamp')

            # Collect eligibility data from logs (may be in any step)
            case_data = {}
            for log in case_logs:
                # Aggregate data across all steps
                if 'customer_age' in log and log['customer_age'] is not None:
                    case_data['customer_age'] = log['customer_age']
                if 'tenor_months' in log and log['tenor_months'] is not None:
                    case_data['tenor_months'] = log['tenor_months']
                if 'emi_to_income_ratio' in log and log['emi_to_income_ratio'] is not None:
                    case_data['emi_to_income_ratio'] = log['emi_to_income_ratio']
                if 'credit_score' in log and log['credit_score'] is not None:
                    case_data['credit_score'] = log['credit_score']
                if 'credit_score_bureau' in log and log['credit_score_bureau'] is not None:
                    case_data['credit_score'] = log['credit_score_bureau']
                if 'exception_flag' in log:
                    case_data['exception_flag'] = log['exception_flag']
                if 'approval_decision' in log and log['approval_decision'] == 'approved':
                    case_data['approved'] = True

            # Check 1: Age eligibility (only if field present)
            if 'customer_age' in case_data:
                try:
                    age = int(case_data['customer_age'])
                    if age < min_age or age > max_age:
                        deviations.append({
                            'case_id': case_id,
                            'officer_id': officer_id,
                            'timestamp': timestamp,
                            'deviation_type': 'ineligible_age',
                            'severity': 'critical',
                            'description': f'Customer age {age} outside eligible range {min_age}-{max_age}',
                            'expected_behavior': f'Customer age must be {min_age}-{max_age} years',
                            'actual_behavior': f'Customer age is {age}',
                            'context': {'age': age, 'min_age': min_age, 'max_age': max_age}
                        })
                except (ValueError, TypeError):
                    # Invalid age format - skip this check
                    pass

            # Check 2: Tenor eligibility (only if field present)
            if 'tenor_months' in case_data:
                try:
                    tenor = int(case_data['tenor_months'])
                    if tenor > max_tenor:
                        deviations.append({
                            'case_id': case_id,
                            'officer_id': officer_id,
                            'timestamp': timestamp,
                            'deviation_type': 'ineligible_tenor',
                            'severity': 'high',
                            'description': f'Loan tenor {tenor} months exceeds maximum {max_tenor} months',
                            'expected_behavior': f'Tenor must be ≤{max_tenor} months',
                            'actual_behavior': f'Tenor is {tenor} months',
                            'context': {'tenor_months': tenor, 'max_tenor': max_tenor}
                        })
                except (ValueError, TypeError):
                    pass

            # Check 3: EMI-to-Income ratio (only if field present)
            if 'emi_to_income_ratio' in case_data:
                try:
                    emi_ratio = float(case_data['emi_to_income_ratio'])
                    if emi_ratio > max_emi_to_income:
                        deviations.append({
                            'case_id': case_id,
                            'officer_id': officer_id,
                            'timestamp': timestamp,
                            'deviation_type': 'emi_to_income_breach',
                            'severity': 'high',
                            'description': f'EMI-to-Income ratio {emi_ratio:.2%} exceeds limit {max_emi_to_income:.2%}',
                            'expected_behavior': f'EMI-to-Income ratio must be ≤{max_emi_to_income:.2%}',
                            'actual_behavior': f'Ratio is {emi_ratio:.2%}',
                            'context': {'emi_to_income_ratio': emi_ratio, 'max_ratio': max_emi_to_income}
                        })
                except (ValueError, TypeError):
                    pass

            # Check 4: Low credit score approved without exception
            if 'credit_score' in case_data and case_data.get('approved', False):
                try:
                    score = int(case_data['credit_score'])
                    has_exception = case_data.get('exception_flag', '').lower() in ['yes', 'true', '1']

                    if score < min_credit_score and not has_exception:
                        deviations.append({
                            'case_id': case_id,
                            'officer_id': officer_id,
                            'timestamp': timestamp,
                            'deviation_type': 'low_score_approved_without_exception',
                            'severity': 'critical',
                            'description': f'Credit score {score} below {min_credit_score} approved without documented exception',
                            'expected_behavior': f'Scores below {min_credit_score} require exception approval',
                            'actual_behavior': f'Score {score} approved without exception flag',
                            'context': {'credit_score': score, 'min_score': min_credit_score, 'exception_flag': has_exception}
                        })
                except (ValueError, TypeError):
                    pass

        return deviations
