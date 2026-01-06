from typing import List, Dict, Any
from collections import defaultdict

class DisbursementChecker:
    """
    Checks disbursement compliance deviations.

    DEVIATION TYPES DETECTED:
    - pre_disbursement_condition_unmet: Disbursement without meeting pre-conditions
    - mandate_not_set_before_disbursement: EMI mandate not set before disbursement
    - incorrect_disbursement_amount: Disbursed amount differs from sanctioned amount
    - post_disbursement_qc_missing: Post-disbursement quality check not performed

    DEFENSIVE: Gracefully handles missing fields/rules.
    Only validates when disbursement fields are present in workflow logs.
    """

    @staticmethod
    def check_disbursement(logs: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check disbursement compliance deviations.

        Args:
            logs: Workflow logs with optional fields (disbursement_date, disbursement_amount, mandate_status, post_disbursement_qc_flag)
            rules: SOP rules (disbursement, post_disbursement_qc types)

        Returns:
            List of disbursement deviations detected
        """
        deviations = []

        # Extract disbursement rules
        disbursement_rules = [r for r in rules if r.get('rule_type') in ['disbursement', 'post_disbursement_qc']]

        # Group logs by case_id
        cases = defaultdict(list)
        for log in logs:
            if 'case_id' in log:  # DEFENSIVE: Skip logs without case_id
                cases[log['case_id']].append(log)

        # Check each case
        for case_id, case_logs in cases.items():
            officer_id = case_logs[0].get('officer_id', 'unknown')
            timestamp = case_logs[0].get('timestamp')

            # Collect disbursement data
            case_data = {}
            step_names = []

            for log in case_logs:
                step_names.append(log.get('step_name', ''))

                # Aggregate disbursement data
                if 'disbursement_date' in log and log['disbursement_date']:
                    case_data['disbursement_date'] = log['disbursement_date']
                if 'disbursement_amount' in log and log['disbursement_amount'] is not None:
                    case_data['disbursement_amount'] = log['disbursement_amount']
                if 'loan_amount_sanctioned' in log and log['loan_amount_sanctioned'] is not None:
                    case_data['sanctioned_amount'] = log['loan_amount_sanctioned']
                if 'mandate_status' in log:
                    case_data['mandate_status'] = log['mandate_status']
                if 'mandate_set_flag' in log:
                    case_data['mandate_set'] = str(log['mandate_set_flag']).lower() in ['yes', 'true', '1', 'set']
                if 'post_disbursement_qc_flag' in log:
                    case_data['qc_completed'] = str(log['post_disbursement_qc_flag']).lower() in ['yes', 'true', '1', 'completed']
                if 'approval_decision' in log and log['approval_decision'] == 'approved':
                    case_data['approved'] = True

            # Determine if disbursement happened
            has_disbursement = 'disbursement_date' in case_data or 'disbursement_amount' in case_data
            has_disbursement_step = any('disbursement' in step.lower() or 'disburse' in step.lower() for step in step_names)

            if not has_disbursement and not has_disbursement_step:
                continue  # No disbursement, skip checks

            # Check 1: Pre-disbursement conditions (approval must exist before disbursement)
            if has_disbursement or has_disbursement_step:
                has_approval = case_data.get('approved', False)
                has_approval_step = any('approval' in step.lower() for step in step_names)

                if not has_approval and not has_approval_step:
                    deviations.append({
                        'case_id': case_id,
                        'officer_id': officer_id,
                        'timestamp': timestamp,
                        'deviation_type': 'pre_disbursement_condition_unmet',
                        'severity': 'critical',
                        'description': 'Disbursement completed without approval step/decision',
                        'expected_behavior': 'Loan must be approved before disbursement',
                        'actual_behavior': 'Disbursement found without approval',
                        'context': {
                            'has_approval': has_approval,
                            'has_approval_step': has_approval_step,
                            'has_disbursement': has_disbursement
                        }
                    })

            # Check 2: Mandate not set before disbursement (EMI collection setup)
            if has_disbursement or has_disbursement_step:
                mandate_set = case_data.get('mandate_set', False)
                mandate_status = str(case_data.get('mandate_status', '')).lower()

                # Mandate is set if flag=true or status indicates completion
                mandate_complete = mandate_set or mandate_status in ['set', 'active', 'registered', 'completed']

                if not mandate_complete:
                    # Also check step names
                    has_mandate_step = any('mandate' in step.lower() or 'nach' in step.lower() or 'emi' in step.lower()
                                         for step in step_names)

                    if not has_mandate_step:
                        deviations.append({
                            'case_id': case_id,
                            'officer_id': officer_id,
                            'timestamp': timestamp,
                            'deviation_type': 'mandate_not_set_before_disbursement',
                            'severity': 'critical',
                            'description': 'Loan disbursed without setting up EMI mandate/NACH',
                            'expected_behavior': 'EMI mandate must be set before disbursement',
                            'actual_behavior': f'Disbursement completed with mandate status: {mandate_status or "not set"}',
                            'context': {
                                'mandate_set': mandate_set,
                                'mandate_status': mandate_status,
                                'has_mandate_step': has_mandate_step
                            }
                        })

            # Check 3: Incorrect disbursement amount (if both amounts present)
            if 'disbursement_amount' in case_data and 'sanctioned_amount' in case_data:
                try:
                    disbursed = float(case_data['disbursement_amount'])
                    sanctioned = float(case_data['sanctioned_amount'])

                    # Allow 1% tolerance for rounding
                    tolerance = sanctioned * 0.01
                    difference = abs(disbursed - sanctioned)

                    if difference > tolerance:
                        severity = 'critical' if difference > sanctioned * 0.05 else 'high'
                        deviations.append({
                            'case_id': case_id,
                            'officer_id': officer_id,
                            'timestamp': timestamp,
                            'deviation_type': 'incorrect_disbursement_amount',
                            'severity': severity,
                            'description': f'Disbursed amount {disbursed} differs from sanctioned amount {sanctioned} (difference: {difference})',
                            'expected_behavior': f'Disbursed amount should match sanctioned amount: {sanctioned}',
                            'actual_behavior': f'Disbursed: {disbursed}',
                            'context': {
                                'sanctioned_amount': sanctioned,
                                'disbursed_amount': disbursed,
                                'difference': difference,
                                'difference_percentage': (difference / sanctioned) * 100
                            }
                        })
                except (ValueError, TypeError):
                    pass

            # Check 4: Post-disbursement QC missing (if disbursement occurred)
            if has_disbursement or has_disbursement_step:
                qc_completed = case_data.get('qc_completed', False)

                # Also check step names
                has_qc_step = any('qc' in step.lower() or 'quality check' in step.lower() or 'post disbursement' in step.lower()
                                for step in step_names)

                if not qc_completed and not has_qc_step:
                    # Look for rule requiring post-disbursement QC
                    qc_required = any('post' in r.get('rule_description', '').lower() and
                                     'disbursement' in r.get('rule_description', '').lower()
                                     for r in disbursement_rules)

                    if qc_required or disbursement_rules:  # If rules exist, assume QC required
                        deviations.append({
                            'case_id': case_id,
                            'officer_id': officer_id,
                            'timestamp': timestamp,
                            'deviation_type': 'post_disbursement_qc_missing',
                            'severity': 'medium',
                            'description': 'Post-disbursement quality check not performed',
                            'expected_behavior': 'Post-disbursement QC required within specified timeframe',
                            'actual_behavior': 'No QC step or flag found after disbursement',
                            'context': {
                                'qc_completed': qc_completed,
                                'has_qc_step': has_qc_step,
                                'has_disbursement': has_disbursement
                            }
                        })

        return deviations
