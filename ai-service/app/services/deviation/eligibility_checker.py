from typing import List, Dict, Any
from collections import defaultdict
import re
import logging
from .rule_parser import RuleParser

logger = logging.getLogger(__name__)

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

        logger.info(f"EligibilityChecker base thresholds: age={min_age}-{max_age}, emi={max_emi_to_income}, score={min_credit_score}")
        logger.info(f"EligibilityChecker will apply CONDITIONAL EMI thresholds: Salaried=55%, Self-Employed=50%, High-Income=60%")

        # DEFENSIVE VALIDATION: Use SOP defaults if extracted values are garbage
        # Age must be reasonable (18-100 range), not loan amounts (40000) or other values
        if min_age is not None and (min_age < 18 or min_age > 100):
            logger.warning(f"Invalid min_age {min_age} detected (outside 18-100 range), using SOP default 21")
            min_age = 21  # SOP Section 3.1 default
        if max_age is not None and (max_age < 18 or max_age > 100 or max_age < (min_age or 18)):
            logger.warning(f"Invalid max_age {max_age} detected, using SOP default 65")
            max_age = 65  # SOP Section 3.1 default

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
                if 'employment_type' in log and log['employment_type'] is not None:
                    case_data['employment_type'] = log['employment_type']
                if 'monthly_income' in log and log['monthly_income'] is not None:
                    case_data['monthly_income'] = log['monthly_income']
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

            # Check 3: EMI-to-Income ratio with CONDITIONAL thresholds (SOP Section 2.4)
            if 'emi_to_income_ratio' in case_data and max_emi_to_income is not None:
                try:
                    emi_ratio = float(case_data['emi_to_income_ratio'])
                    employment_type = case_data.get('employment_type', '').lower()
                    monthly_income = case_data.get('monthly_income')

                    # CONDITIONAL THRESHOLD: Apply different limits based on employment type
                    # Per SOP Section 2.4:
                    # - Salaried: 55% (0.55)
                    # - Self-Employed: 50% (0.50)
                    # - High Income (>100k/month): 60% (0.60)
                    conditional_threshold = max_emi_to_income  # Default from SOP

                    if 'salaried' in employment_type or 'employed' in employment_type:
                        # Check if high income exception applies
                        if monthly_income and float(monthly_income) > 100000:
                            conditional_threshold = 0.60  # High income: 60%
                        else:
                            conditional_threshold = 0.55  # Standard salaried: 55%
                    elif 'self' in employment_type or 'business' in employment_type:
                        # Check if high income exception applies
                        if monthly_income and float(monthly_income) > 100000:
                            conditional_threshold = 0.60  # High income: 60%
                        else:
                            conditional_threshold = 0.50  # Self-employed: 50%

                    # NORMALIZE THRESHOLD TO MATCH INPUT FORMAT
                    # Input data uses decimals (0.42 = 42%), threshold uses decimals (0.55 = 55%)
                    # Already normalized by workflow_log_cleaner.py
                    threshold_normalized = conditional_threshold
                    if emi_ratio > 1 and conditional_threshold <= 1:
                        # Input is raw percentage (42), threshold is decimal (0.55) → convert threshold to raw (55)
                        threshold_normalized = conditional_threshold * 100
                    elif emi_ratio <= 1 and conditional_threshold > 1:
                        # Input is decimal (0.42), threshold is raw (55) → convert threshold to decimal (0.55)
                        threshold_normalized = conditional_threshold / 100

                    if emi_ratio > threshold_normalized:
                        # Format for display: if value > 1, it's already a percentage, use {:.2f}%
                        # If value <= 1, it's a decimal, use {:.2%} to convert to percentage
                        if emi_ratio > 1:
                            display_ratio = f'{emi_ratio:.2f}%'
                            display_max = f'{threshold_normalized:.2f}%'
                        else:
                            display_ratio = f'{emi_ratio:.2%}'
                            display_max = f'{threshold_normalized:.2%}'

                        # Determine employment category for context
                        employment_category = 'Unknown'
                        if 'salaried' in employment_type or 'employed' in employment_type:
                            employment_category = 'Salaried'
                        elif 'self' in employment_type or 'business' in employment_type:
                            employment_category = 'Self-Employed'

                        deviations.append({
                            'case_id': case_id,
                            'officer_id': officer_id,
                            'timestamp': timestamp,
                            'deviation_type': 'emi_to_income_breach',
                            'severity': 'high',
                            'description': f'EMI-to-Income ratio {display_ratio} exceeds limit {display_max} for {employment_category} customers',
                            'expected_behavior': f'EMI-to-Income ratio must be ≤{display_max} for {employment_category} customers (per SOP Section 2.4)',
                            'actual_behavior': f'Ratio is {display_ratio}',
                            'context': {
                                'emi_to_income_ratio': emi_ratio,
                                'max_ratio': conditional_threshold,
                                'employment_type': employment_category,
                                'threshold_applied': f'{conditional_threshold:.0%}'
                            }
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

        logger.info(f"EligibilityChecker found {len(deviations)} deviations from {len(cases)} cases")
        return deviations
