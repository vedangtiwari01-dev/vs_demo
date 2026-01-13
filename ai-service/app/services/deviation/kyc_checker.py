from typing import List, Dict, Any
from collections import defaultdict
from .rule_parser import RuleParser

class KYCChecker:
    """
    Checks KYC/AML/sanctions compliance deviations.

    DEVIATION TYPES DETECTED:
    - kyc_incomplete_progression: Case progressed without complete KYC
    - sanctions_hit_not_rejected: Sanctions match found but case not rejected
    - pep_no_edd_or_extra_approval: PEP (Politically Exposed Person) case without Enhanced Due Diligence

    STRICT MODE: Only validates if SOP explicitly defines KYC/AML requirements.
    If no KYC rules exist, returns empty list (no validation, no false positives).
    """

    @staticmethod
    def check_kyc(logs: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check KYC/AML/sanctions compliance deviations.

        STRICT MODE: Only validates based on explicit SOP requirements.
        If no KYC rules defined, skips validation entirely.

        Args:
            logs: Workflow logs with optional fields (kyc_status, kyc_completed_flag, sanctions_hit_flag, pep_flag)
            rules: SOP rules (kyc, aml types)

        Returns:
            List of KYC/AML deviations detected
        """
        deviations = []

        # Extract KYC requirements from SOP
        kyc_requirements = RuleParser.extract_kyc_requirements(rules)

        # STRICT MODE: If no KYC rules defined in SOP, skip validation
        if not kyc_requirements['kyc_required_before'] and kyc_requirements['sanctions_action'] is None and not kyc_requirements['pep_requirements']:
            return deviations

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

            # Check 1: KYC incomplete progression (only if SOP requires it)
            if kyc_requirements['kyc_required_before'] and ('kyc_status' in case_data or 'kyc_completed' in case_data):
                kyc_complete = case_data.get('kyc_completed', False)
                kyc_status = case_data.get('kyc_status', '').lower()

                # Check if KYC is incomplete
                if not kyc_complete and kyc_status not in ['completed', 'verified', 'approved']:
                    # Check if case progressed to a step that requires KYC completion
                    required_before = kyc_requirements['kyc_required_before']
                    progression_detected = False
                    progressed_to = None

                    if 'approval' in required_before and has_approval_step:
                        progression_detected = True
                        progressed_to = 'approval'
                    elif 'disbursement' in required_before and has_disbursement_step:
                        progression_detected = True
                        progressed_to = 'disbursement'
                    elif 'sanction' in required_before and (has_approval_step or has_disbursement_step):
                        progression_detected = True
                        progressed_to = 'sanction'

                    if progression_detected:
                        deviations.append({
                            'case_id': case_id,
                            'officer_id': officer_id,
                            'timestamp': timestamp,
                            'deviation_type': 'kyc_incomplete_progression',
                            'severity': 'critical',
                            'description': f'Case progressed to {progressed_to} with incomplete KYC (status: {kyc_status or "unknown"})',
                            'expected_behavior': f'KYC must be completed before {", ".join(required_before)}',
                            'actual_behavior': f'Case progressed to {progressed_to} with KYC status: {kyc_status or "incomplete"}',
                            'context': {
                                'kyc_status': kyc_status,
                                'kyc_completed': kyc_complete,
                                'required_before': required_before,
                                'progressed_to': progressed_to
                            }
                        })

            # Check 2: Sanctions hit handling (only if SOP defines required action)
            if kyc_requirements['sanctions_action'] and 'sanctions_hit' in case_data and case_data['sanctions_hit']:
                decision = case_data.get('decision', '').lower()
                required_action = kyc_requirements['sanctions_action']

                # Check if required action was taken
                action_taken = False

                if required_action == 'reject':
                    # Check if case was rejected
                    if decision in ['rejected', 'declined', 'reject']:
                        action_taken = True
                elif required_action == 'edd':
                    # Check if EDD was completed
                    if case_data.get('edd_completed', False):
                        action_taken = True
                elif required_action == 'escalate':
                    # Check for escalation step
                    has_escalation = any('escalat' in step.lower() or 'senior' in step.lower() or 'compliance' in step.lower()
                                       for step in step_names)
                    if has_escalation:
                        action_taken = True

                if not action_taken:
                    deviations.append({
                        'case_id': case_id,
                        'officer_id': officer_id,
                        'timestamp': timestamp,
                        'deviation_type': 'sanctions_hit_not_handled',
                        'severity': 'critical',
                        'description': f'Sanctions screening match found but required action not taken (expected: {required_action}, decision: {decision or "pending"})',
                        'expected_behavior': f'Cases with sanctions hits must be handled: {required_action}',
                        'actual_behavior': f'Sanctions hit detected but decision: {decision or "no action taken"}',
                        'context': {
                            'sanctions_hit': True,
                            'decision': decision,
                            'required_action': required_action,
                            'has_approval': has_approval_step
                        }
                    })

            # Check 3: PEP handling (only if SOP defines PEP requirements)
            if kyc_requirements['pep_requirements'] and 'pep_flag' in case_data and case_data['pep_flag']:
                edd_completed = case_data.get('edd_completed', False)
                pep_reqs = kyc_requirements['pep_requirements']

                # Check if SOP requires EDD for PEP
                edd_required = pep_reqs.get('edd_required', False)
                extra_approval_required = pep_reqs.get('extra_approval_required', False)

                # Check for extra approval steps
                has_extra_approval = False
                approval_level = pep_reqs.get('approval_level')
                if approval_level:
                    if approval_level == 'senior':
                        has_extra_approval = any('senior' in step.lower() or 'compliance' in step.lower()
                                                for step in step_names)
                    else:
                        has_extra_approval = any(approval_level in step.lower() for step in step_names)
                else:
                    # Generic check for enhanced approval
                    has_extra_approval = any('senior' in step.lower() or 'compliance' in step.lower() or 'enhanced' in step.lower()
                                            for step in step_names)

                # Determine if deviation exists
                missing_requirements = []
                if edd_required and not edd_completed:
                    missing_requirements.append('EDD')
                if extra_approval_required and not has_extra_approval:
                    missing_requirements.append(f'{approval_level or "extra"} approval')

                if missing_requirements and (has_approval_step or has_disbursement_step):
                    deviations.append({
                        'case_id': case_id,
                        'officer_id': officer_id,
                        'timestamp': timestamp,
                        'deviation_type': 'pep_requirements_not_met',
                        'severity': 'critical',
                        'description': f'PEP (Politically Exposed Person) case progressed without required: {", ".join(missing_requirements)}',
                        'expected_behavior': f'PEP cases require: {", ".join([k for k, v in pep_reqs.items() if v])}',
                        'actual_behavior': f'PEP case progressed without: {", ".join(missing_requirements)}',
                        'context': {
                            'pep_flag': True,
                            'edd_completed': edd_completed,
                            'has_extra_approval': has_extra_approval,
                            'missing_requirements': missing_requirements,
                            'steps_performed': step_names
                        }
                    })

        return deviations
