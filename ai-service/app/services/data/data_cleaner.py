"""
Data Cleaning Module for Deviation Analysis

This module provides comprehensive data cleaning functionality:
1. Duplicate removal
2. Missing value handling
3. Data validation and type checking
4. Text normalization
5. Outlier detection in numeric fields
"""

import logging
from typing import List, Dict, Any, Tuple, Set
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class DataCleaner:
    """
    Handles all data cleaning operations for deviation analysis.
    """

    # Valid values for categorical fields
    VALID_SEVERITIES = {'low', 'medium', 'high', 'critical'}
    VALID_DEVIATION_TYPES = {
        'missing_step', 'wrong_sequence', 'unexpected_step', 'duplicate_step',
        'skipped_mandatory_subprocess', 'missing_approval', 'insufficient_approval_hierarchy',
        'unauthorized_approver', 'self_approval_violation', 'escalation_missing',
        'timing_violation', 'tat_breach', 'cutoff_breach', 'post_disbursement_qc_delay',
        'ineligible_age', 'ineligible_tenor', 'emi_to_income_breach',
        'low_score_approved_without_exception', 'kyc_incomplete_progression',
        'sanctions_hit_not_rejected', 'pep_no_edd_or_extra_approval',
        'missing_mandatory_document', 'expired_document_used', 'legal_clearance_missing',
        'collateral_docs_incomplete', 'ltv_breach', 'valuation_missing_or_stale',
        'security_not_created', 'pre_disbursement_condition_unmet',
        'mandate_not_set_before_disbursement', 'incorrect_disbursement_amount',
        'post_disbursement_qc_missing', 'collection_escalation_delay',
        'unauthorized_restructure', 'unauthorized_writeoff', 'classification_mismatch',
        'provisioning_shortfall', 'regulatory_report_missing_or_late',
        'missing_core_field', 'invalid_format', 'inconsistent_value_across_steps',
        'duplicate_active_case', 'audit_trail_missing'
    }

    @staticmethod
    def clean_deviations(deviations: List[Dict[str, Any]],
                        remove_duplicates: bool = True,
                        validate_types: bool = True,
                        handle_missing: bool = True,
                        normalize_text: bool = True) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Clean deviation data with comprehensive quality checks.

        Args:
            deviations: List of deviation dictionaries
            remove_duplicates: Whether to remove duplicate deviations
            validate_types: Whether to validate and fix data types
            handle_missing: Whether to handle missing values
            normalize_text: Whether to normalize text fields

        Returns:
            Tuple of (cleaned_deviations, cleaning_report)
        """
        logger.info(f"Starting data cleaning for {len(deviations)} deviations")

        cleaning_report = {
            'original_count': len(deviations),
            'duplicates_removed': 0,
            'invalid_types_fixed': 0,
            'missing_values_handled': 0,
            'text_normalized': 0,
            'validation_errors': [],
            'warnings': []
        }

        if len(deviations) == 0:
            logger.warning("No deviations to clean")
            return [], cleaning_report

        cleaned = deviations.copy()

        # Step 1: Remove duplicates
        if remove_duplicates:
            cleaned, dup_count = DataCleaner._remove_duplicates(cleaned)
            cleaning_report['duplicates_removed'] = dup_count

        # Step 2: Validate and fix data types
        if validate_types:
            cleaned, type_fixes = DataCleaner._validate_and_fix_types(cleaned)
            cleaning_report['invalid_types_fixed'] = type_fixes

        # Step 3: Handle missing values
        if handle_missing:
            cleaned, missing_handled = DataCleaner._handle_missing_values(cleaned)
            cleaning_report['missing_values_handled'] = missing_handled

        # Step 4: Normalize text fields
        if normalize_text:
            cleaned, text_normalized = DataCleaner._normalize_text_fields(cleaned)
            cleaning_report['text_normalized'] = text_normalized

        # Step 5: Final validation
        cleaned, validation_errors = DataCleaner._final_validation(cleaned)
        cleaning_report['validation_errors'] = validation_errors

        cleaning_report['final_count'] = len(cleaned)
        cleaning_report['cleaned_percentage'] = round(
            (cleaning_report['final_count'] / cleaning_report['original_count']) * 100, 2
        ) if cleaning_report['original_count'] > 0 else 0

        logger.info(f"Data cleaning complete: {cleaning_report['final_count']}/{cleaning_report['original_count']} deviations retained")
        logger.info(f"Removed {cleaning_report['duplicates_removed']} duplicates, "
                   f"fixed {cleaning_report['invalid_types_fixed']} type errors, "
                   f"handled {cleaning_report['missing_values_handled']} missing values")

        return cleaned, cleaning_report

    @staticmethod
    def _remove_duplicates(deviations: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Remove duplicate deviations based on case_id, officer_id, and deviation_type.
        Keeps the first occurrence.
        """
        seen: Set[Tuple[str, str, str]] = set()
        unique_deviations = []
        duplicates_count = 0

        for deviation in deviations:
            case_id = str(deviation.get('case_id', '')).strip()
            officer_id = str(deviation.get('officer_id', '')).strip()
            deviation_type = str(deviation.get('deviation_type', '')).strip().lower()

            key = (case_id, officer_id, deviation_type)

            if key not in seen:
                seen.add(key)
                unique_deviations.append(deviation)
            else:
                duplicates_count += 1
                logger.debug(f"Duplicate found: {key}")

        return unique_deviations, duplicates_count

    @staticmethod
    def _validate_and_fix_types(deviations: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Validate and fix data types for all fields.
        """
        fixed_count = 0

        for deviation in deviations:
            original_deviation = deviation.copy()

            # Ensure string fields are strings
            string_fields = ['case_id', 'officer_id', 'deviation_type', 'severity',
                           'description', 'expected_behavior', 'actual_behavior', 'notes']

            for field in string_fields:
                if field in deviation and deviation[field] is not None:
                    if not isinstance(deviation[field], str):
                        deviation[field] = str(deviation[field])
                        fixed_count += 1

            # Normalize severity to lowercase
            if 'severity' in deviation and deviation['severity']:
                normalized_severity = deviation['severity'].strip().lower()
                if normalized_severity not in DataCleaner.VALID_SEVERITIES:
                    # Try to map common variants
                    severity_map = {
                        'crit': 'critical',
                        'hi': 'high',
                        'med': 'medium',
                        'lo': 'low',
                        'important': 'high',
                        'minor': 'low'
                    }
                    normalized_severity = severity_map.get(normalized_severity, 'medium')
                    logger.warning(f"Invalid severity '{deviation['severity']}' mapped to '{normalized_severity}'")
                    fixed_count += 1

                deviation['severity'] = normalized_severity

            # Normalize deviation_type to lowercase and underscore
            if 'deviation_type' in deviation and deviation['deviation_type']:
                normalized_type = deviation['deviation_type'].strip().lower()
                normalized_type = re.sub(r'[- ]+', '_', normalized_type)  # Replace spaces/hyphens with underscore

                if normalized_type not in DataCleaner.VALID_DEVIATION_TYPES:
                    logger.warning(f"Unknown deviation type: {normalized_type}")

                if normalized_type != deviation['deviation_type']:
                    deviation['deviation_type'] = normalized_type
                    fixed_count += 1

        return deviations, fixed_count

    @staticmethod
    def _handle_missing_values(deviations: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Handle missing values in critical fields.
        """
        handled_count = 0
        valid_deviations = []

        for deviation in deviations:
            # Required fields that cannot be missing
            required_fields = ['case_id', 'officer_id', 'deviation_type', 'severity', 'description']

            has_missing_required = False
            for field in required_fields:
                value = deviation.get(field)
                if value is None or (isinstance(value, str) and value.strip() == ''):
                    logger.warning(f"Deviation missing required field '{field}': {deviation.get('case_id', 'unknown')}")
                    has_missing_required = True
                    break

            if has_missing_required:
                handled_count += 1
                continue  # Skip this deviation

            # Optional fields - fill with defaults
            if not deviation.get('expected_behavior'):
                deviation['expected_behavior'] = 'Not specified'

            if not deviation.get('actual_behavior'):
                deviation['actual_behavior'] = 'Not specified'

            if not deviation.get('notes'):
                deviation['notes'] = ''

            valid_deviations.append(deviation)

        return valid_deviations, handled_count

    @staticmethod
    def _normalize_text_fields(deviations: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Normalize text fields (trim whitespace, fix encoding, etc.).
        """
        normalized_count = 0
        text_fields = ['description', 'expected_behavior', 'actual_behavior', 'notes']

        for deviation in deviations:
            for field in text_fields:
                if field in deviation and deviation[field]:
                    original = deviation[field]

                    # Strip whitespace
                    normalized = original.strip()

                    # Remove excessive whitespace
                    normalized = re.sub(r'\s+', ' ', normalized)

                    # Remove control characters (except newlines and tabs)
                    normalized = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', normalized)

                    if normalized != original:
                        deviation[field] = normalized
                        normalized_count += 1

        return deviations, normalized_count

    @staticmethod
    def _final_validation(deviations: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Final validation pass to ensure data quality.
        """
        validation_errors = []
        valid_deviations = []

        for i, deviation in enumerate(deviations):
            errors = []

            # Check case_id format (should be non-empty)
            if not deviation.get('case_id') or len(str(deviation['case_id']).strip()) == 0:
                errors.append(f"Invalid case_id at index {i}")

            # Check officer_id format
            if not deviation.get('officer_id') or len(str(deviation['officer_id']).strip()) == 0:
                errors.append(f"Invalid officer_id at index {i}")

            # Check description length (should have meaningful content)
            description = deviation.get('description', '')
            if len(description) < 10:
                errors.append(f"Description too short at index {i}: '{description}'")

            if errors:
                validation_errors.extend(errors)
                logger.warning(f"Validation failed for deviation {i}: {errors}")
            else:
                valid_deviations.append(deviation)

        return valid_deviations, validation_errors

    @staticmethod
    def get_data_quality_score(cleaning_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate a data quality score based on the cleaning report.

        Returns a quality assessment with score (0-100) and grade (A-F).
        """
        total_issues = (
            cleaning_report['duplicates_removed'] +
            cleaning_report['invalid_types_fixed'] +
            cleaning_report['missing_values_handled']
        )

        original_count = cleaning_report['original_count']

        if original_count == 0:
            return {
                'score': 0,
                'grade': 'N/A',
                'assessment': 'No data to assess'
            }

        # Calculate quality score (0-100)
        issue_percentage = (total_issues / original_count) * 100
        quality_score = max(0, 100 - issue_percentage)

        # Assign grade
        if quality_score >= 95:
            grade = 'A'
            assessment = 'Excellent data quality'
        elif quality_score >= 85:
            grade = 'B'
            assessment = 'Good data quality'
        elif quality_score >= 70:
            grade = 'C'
            assessment = 'Acceptable data quality'
        elif quality_score >= 60:
            grade = 'D'
            assessment = 'Poor data quality'
        else:
            grade = 'F'
            assessment = 'Very poor data quality'

        return {
            'score': round(quality_score, 2),
            'grade': grade,
            'assessment': assessment,
            'total_issues': total_issues,
            'issue_percentage': round(issue_percentage, 2)
        }
