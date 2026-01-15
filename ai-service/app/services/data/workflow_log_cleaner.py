"""
Workflow Log Cleaner Module

Cleans raw workflow logs BEFORE deviation detection.
This ensures deviation detection works on clean, validated data.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from collections import Counter
from .missing_field_analyzer import MissingFieldAnalyzer

logger = logging.getLogger(__name__)


class WorkflowLogCleaner:
    """
    Cleans and validates workflow logs before deviation detection.
    """

    @staticmethod
    def clean_logs(
        logs: List[Dict[str, Any]],
        remove_duplicates: bool = True,
        validate_types: bool = True,
        handle_missing: bool = True,
        normalize_text: bool = True,
        rules: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Clean workflow logs with comprehensive quality checks.

        Args:
            logs: List of workflow log dictionaries
            remove_duplicates: Remove duplicate log entries
            validate_types: Validate and fix data types
            handle_missing: Handle missing required fields
            normalize_text: Normalize text fields
            rules: Optional SOP rules for missing field analysis

        Returns:
            Tuple of (cleaned_logs, cleaning_report)
        """
        logger.info(f"Starting workflow log cleaning for {len(logs)} logs")

        original_count = len(logs)
        cleaned_logs = logs.copy()

        # Initialize report
        report = {
            'original_count': original_count,
            'duplicates_removed': 0,
            'invalid_types_fixed': 0,
            'missing_values_handled': 0,
            'text_normalized': 0,
            'invalid_logs_removed': 0,
            'validation_errors': [],
            'final_count': 0
        }

        # Required fields for workflow logs
        required_fields = ['case_id', 'officer_id', 'step_name', 'action', 'timestamp']

        # Step 1: Remove duplicates
        if remove_duplicates:
            cleaned_logs, duplicates_removed = WorkflowLogCleaner._remove_duplicates(cleaned_logs)
            report['duplicates_removed'] = duplicates_removed
            logger.info(f"Removed {duplicates_removed} duplicate logs")

        # Step 2: Validate required fields and remove invalid logs
        validated_logs = []
        invalid_count = 0

        for log in cleaned_logs:
            is_valid = True
            missing_fields = []

            # Check required fields
            for field in required_fields:
                if field not in log or log[field] is None or log[field] == '':
                    missing_fields.append(field)
                    is_valid = False

            if is_valid:
                validated_logs.append(log)
            else:
                invalid_count += 1
                report['validation_errors'].append(
                    f"Log missing required fields: {', '.join(missing_fields)} "
                    f"(case: {log.get('case_id', 'unknown')})"
                )

        cleaned_logs = validated_logs
        report['invalid_logs_removed'] = invalid_count
        logger.info(f"Removed {invalid_count} invalid logs")

        # Step 3: Validate and fix data types
        if validate_types:
            cleaned_logs, type_fixes = WorkflowLogCleaner._validate_types(cleaned_logs)
            report['invalid_types_fixed'] = type_fixes
            logger.info(f"Fixed {type_fixes} type issues")

        # Step 4: Handle missing optional fields
        if handle_missing:
            cleaned_logs, missing_handled = WorkflowLogCleaner._handle_missing_values(cleaned_logs)
            report['missing_values_handled'] = missing_handled
            logger.info(f"Handled {missing_handled} missing values")

        # Step 5: Normalize text fields
        if normalize_text:
            cleaned_logs, normalized_count = WorkflowLogCleaner._normalize_text(cleaned_logs)
            report['text_normalized'] = normalized_count
            logger.info(f"Normalized {normalized_count} text fields")

        report['final_count'] = len(cleaned_logs)
        logger.info(f"Cleaning complete: {original_count} → {len(cleaned_logs)} logs")

        # Step 6: Check for missing audit trail fields (log quality, not deviation)
        audit_trail_issues = WorkflowLogCleaner._check_audit_trail_completeness(cleaned_logs)
        report['audit_trail_issues'] = audit_trail_issues
        logger.info(f"Audit trail check: {audit_trail_issues['critical_steps_missing_audit_trail']} critical steps without audit trail")

        # Run missing field analysis if rules are provided
        if rules and len(rules) > 0:
            logger.info(f"Running missing field analysis with {len(rules)} rules")
            missing_field_analysis = MissingFieldAnalyzer.analyze_missing_fields(rules, cleaned_logs)
            report['missing_field_analysis'] = missing_field_analysis
            logger.info(f"Missing field analysis complete: {len(missing_field_analysis['missing_fields'])} missing fields identified")
        else:
            report['missing_field_analysis'] = None

        return cleaned_logs, report

    @staticmethod
    def _remove_duplicates(logs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """Remove duplicate log entries based on key fields."""
        seen = set()
        unique_logs = []

        for log in logs:
            # Create a unique key from critical fields
            key = (
                log.get('case_id'),
                log.get('officer_id'),
                log.get('step_name'),
                log.get('action'),
                log.get('timestamp')
            )

            if key not in seen:
                seen.add(key)
                unique_logs.append(log)

        duplicates_removed = len(logs) - len(unique_logs)
        return unique_logs, duplicates_removed

    @staticmethod
    def _validate_types(logs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """Validate and fix data types in logs."""
        fixes = 0

        for log in logs:
            # Ensure string fields are strings
            string_fields = ['case_id', 'officer_id', 'step_name', 'action', 'status']
            for field in string_fields:
                if field in log and log[field] is not None:
                    if not isinstance(log[field], str):
                        log[field] = str(log[field]).strip()
                        fixes += 1

            # Ensure numeric fields are numbers
            if 'duration_seconds' in log and log['duration_seconds'] is not None:
                try:
                    if isinstance(log['duration_seconds'], str):
                        log['duration_seconds'] = int(float(log['duration_seconds']))
                        fixes += 1
                except (ValueError, TypeError):
                    log['duration_seconds'] = None
                    fixes += 1

            # Normalize percentage fields: convert raw percentages (42) to decimals (0.42)
            percentage_fields = ['emi_to_income_ratio', 'ltv_ratio', 'dti_ratio']
            for field in percentage_fields:
                if field in log and log[field] is not None:
                    try:
                        value = float(log[field])
                        # If value > 1, assume it's stored as raw percentage (42 = 42%)
                        if value > 1:
                            log[field] = value / 100.0  # Convert to decimal: 42 → 0.42
                            fixes += 1
                    except (ValueError, TypeError):
                        pass  # Keep original if conversion fails

            # Validate timestamp format
            if 'timestamp' in log and log['timestamp'] is not None:
                if isinstance(log['timestamp'], str):
                    # Try to parse and reformat timestamp
                    try:
                        # Handle various timestamp formats
                        timestamp_str = log['timestamp'].split('.')[0]  # Remove microseconds
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                            try:
                                dt = datetime.strptime(timestamp_str, fmt)
                                log['timestamp'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                                break
                            except ValueError:
                                continue
                    except Exception:
                        # Keep original if parsing fails
                        pass

        return logs, fixes

    @staticmethod
    def _handle_missing_values(logs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """Handle missing optional fields with defaults."""
        handled = 0

        for log in logs:
            # Set default values for optional fields
            if 'duration_seconds' not in log or log['duration_seconds'] is None:
                log['duration_seconds'] = 0
                handled += 1

            if 'status' not in log or log['status'] is None:
                log['status'] = 'completed'
                handled += 1

            if 'metadata' not in log or log['metadata'] is None:
                log['metadata'] = {}
                handled += 1

        return logs, handled

    @staticmethod
    def _normalize_text(logs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """Normalize text fields (trim, lowercase where appropriate)."""
        normalized = 0

        for log in logs:
            # Trim whitespace from string fields
            for field in ['case_id', 'officer_id', 'step_name', 'action', 'status']:
                if field in log and isinstance(log[field], str):
                    original = log[field]
                    log[field] = log[field].strip()
                    if original != log[field]:
                        normalized += 1

            # Normalize step_name and action to uppercase for consistency
            if 'step_name' in log and isinstance(log['step_name'], str):
                original = log['step_name']
                log['step_name'] = log['step_name'].upper()
                if original != log['step_name']:
                    normalized += 1

            if 'action' in log and isinstance(log['action'], str):
                original = log['action']
                log['action'] = log['action'].upper()
                if original != log['action']:
                    normalized += 1

        return logs, normalized

    @staticmethod
    def _check_audit_trail_completeness(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check for missing audit trail fields in critical steps.
        This is a LOG QUALITY check, not a compliance deviation.

        Returns:
            Dict with audit trail completeness metrics
        """
        total_logs = len(logs)
        total_critical_steps = 0
        missing_audit_trail = 0
        affected_cases = set()

        CRITICAL_STEP_KEYWORDS = ['approval', 'disbursement', 'sanction', 'final']

        for log in logs:
            step_name = str(log.get('step_name', '')).lower()

            # Check if this is a critical step
            is_critical = any(keyword in step_name for keyword in CRITICAL_STEP_KEYWORDS)

            if is_critical:
                total_critical_steps += 1

                # Check if audit trail fields are present
                has_audit_trail_id = 'audit_trail_id' in log and log['audit_trail_id'] is not None
                has_source_system = 'source_system' in log and log['source_system'] is not None

                if not has_audit_trail_id and not has_source_system:
                    missing_audit_trail += 1
                    affected_cases.add(log.get('case_id', 'unknown'))

        return {
            'total_logs': total_logs,
            'total_critical_steps': total_critical_steps,
            'critical_steps_missing_audit_trail': missing_audit_trail,
            'affected_cases_count': len(affected_cases),
            'audit_trail_completeness_rate': (
                ((total_critical_steps - missing_audit_trail) / total_critical_steps * 100)
                if total_critical_steps > 0 else 100.0
            ),
            'note': 'Audit trail fields (audit_trail_id or source_system) should be present for critical steps (approval, disbursement, sanction)'
        }

    @staticmethod
    def get_data_quality_score(report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate data quality score based on cleaning report.

        Returns dict with:
            - score: 0-100
            - grade: A-F
            - assessment: text description
        """
        if report['original_count'] == 0:
            return {
                'score': 0,
                'grade': 'F',
                'assessment': 'No data'
            }

        # Calculate score based on issues found
        original = report['original_count']
        final = report['final_count']

        # Retention rate (weight: 40%)
        retention_rate = (final / original) * 100 if original > 0 else 0
        retention_score = (retention_rate / 100) * 40

        # Duplicate rate (weight: 20%)
        duplicate_rate = (report['duplicates_removed'] / original) * 100 if original > 0 else 0
        duplicate_score = max(0, 20 - duplicate_rate)  # Fewer duplicates = higher score

        # Validation error rate (weight: 25%)
        invalid_rate = (report['invalid_logs_removed'] / original) * 100 if original > 0 else 0
        validation_score = max(0, 25 - (invalid_rate * 2))  # Penalize invalid logs

        # Type fix rate (weight: 15%)
        type_fix_rate = (report['invalid_types_fixed'] / original) * 100 if original > 0 else 0
        type_score = max(0, 15 - type_fix_rate)

        # Total score
        total_score = retention_score + duplicate_score + validation_score + type_score

        # Assign grade
        if total_score >= 90:
            grade = 'A'
            assessment = 'Excellent data quality'
        elif total_score >= 80:
            grade = 'B'
            assessment = 'Good data quality'
        elif total_score >= 70:
            grade = 'C'
            assessment = 'Fair data quality'
        elif total_score >= 60:
            grade = 'D'
            assessment = 'Poor data quality - improvements needed'
        else:
            grade = 'F'
            assessment = 'Very poor data quality - major issues'

        return {
            'score': round(total_score, 2),
            'grade': grade,
            'assessment': assessment,
            'details': {
                'retention_rate': round(retention_rate, 2),
                'duplicate_rate': round(duplicate_rate, 2),
                'invalid_rate': round(invalid_rate, 2),
                'type_fix_rate': round(type_fix_rate, 2)
            }
        }
