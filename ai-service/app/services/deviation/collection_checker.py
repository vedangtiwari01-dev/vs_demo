from typing import List, Dict, Any
from collections import defaultdict

class CollectionChecker:
    """
    Checks collection and restructuring compliance deviations.

    DEVIATION TYPES DETECTED:
    - collection_escalation_delay: Overdue account not escalated per policy
    - unauthorized_restructure: Loan restructured without proper approval
    - unauthorized_writeoff: Write-off without required authority approval

    DEFENSIVE: Gracefully handles missing fields/rules.
    Only validates when collection fields are present in workflow logs.
    """

    @staticmethod
    def check_collection(logs: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check collection and restructuring compliance deviations.

        Args:
            logs: Workflow logs with optional fields (overdue_days, bucket, collection_status, restructure_flag)
            rules: SOP rules (collection, restructuring types)

        Returns:
            List of collection deviations detected
        """
        deviations = []

        # Extract collection/restructuring rules
        collection_rules = [r for r in rules if r.get('rule_type') in ['collection', 'restructuring']]

        # Default thresholds (used if not in SOP)
        escalation_thresholds = {
            30: 'first_reminder',
            60: 'legal_notice',
            90: 'legal_action'
        }

        # Override with SOP rules if available
        for rule in collection_rules:
            desc = rule.get('rule_description', '').lower()
            if 'dpd' in desc or 'days past due' in desc or 'overdue' in desc:
                import re
                match = re.search(r'(\d+)\s*day', desc)
                if match:
                    days = int(match.group(1))
                    if 'legal' in desc:
                        escalation_thresholds[days] = 'legal_action'
                    elif 'notice' in desc:
                        escalation_thresholds[days] = 'legal_notice'

        # Group logs by case_id
        cases = defaultdict(list)
        for log in logs:
            if 'case_id' in log:  # DEFENSIVE: Skip logs without case_id
                cases[log['case_id']].append(log)

        # Check each case
        for case_id, case_logs in cases.items():
            officer_id = case_logs[0].get('officer_id', 'unknown')
            timestamp = case_logs[0].get('timestamp')

            # Collect collection data
            case_data = {}
            step_names = []

            for log in case_logs:
                step_names.append(log.get('step_name', ''))

                # Aggregate collection data
                if 'overdue_days' in log and log['overdue_days'] is not None:
                    case_data['overdue_days'] = log['overdue_days']
                if 'bucket' in log and log['bucket']:
                    case_data['bucket'] = log['bucket']
                if 'collection_status' in log:
                    case_data['collection_status'] = log['collection_status']
                if 'restructure_flag' in log:
                    case_data['restructured'] = str(log['restructure_flag']).lower() in ['yes', 'true', '1']
                if 'restructure_approval' in log:
                    case_data['restructure_approval'] = log['restructure_approval']
                if 'writeoff_flag' in log:
                    case_data['writeoff'] = str(log['writeoff_flag']).lower() in ['yes', 'true', '1']
                if 'writeoff_approval' in log:
                    case_data['writeoff_approval'] = log['writeoff_approval']

            # Determine if case is in collections (overdue)
            is_overdue = ('overdue_days' in case_data or
                         'bucket' in case_data or
                         any('collection' in step.lower() or 'overdue' in step.lower() for step in step_names))

            if not is_overdue:
                continue  # Not in collections, skip checks

            # Check 1: Collection escalation delay (if overdue days available)
            if 'overdue_days' in case_data:
                try:
                    overdue = int(case_data['overdue_days'])

                    # Determine required escalation level
                    required_escalation = None
                    for threshold in sorted(escalation_thresholds.keys()):
                        if overdue >= threshold:
                            required_escalation = escalation_thresholds[threshold]

                    if required_escalation:
                        # Check if escalation action was taken
                        collection_status = str(case_data.get('collection_status', '')).lower()

                        # Check step names for escalation actions
                        has_legal_notice = any('legal notice' in step.lower() or 'demand' in step.lower() for step in step_names)
                        has_legal_action = any('legal action' in step.lower() or 'suit filed' in step.lower() for step in step_names)

                        escalated = False
                        if required_escalation == 'legal_action' and has_legal_action:
                            escalated = True
                        elif required_escalation == 'legal_notice' and (has_legal_notice or has_legal_action):
                            escalated = True
                        elif required_escalation == 'first_reminder' and any('reminder' in step.lower() or 'follow' in step.lower() for step in step_names):
                            escalated = True

                        if not escalated:
                            deviations.append({
                                'case_id': case_id,
                                'officer_id': officer_id,
                                'timestamp': timestamp,
                                'deviation_type': 'collection_escalation_delay',
                                'severity': 'high' if overdue >= 90 else 'medium',
                                'description': f'Account {overdue} days overdue without required escalation ({required_escalation})',
                                'expected_behavior': f'At {overdue} DPD, escalation to {required_escalation} required',
                                'actual_behavior': f'No {required_escalation} action found in workflow',
                                'context': {
                                    'overdue_days': overdue,
                                    'required_escalation': required_escalation,
                                    'collection_status': collection_status,
                                    'steps_taken': step_names
                                }
                            })
                except (ValueError, TypeError):
                    pass

            # Check 2: Unauthorized restructure (restructure without proper approval)
            if case_data.get('restructured', False):
                restructure_approval = case_data.get('restructure_approval', '').lower()

                # Check for restructure approval in step names
                has_restructure_approval = any('restructure approval' in step.lower() or
                                              'restructuring approval' in step.lower() or
                                              ('senior' in step.lower() and 'approval' in step.lower())
                                              for step in step_names)

                # Restructure approved by appropriate authority?
                approval_valid = (restructure_approval in ['approved', 'sanctioned'] or
                                has_restructure_approval)

                if not approval_valid:
                    deviations.append({
                        'case_id': case_id,
                        'officer_id': officer_id,
                        'timestamp': timestamp,
                        'deviation_type': 'unauthorized_restructure',
                        'severity': 'critical',
                        'description': 'Loan restructured without proper authority approval',
                        'expected_behavior': 'Restructuring requires senior management/credit committee approval',
                        'actual_behavior': f'Restructure found without approval (status: {restructure_approval or "not found"})',
                        'context': {
                            'restructured': True,
                            'restructure_approval': restructure_approval,
                            'has_approval_step': has_restructure_approval
                        }
                    })

            # Check 3: Unauthorized write-off (write-off without required authority)
            if case_data.get('writeoff', False):
                writeoff_approval = case_data.get('writeoff_approval', '').lower()

                # Check for write-off approval in step names
                has_writeoff_approval = any('writeoff approval' in step.lower() or
                                           'write-off approval' in step.lower() or
                                           ('board' in step.lower() and 'approval' in step.lower())
                                           for step in step_names)

                # Write-off approved by appropriate authority (typically board/senior management)?
                approval_valid = (writeoff_approval in ['approved', 'board approved', 'sanctioned'] or
                                has_writeoff_approval)

                if not approval_valid:
                    deviations.append({
                        'case_id': case_id,
                        'officer_id': officer_id,
                        'timestamp': timestamp,
                        'deviation_type': 'unauthorized_writeoff',
                        'severity': 'critical',
                        'description': 'Loan written off without required authority approval',
                        'expected_behavior': 'Write-offs require board/senior management approval',
                        'actual_behavior': f'Write-off found without approval (status: {writeoff_approval or "not found"})',
                        'context': {
                            'writeoff': True,
                            'writeoff_approval': writeoff_approval,
                            'has_approval_step': has_writeoff_approval,
                            'overdue_days': case_data.get('overdue_days')
                        }
                    })

        return deviations
