from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime

class DataQualityChecker:
    """
    Checks data quality and audit trail deviations.

    DEVIATION TYPES DETECTED:
    - missing_core_field: Required core field (case_id, officer_id, step_name, timestamp) missing
    - invalid_format: Field value has invalid format (dates, amounts, IDs)
    - inconsistent_value_across_steps: Field value changes inconsistently across workflow
    - duplicate_active_case: Same case_id appears multiple times in active cases
    - audit_trail_missing: Audit trail information missing or incomplete

    DEFENSIVE: Always runs (validates core required fields).
    """

    @staticmethod
    def check_data_quality(logs: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check data quality and audit trail deviations.

        Args:
            logs: Workflow logs (all logs validated for core fields)
            rules: SOP rules (data_quality type)

        Returns:
            List of data quality deviations detected
        """
        deviations = []

        # Core required fields for all workflow logs
        core_fields = ['case_id', 'officer_id', 'step_name', 'timestamp']

        # Extract data quality rules
        dq_rules = [r for r in rules if r.get('rule_type') == 'data_quality']

        # Track case IDs for duplicate detection
        case_occurrences = defaultdict(int)

        # Track field consistency across steps
        case_field_values = defaultdict(lambda: defaultdict(set))

        # Check each log
        for i, log in enumerate(logs):
            log_identifier = f"Log #{i+1}"
            case_id = log.get('case_id', f'unknown_case_{i}')

            # Check 1: Missing core fields
            for field in core_fields:
                if field not in log or log[field] is None or str(log[field]).strip() == '':
                    deviations.append({
                        'case_id': case_id,
                        'officer_id': log.get('officer_id', 'unknown'),
                        'timestamp': log.get('timestamp'),
                        'deviation_type': 'missing_core_field',
                        'severity': 'critical',
                        'description': f'Missing required core field: {field}',
                        'expected_behavior': f'All workflow logs must have {field}',
                        'actual_behavior': f'{field} is missing or empty',
                        'context': {
                            'log_identifier': log_identifier,
                            'missing_field': field,
                            'available_fields': list(log.keys())
                        }
                    })

            # Check 2: Invalid format - timestamp
            if 'timestamp' in log and log['timestamp']:
                try:
                    # Try parsing timestamp
                    ts_str = str(log['timestamp']).split('.')[0].replace('Z', '')
                    datetime.fromisoformat(ts_str)
                except (ValueError, AttributeError):
                    deviations.append({
                        'case_id': case_id,
                        'officer_id': log.get('officer_id', 'unknown'),
                        'timestamp': None,
                        'deviation_type': 'invalid_format',
                        'severity': 'high',
                        'description': f'Invalid timestamp format: {log["timestamp"]}',
                        'expected_behavior': 'Timestamp must be in ISO format (YYYY-MM-DDTHH:MM:SS)',
                        'actual_behavior': f'Timestamp: {log["timestamp"]}',
                        'context': {
                            'log_identifier': log_identifier,
                            'field': 'timestamp',
                            'value': log['timestamp']
                        }
                    })

            # Check 3: Invalid format - amounts (should be numeric)
            amount_fields = ['loan_amount_requested', 'loan_amount_sanctioned', 'disbursement_amount',
                           'emi_amount', 'outstanding_amount', 'collateral_value', 'provisioning_amount']

            for field in amount_fields:
                if field in log and log[field] is not None:
                    try:
                        value = float(log[field])
                        if value < 0:  # Negative amounts are invalid
                            deviations.append({
                                'case_id': case_id,
                                'officer_id': log.get('officer_id', 'unknown'),
                                'timestamp': log.get('timestamp'),
                                'deviation_type': 'invalid_format',
                                'severity': 'high',
                                'description': f'Negative amount in {field}: {value}',
                                'expected_behavior': f'{field} must be positive',
                                'actual_behavior': f'{field}: {value}',
                                'context': {
                                    'log_identifier': log_identifier,
                                    'field': field,
                                    'value': value
                                }
                            })
                    except (ValueError, TypeError):
                        deviations.append({
                            'case_id': case_id,
                            'officer_id': log.get('officer_id', 'unknown'),
                            'timestamp': log.get('timestamp'),
                            'deviation_type': 'invalid_format',
                            'severity': 'medium',
                            'description': f'Non-numeric value in {field}: {log[field]}',
                            'expected_behavior': f'{field} must be numeric',
                            'actual_behavior': f'{field}: {log[field]}',
                            'context': {
                                'log_identifier': log_identifier,
                                'field': field,
                                'value': log[field]
                            }
                        })

            # Track case occurrences
            if 'case_id' in log and log['case_id']:
                case_occurrences[log['case_id']] += 1

            # Track field consistency (immutable fields shouldn't change)
            immutable_fields = ['customer_id', 'customer_name', 'application_id', 'loan_id', 'product_type']
            for field in immutable_fields:
                if field in log and log[field] is not None:
                    case_field_values[case_id][field].add(str(log[field]))

            # Check 4: Audit trail missing → MOVED TO LOG QUALITY REPORT
            # This is now reported in workflow_log_cleaner.py as part of log quality metrics
            # Not counted as a compliance deviation per user request

        # Check 5: Duplicate active cases (same case_id with multiple active workflows)
        # Note: This is a simplified check - in production, would check against database
        for case_id, count in case_occurrences.items():
            if count > 20:  # Unusually high number of steps for one case
                deviations.append({
                    'case_id': case_id,
                    'officer_id': 'system',
                    'timestamp': None,
                    'deviation_type': 'duplicate_active_case',
                    'severity': 'medium',
                    'description': f'Case {case_id} appears {count} times in workflow (possible duplicate or loop)',
                    'expected_behavior': 'Typical workflow has 7-15 steps per case',
                    'actual_behavior': f'{count} log entries for this case',
                    'context': {
                        'case_id': case_id,
                        'occurrence_count': count
                    }
                })

        # Check 6: Inconsistent values across steps (immutable fields changing)
        for case_id, field_values in case_field_values.items():
            for field, values in field_values.items():
                if len(values) > 1:  # Field has multiple different values
                    deviations.append({
                        'case_id': case_id,
                        'officer_id': 'system',
                        'timestamp': None,
                        'deviation_type': 'inconsistent_value_across_steps',
                        'severity': 'high',
                        'description': f'Immutable field "{field}" has inconsistent values across workflow: {", ".join(values)}',
                        'expected_behavior': f'{field} should remain constant throughout case lifecycle',
                        'actual_behavior': f'Found {len(values)} different values: {", ".join(list(values)[:3])}',
                        'context': {
                            'case_id': case_id,
                            'field': field,
                            'values': list(values)
                        }
                    })

        return deviations
