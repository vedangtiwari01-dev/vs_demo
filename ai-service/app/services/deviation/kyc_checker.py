from typing import List, Dict, Any
from collections import defaultdict

class KYCChecker:
    """
    Checks KYC/AML/sanctions compliance deviations.

    DEVIATION TYPES DETECTED:
    - kyc_incomplete_progression: Case progressed without complete KYC
    - sanctions_hit_not_rejected: Sanctions match found but case not rejected
    - pep_no_edd_or_extra_approval: PEP (Politically Exposed Person) case without Enhanced Due Diligence

    DEFENSIVE: Gracefully handles missing fields/rules.
    Only validates when KYC/AML fields are present in workflow logs.
    """

    @staticmethod
    def check_kyc(logs: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check KYC/AML/sanctions compliance deviations.

        Args:
            logs: Workflow logs with optional fields (kyc_status, kyc_completed_flag, sanctions_hit_flag, pep_flag)
            rules: SOP rules (kyc, aml types)

        Returns:
            List of KYC/AML deviations detected
        """
        deviations = []

        # Extract KYC/AML rules
        kyc_rules = [r for r in rules if r.get('rule_type') in ['kyc', 'aml']]

        # Group logs by case_id
        cases = defaultdict(list)
        for log in logs:
            if 'case_id' in log:  # DEFENSIVE: Skip logs without case_id
                cases[log['case_id']].append(log)

        # Check each case
        for case_id, case_logs in cases.items():
            officer_id = case_logs[0].get('officer_id', 'unknown')
            timestamp = case_logs[0].get('timestamp')

            # Collect KYC/AML data from logs
            case_data = {}
            step_names = []

            for log in case_logs:
                step_names.append(log.get('step_name', ''))

                # Aggregate KYC/AML data
                if 'kyc_status' in log and log['kyc_status'] is not None:
                    case_data['kyc_status'] = log['kyc_status']
                if 'kyc_completed_flag' in log and log['kyc_completed_flag'] is not None:
                    case_data['kyc_completed'] = str(log['kyc_completed_flag']).lower() in ['yes', 'true', '1', 'completed']
                if 'sanctions_hit_flag' in log and log['sanctions_hit_flag'] is not None:
                    case_data['sanctions_hit'] = str(log['sanctions_hit_flag']).lower() in ['yes', 'true', '1', 'hit']
                if 'pep_flag' in log and log['pep_flag'] is not None:
                    case_data['pep_flag'] = str(log['pep_flag']).lower() in ['yes', 'true', '1']
                if 'edd_completed' in log and log['edd_completed'] is not None:
                    case_data['edd_completed'] = str(log['edd_completed']).lower() in ['yes', 'true', '1', 'completed']
                if 'approval_decision' in log and log['approval_decision']:
                    case_data['decision'] = log['approval_decision']

            # Determine if case progressed to approvals
            has_approval_step = any('approval' in step.lower() for step in step_names)
            has_disbursement_step = any('disbursement' in step.lower() or 'disburse' in step.lower() for step in step_names)

            # Check 1: KYC incomplete progression (only if kyc fields present)
            if 'kyc_status' in case_data or 'kyc_completed' in case_data:
                kyc_complete = case_data.get('kyc_completed', False)
                kyc_status = case_data.get('kyc_status', '').lower()

                # If KYC not completed but case progressed to approval/disbursement
                if not kyc_complete and kyc_status not in ['completed', 'verified', 'approved']:
                    if has_approval_step or has_disbursement_step:
                        deviations.append({
                            'case_id': case_id,
                            'officer_id': officer_id,
                            'timestamp': timestamp,
                            'deviation_type': 'kyc_incomplete_progression',
                            'severity': 'critical',
                            'description': f'Case progressed to approval/disbursement with incomplete KYC (status: {kyc_status or "unknown"})',
                            'expected_behavior': 'KYC must be completed before approval/disbursement',
                            'actual_behavior': f'Case progressed with KYC status: {kyc_status or "incomplete"}',
                            'context': {
                                'kyc_status': kyc_status,
                                'kyc_completed': kyc_complete,
                                'has_approval': has_approval_step,
                                'has_disbursement': has_disbursement_step
                            }
                        })

            # Check 2: Sanctions hit not rejected (only if sanctions field present)
            if 'sanctions_hit' in case_data and case_data['sanctions_hit']:
                decision = case_data.get('decision', '').lower()

                # Sanctions hit found but case not rejected
                if decision not in ['rejected', 'declined', 'reject']:
                    deviations.append({
                        'case_id': case_id,
                        'officer_id': officer_id,
                        'timestamp': timestamp,
                        'deviation_type': 'sanctions_hit_not_rejected',
                        'severity': 'critical',
                        'description': f'Sanctions screening match found but case not rejected (decision: {decision or "pending"})',
                        'expected_behavior': 'Cases with sanctions hits must be rejected immediately',
                        'actual_behavior': f'Sanctions hit detected but decision: {decision or "not rejected"}',
                        'context': {
                            'sanctions_hit': True,
                            'decision': decision,
                            'has_approval': has_approval_step
                        }
                    })

            # Check 3: PEP without Enhanced Due Diligence (only if pep field present)
            if 'pep_flag' in case_data and case_data['pep_flag']:
                edd_completed = case_data.get('edd_completed', False)

                # Check for extra approval steps for PEP cases
                has_extra_approval = any('senior' in step.lower() or 'compliance' in step.lower() or 'enhanced' in step.lower()
                                        for step in step_names)

                # PEP case without EDD or extra approvals
                if not edd_completed and not has_extra_approval:
                    if has_approval_step or has_disbursement_step:
                        deviations.append({
                            'case_id': case_id,
                            'officer_id': officer_id,
                            'timestamp': timestamp,
                            'deviation_type': 'pep_no_edd_or_extra_approval',
                            'severity': 'critical',
                            'description': 'PEP (Politically Exposed Person) case progressed without Enhanced Due Diligence or extra approval',
                            'expected_behavior': 'PEP cases require Enhanced Due Diligence and senior/compliance approval',
                            'actual_behavior': 'PEP case progressed without EDD or enhanced approval steps',
                            'context': {
                                'pep_flag': True,
                                'edd_completed': edd_completed,
                                'has_extra_approval': has_extra_approval,
                                'steps_performed': step_names
                            }
                        })

        return deviations
