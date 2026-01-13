from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime, timedelta
from .rule_parser import RuleParser

class CollateralChecker:
    """
    Checks collateral and security deviations.

    DEVIATION TYPES DETECTED:
    - ltv_breach: Loan-to-Value ratio exceeds policy limit
    - valuation_missing_or_stale: Collateral valuation missing or outdated
    - security_not_created: Legal security not created before disbursement

    STRICT MODE: Only validates if SOP explicitly defines collateral requirements.
    If no collateral rules exist, returns empty list (no validation, no false positives).
    """

    @staticmethod
    def check_collateral(logs: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check collateral and security compliance deviations.

        STRICT MODE: Only validates based on explicit SOP requirements.
        If no collateral thresholds defined, skips validation entirely.

        Args:
            logs: Workflow logs with optional fields (ltv_ratio, collateral_value, collateral_value_date, security_created_flag)
            rules: SOP rules (collateral type)

        Returns:
            List of collateral deviations detected
        """
        deviations = []

        # Extract collateral requirements from SOP
        collateral_reqs = RuleParser.extract_collateral_requirements(rules)

        # STRICT MODE: If no collateral requirements defined in SOP, skip validation
        if not collateral_reqs['ltv_limits'] and collateral_reqs['valuation_age_days'] is None and not collateral_reqs['security_required']:
            return deviations

        # Extract requirements (None if not defined)
        ltv_limits = collateral_reqs['ltv_limits']
        max_valuation_age_days = collateral_reqs['valuation_age_days']
        security_required = collateral_reqs['security_required']

        # Group logs by case_id
        cases = defaultdict(list)
        for log in logs:
            if 'case_id' in log:  # DEFENSIVE: Skip logs without case_id
                cases[log['case_id']].append(log)

        # Check each case
        for case_id, case_logs in cases.items():
            officer_id = case_logs[0].get('officer_id', 'unknown')
            timestamp = case_logs[0].get('timestamp')

            # Collect collateral data
            case_data = {}
            step_names = []

            for log in case_logs:
                step_names.append(log.get('step_name', ''))

                # Aggregate collateral data
                if 'ltv_ratio' in log and log['ltv_ratio'] is not None:
                    case_data['ltv_ratio'] = log['ltv_ratio']
                if 'collateral_value' in log and log['collateral_value'] is not None:
                    case_data['collateral_value'] = log['collateral_value']
                if 'collateral_value_date' in log and log['collateral_value_date']:
                    case_data['collateral_value_date'] = log['collateral_value_date']
                if 'collateral_type' in log and log['collateral_type']:
                    case_data['collateral_type'] = log['collateral_type']
                if 'valuation_status' in log:
                    case_data['valuation_status'] = log['valuation_status']
                if 'security_created_flag' in log:
                    case_data['security_created'] = str(log['security_created_flag']).lower() in ['yes', 'true', '1', 'created']
                if 'loan_amount_sanctioned' in log and log['loan_amount_sanctioned']:
                    case_data['loan_amount'] = log['loan_amount_sanctioned']
                elif 'loan_amount_requested' in log and log['loan_amount_requested']:
                    case_data['loan_amount'] = log['loan_amount_requested']

            # Determine if case has collateral (is secured loan)
            has_collateral = ('collateral_type' in case_data or
                            'collateral_value' in case_data or
                            any('collateral' in step.lower() for step in step_names))

            if not has_collateral:
                continue  # Skip unsecured loans

            # Determine if case progressed to disbursement
            has_disbursement_step = any('disbursement' in step.lower() or 'disburse' in step.lower() for step in step_names)

            # Check 1: LTV breach (only if ltv_ratio present)
            if 'ltv_ratio' in case_data:
                try:
                    ltv = float(case_data['ltv_ratio'])
                    if ltv > max_ltv:
                        deviations.append({
                            'case_id': case_id,
                            'officer_id': officer_id,
                            'timestamp': timestamp,
                            'deviation_type': 'ltv_breach',
                            'severity': 'high',
                            'description': f'Loan-to-Value ratio {ltv:.2%} exceeds policy limit {max_ltv:.2%}',
                            'expected_behavior': f'LTV must be ≤{max_ltv:.2%} for secured loans',
                            'actual_behavior': f'LTV is {ltv:.2%}',
                            'context': {
                                'ltv_ratio': ltv,
                                'max_ltv': max_ltv,
                                'collateral_type': case_data.get('collateral_type', 'unknown')
                            }
                        })
                except (ValueError, TypeError):
                    pass

            # Check 2: Valuation missing or stale (for secured loans)
            if has_disbursement_step:
                valuation_status = str(case_data.get('valuation_status', '')).lower()
                has_valid_valuation = valuation_status in ['completed', 'verified', 'approved']

                # Check valuation date if available
                if 'collateral_value_date' in case_data:
                    try:
                        valuation_date_str = case_data['collateral_value_date']
                        valuation_date = None

                        # Try multiple date formats
                        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%dT%H:%M:%S']:
                            try:
                                valuation_date = datetime.strptime(valuation_date_str.split()[0], fmt)
                                break
                            except (ValueError, AttributeError):
                                continue

                        if valuation_date:
                            # Get disbursement date (approximate as last log timestamp)
                            disbursement_date = datetime.fromisoformat(case_logs[-1].get('timestamp', '').split('.')[0].replace('Z', ''))
                            age_days = (disbursement_date - valuation_date).days

                            if age_days > max_valuation_age_days:
                                has_valid_valuation = False
                                deviations.append({
                                    'case_id': case_id,
                                    'officer_id': officer_id,
                                    'timestamp': timestamp,
                                    'deviation_type': 'valuation_missing_or_stale',
                                    'severity': 'high',
                                    'description': f'Collateral valuation is {age_days} days old (limit: {max_valuation_age_days} days)',
                                    'expected_behavior': f'Valuation must be <{max_valuation_age_days} days old',
                                    'actual_behavior': f'Valuation is {age_days} days old',
                                    'context': {
                                        'valuation_date': valuation_date.strftime('%Y-%m-%d'),
                                        'disbursement_date': disbursement_date.strftime('%Y-%m-%d'),
                                        'age_days': age_days
                                    }
                                })
                    except Exception:
                        # Date parsing failed
                        pass

                # If no valuation status or date
                if not has_valid_valuation and 'collateral_value_date' not in case_data:
                    deviations.append({
                        'case_id': case_id,
                        'officer_id': officer_id,
                        'timestamp': timestamp,
                        'deviation_type': 'valuation_missing_or_stale',
                        'severity': 'critical',
                        'description': 'Secured loan disbursed without collateral valuation',
                        'expected_behavior': 'Valid collateral valuation required before disbursement',
                        'actual_behavior': 'No valuation date or status found',
                        'context': {
                            'has_collateral': has_collateral,
                            'valuation_status': valuation_status
                        }
                    })

            # Check 3: Security not created (for secured loans before disbursement)
            if has_disbursement_step:
                security_created = case_data.get('security_created', False)

                if not security_created:
                    # Also check step names for security creation
                    has_security_step = any('security' in step.lower() and ('creat' in step.lower() or 'register' in step.lower())
                                          for step in step_names)

                    if not has_security_step:
                        deviations.append({
                            'case_id': case_id,
                            'officer_id': officer_id,
                            'timestamp': timestamp,
                            'deviation_type': 'security_not_created',
                            'severity': 'critical',
                            'description': 'Secured loan disbursed without creating legal security',
                            'expected_behavior': 'Legal security must be created/registered before disbursement',
                            'actual_behavior': 'Disbursement completed without security creation',
                            'context': {
                                'security_created': security_created,
                                'has_security_step': has_security_step,
                                'collateral_type': case_data.get('collateral_type', 'unknown')
                            }
                        })

        return deviations
