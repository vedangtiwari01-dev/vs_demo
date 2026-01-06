from typing import List, Dict, Any
from collections import defaultdict

class RegulatoryChecker:
    """
    Checks regulatory compliance deviations.

    DEVIATION TYPES DETECTED:
    - classification_mismatch: Loan classification doesn't match asset quality
    - provisioning_shortfall: Provisioning amount below regulatory requirement
    - regulatory_report_missing_or_late: Required regulatory report not submitted on time

    DEFENSIVE: Gracefully handles missing fields/rules.
    Only validates when regulatory fields are present in workflow logs.
    """

    @staticmethod
    def check_regulatory(logs: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check regulatory compliance deviations.

        Args:
            logs: Workflow logs with optional fields (risk_grade, npa_classification, provisioning_amount, overdue_days)
            rules: SOP rules (regulatory type)

        Returns:
            List of regulatory deviations detected
        """
        deviations = []

        # Extract regulatory rules
        regulatory_rules = [r for r in rules if r.get('rule_type') == 'regulatory']

        # Default classification thresholds (RBI norms)
        classification_thresholds = {
            'standard': {'min_dpd': 0, 'max_dpd': 29, 'provisioning': 0.0025},  # 0.25%
            'sub_standard': {'min_dpd': 30, 'max_dpd': 89, 'provisioning': 0.15},  # 15%
            'doubtful': {'min_dpd': 90, 'max_dpd': 365, 'provisioning': 0.25},  # 25%
            'loss': {'min_dpd': 366, 'max_dpd': 999999, 'provisioning': 1.0}  # 100%
        }

        # Group logs by case_id
        cases = defaultdict(list)
        for log in logs:
            if 'case_id' in log:  # DEFENSIVE: Skip logs without case_id
                cases[log['case_id']].append(log)

        # Check each case
        for case_id, case_logs in cases.items():
            officer_id = case_logs[0].get('officer_id', 'unknown')
            timestamp = case_logs[0].get('timestamp')

            # Collect regulatory data
            case_data = {}
            step_names = []

            for log in case_logs:
                step_names.append(log.get('step_name', ''))

                # Aggregate regulatory data
                if 'risk_grade' in log and log['risk_grade']:
                    case_data['risk_grade'] = log['risk_grade']
                if 'npa_classification' in log and log['npa_classification']:
                    case_data['npa_classification'] = log['npa_classification']
                if 'provisioning_amount' in log and log['provisioning_amount'] is not None:
                    case_data['provisioning_amount'] = log['provisioning_amount']
                if 'overdue_days' in log and log['overdue_days'] is not None:
                    case_data['overdue_days'] = log['overdue_days']
                if 'outstanding_amount' in log and log['outstanding_amount'] is not None:
                    case_data['outstanding_amount'] = log['outstanding_amount']
                if 'loan_amount_sanctioned' in log and log['loan_amount_sanctioned'] is not None:
                    case_data['loan_amount'] = log['loan_amount_sanctioned']

            # Check 1: Classification mismatch (if overdue days and classification present)
            if 'overdue_days' in case_data and 'npa_classification' in case_data:
                try:
                    overdue = int(case_data['overdue_days'])
                    reported_class = str(case_data['npa_classification']).lower().replace(' ', '_').replace('-', '_')

                    # Determine expected classification based on DPD
                    expected_class = None
                    for class_name, thresholds in classification_thresholds.items():
                        if thresholds['min_dpd'] <= overdue <= thresholds['max_dpd']:
                            expected_class = class_name
                            break

                    if expected_class and reported_class != expected_class:
                        # Allow some flexibility in naming (sub-standard vs substandard)
                        reported_normalized = reported_class.replace('_', '').replace('sub', '').replace('standard', '')
                        expected_normalized = expected_class.replace('_', '').replace('sub', '').replace('standard', '')

                        if reported_normalized != expected_normalized:
                            deviations.append({
                                'case_id': case_id,
                                'officer_id': officer_id,
                                'timestamp': timestamp,
                                'deviation_type': 'classification_mismatch',
                                'severity': 'high',
                                'description': f'Asset classification mismatch: {overdue} DPD classified as {reported_class} (should be {expected_class})',
                                'expected_behavior': f'At {overdue} DPD, classification should be {expected_class}',
                                'actual_behavior': f'Classified as {reported_class}',
                                'context': {
                                    'overdue_days': overdue,
                                    'reported_classification': reported_class,
                                    'expected_classification': expected_class
                                }
                            })
                except (ValueError, TypeError):
                    pass

            # Check 2: Provisioning shortfall (if classification and amounts present)
            if 'npa_classification' in case_data and ('provisioning_amount' in case_data or 'overdue_days' in case_data):
                reported_class = str(case_data['npa_classification']).lower().replace(' ', '_').replace('-', '_')

                # Get provisioning rate
                provisioning_rate = None
                for class_name, thresholds in classification_thresholds.items():
                    if class_name in reported_class or reported_class in class_name:
                        provisioning_rate = thresholds['provisioning']
                        break

                if provisioning_rate is not None:
                    # Calculate required provisioning
                    outstanding = case_data.get('outstanding_amount') or case_data.get('loan_amount', 0)

                    if outstanding:
                        try:
                            outstanding = float(outstanding)
                            required_provisioning = outstanding * provisioning_rate

                            actual_provisioning = float(case_data.get('provisioning_amount', 0))

                            # Allow 5% tolerance
                            tolerance = required_provisioning * 0.05
                            shortfall = required_provisioning - actual_provisioning

                            if shortfall > tolerance:
                                deviations.append({
                                    'case_id': case_id,
                                    'officer_id': officer_id,
                                    'timestamp': timestamp,
                                    'deviation_type': 'provisioning_shortfall',
                                    'severity': 'high',
                                    'description': f'Provisioning shortfall: Required {required_provisioning:.2f} ({provisioning_rate:.1%}) but provided {actual_provisioning:.2f}',
                                    'expected_behavior': f'{reported_class} loans require {provisioning_rate:.1%} provisioning',
                                    'actual_behavior': f'Provisioned: {actual_provisioning:.2f} (shortfall: {shortfall:.2f})',
                                    'context': {
                                        'classification': reported_class,
                                        'outstanding_amount': outstanding,
                                        'required_provisioning': required_provisioning,
                                        'actual_provisioning': actual_provisioning,
                                        'shortfall': shortfall,
                                        'provisioning_rate': provisioning_rate
                                    }
                                })
                        except (ValueError, TypeError):
                            pass

            # Check 3: Regulatory report missing or late (placeholder - requires reporting schedule)
            # This check would require additional context about reporting schedules
            # For now, we check if classification/provisioning steps exist for NPA cases
            if case_data.get('overdue_days', 0) >= 90:  # NPA threshold
                has_classification_step = any('classif' in step.lower() or 'npa' in step.lower() for step in step_names)
                has_provisioning_step = any('provision' in step.lower() for step in step_names)

                if not has_classification_step and not has_provisioning_step:
                    # Missing regulatory compliance steps for NPA case
                    deviations.append({
                        'case_id': case_id,
                        'officer_id': officer_id,
                        'timestamp': timestamp,
                        'deviation_type': 'regulatory_report_missing_or_late',
                        'severity': 'high',
                        'description': f'NPA case (≥90 DPD) without classification/provisioning steps',
                        'expected_behavior': 'NPA cases require timely classification and provisioning',
                        'actual_behavior': 'No classification or provisioning steps found',
                        'context': {
                            'overdue_days': case_data.get('overdue_days'),
                            'has_classification_step': has_classification_step,
                            'has_provisioning_step': has_provisioning_step
                        }
                    })

        return deviations
