from typing import List, Dict, Any
from collections import defaultdict
import re
from .rule_parser import RuleParser

class EligibilityChecker:
    """
    Checks eligibility deviations (age, tenor, EMI-to-income).

    DEVIATION TYPES DETECTED:
    - ineligible_age: Customer age outside policy limits
    - ineligible_tenor: Loan tenor exceeds maximum allowed
    - emi_to_income_breach: EMI-to-Income ratio exceeds policy limit
    - low_score_approved_without_exception: Low credit score approved without documented exception

    STRICT MODE: Only validates if SOP explicitly defines eligibility requirements.
    If no eligibility rules exist, returns empty list (no validation, no false positives).
    """

    @staticmethod
    def check_eligibility(logs: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check eligibility deviations across workflow logs.

        STRICT MODE: Only validates based on explicit SOP requirements.
        If no eligibility thresholds defined, skips validation entirely.

        Args:
            logs: Workflow logs with optional fields (customer_age, tenor_months, emi_to_income_ratio, credit_score)
            rules: SOP rules (may contain eligibility thresholds)

        Returns:
            List of eligibility deviations detected
        """
        deviations = []

        # Extract eligibility thresholds from SOP
        thresholds = RuleParser.extract_eligibility_thresholds(rules)

        # STRICT MODE: If no eligibility thresholds defined in SOP, skip validation
        if not thresholds:
            return deviations

        # Extract thresholds (None if not defined)
        min_age = thresholds.get('min_age')
        max_age = thresholds.get('max_age')
        max_tenor = thresholds.get('max_tenor')
        max_emi_to_income = thresholds.get('max_emi_to_income')
        min_credit_score = thresholds.get('min_credit_score')
        max_ltv = thresholds.get('max_ltv')

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

            # Check 1: Age eligibility (only if field present AND SOP defines age limits)
            if 'customer_age' in case_data and (min_age is not None or max_age is not None):
                try:
                    age = int(case_data['customer_age'])
                    age_violated = False
                    if min_age is not None and age < min_age:
                        age_violated = True
                    if max_age is not None and age > max_age:
                        age_violated = True

                    if age_violated:
                        age_range = f'{min_age or "any"}-{max_age or "any"}'
                        deviations.append({
                            'case_id': case_id,
                            'officer_id': officer_id,
                            'timestamp': timestamp,
                            'deviation_type': 'ineligible_age',
                            'severity': 'critical',
                            'description': f'Customer age {age} outside eligible range {age_range} (per SOP)',
                            'expected_behavior': f'Customer age must be {age_range} years (per SOP)',
                            'actual_behavior': f'Customer age is {age}',
                            'context': {'age': age, 'min_age': min_age, 'max_age': max_age}
                        })
                except (ValueError, TypeError):
                    # Invalid age format - skip this check
                    pass

            # Check 2: Tenor eligibility (only if field present AND SOP defines max tenor)
            if 'tenor_months' in case_data and max_tenor is not None:
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

            # Check 3: EMI-to-Income ratio (only if field present AND SOP defines limit)
            if 'emi_to_income_ratio' in case_data and max_emi_to_income is not None:
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

            # Check 4: Low credit score approved without exception (only if SOP defines min score)
            if 'credit_score' in case_data and case_data.get('approved', False) and min_credit_score is not None:
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
