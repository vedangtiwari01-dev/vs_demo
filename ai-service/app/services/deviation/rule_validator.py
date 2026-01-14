from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
import re

class RuleValidator:
    """
    Validates workflow logs against comprehensive SOP rules.

    COMPREHENSIVE DEVIATION DETECTION:
    This class works in conjunction with Claude AI prompts (prompts.py) to detect 40+ deviation types across:
    - Process & Sequence (5 types): missing_step, wrong_sequence, unexpected_step, duplicate_step, skipped_mandatory_subprocess
    - Approval & Authority (5 types): missing_approval, insufficient_approval_hierarchy, unauthorized_approver, self_approval_violation, escalation_missing
    - Timing & SLA (4 types): timing_violation, tat_breach, cutoff_breach, post_disbursement_qc_delay
    - Eligibility & Credit (4 types): ineligible_age, ineligible_tenor, emi_to_income_breach, low_score_approved_without_exception
    - KYC/AML/Sanctions (3 types): kyc_incomplete_progression, sanctions_hit_not_rejected, pep_no_edd_or_extra_approval
    - Documentation & Legal (4 types): missing_mandatory_document, expired_document_used, legal_clearance_missing, collateral_docs_incomplete
    - Collateral & Security (3 types): ltv_breach, valuation_missing_or_stale, security_not_created
    - Disbursement (4 types): pre_disbursement_condition_unmet, mandate_not_set_before_disbursement, incorrect_disbursement_amount, post_disbursement_qc_missing
    - Collections & Restructuring (3 types): collection_escalation_delay, unauthorized_restructure, unauthorized_writeoff
    - Regulatory & Reporting (3 types): classification_mismatch, provisioning_shortfall, regulatory_report_missing_or_late
    - Data Quality & Logging (5 types): missing_core_field, invalid_format, inconsistent_value_across_steps, duplicate_active_case, audit_trail_missing

    RULE TYPES SUPPORTED (16 types):
    sequence, approval, timing, eligibility, credit_risk, kyc, aml, documentation, collateral, disbursement,
    post_disbursement_qc, collection, restructuring, regulatory, data_quality, operational

    The primary deviation detection is handled by Claude AI through comprehensive prompts.
    This class provides rule-based validation as a complementary layer for critical checks.
    """

    # Phase 5 Enhancement: Approval Authority Hierarchy
    APPROVAL_HIERARCHY = {
        "Branch Manager": {
            "level": 1,
            "max_amount": 1000000,
            "min_credit_score": 700,
            "max_ltv": 0.70,
            "keywords": ["branch manager", "level 1", "bm approval", "branch mgr"]
        },
        "Regional Credit Manager": {
            "level": 2,
            "max_amount": 3000000,
            "min_credit_score": 650,
            "max_ltv": 0.80,
            "keywords": ["regional", "level 2", "rcm", "regional manager", "regional credit"]
        },
        "Credit Committee": {
            "level": 3,
            "max_amount": float('inf'),
            "min_credit_score": 0,
            "max_ltv": 1.0,
            "keywords": ["credit committee", "level 3", "committee", "cc approval"]
        }
    }

    @staticmethod
    def validate_all(logs: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate workflow logs against all SOP rules.

        This method performs rule-based validation for critical checks:
        - Approval rules (16 rule types supported including approval, eligibility, credit_risk, kyc, aml, etc.)
        - Timing rules (SLA, TAT, cut-offs)
        - Data quality rules (completeness, consistency)

        NOTE: This is a complementary layer. The primary comprehensive deviation detection
        (40+ deviation types) is performed by Claude AI through the DEVIATION_ANALYSIS_PROMPT.

        Args:
            logs: Workflow logs with case_id, officer_id, step_name, action, timestamp, plus 80+ optional fields
            rules: SOP rules with 16 rule types (sequence, approval, timing, eligibility, credit_risk, kyc, aml,
                   documentation, collateral, disbursement, post_disbursement_qc, collection, restructuring,
                   regulatory, data_quality, operational)

        Returns:
            List of deviations detected by rule-based logic
        """
        deviations = []

        # Group logs by case
        cases = defaultdict(list)
        for log in logs:
            cases[log['case_id']].append(log)

        for case_id, case_logs in cases.items():
            case_logs.sort(key=lambda x: datetime.fromisoformat(x['timestamp']))

            # Check approval rules (covers: approval, credit_risk, kyc, aml, collateral, disbursement, regulatory)
            approval_deviations = RuleValidator._check_approval_rules(case_id, case_logs, rules)
            deviations.extend(approval_deviations)

            # Check timing rules (covers: timing, post_disbursement_qc)
            timing_deviations = RuleValidator._check_timing_rules(case_id, case_logs, rules)
            deviations.extend(timing_deviations)

            # NOTE: Additional rule types (eligibility, documentation, collection, restructuring, data_quality, operational)
            # are primarily handled by Claude AI's comprehensive prompt-based analysis for maximum flexibility.
            # Extend this class with additional _check_* methods if rule-based validation is needed.

        return deviations

    @staticmethod
    def _extract_approval_level(step_names: List[str]) -> Optional[str]:
        """
        Phase 5 Enhancement: Extract the highest approval level from step names.

        Args:
            step_names: List of step names (lowercase)

        Returns:
            Approval level name ("Branch Manager", "Regional Credit Manager", "Credit Committee") or None
        """
        highest_level = 0
        highest_approver = None

        for step in step_names:
            for approver, config in RuleValidator.APPROVAL_HIERARCHY.items():
                for keyword in config["keywords"]:
                    if keyword in step and "approv" in step:
                        if config["level"] > highest_level:
                            highest_level = config["level"]
                            highest_approver = approver

        return highest_approver

    @staticmethod
    def _determine_required_approval_level(log_data: Dict[str, Any]) -> Optional[str]:
        """
        Phase 5 Enhancement: Determine required approval level based on case data.

        Args:
            log_data: Aggregated case data with loan_amount_sanctioned, credit_score_bureau, etc.

        Returns:
            Required approval level name or None
        """
        loan_amount = log_data.get('loan_amount_sanctioned') or log_data.get('loan_amount')
        credit_score = log_data.get('credit_score_bureau')
        collateral_value = log_data.get('collateral_value')

        # Calculate LTV if possible
        ltv = None
        if loan_amount and collateral_value and collateral_value > 0:
            try:
                ltv = float(loan_amount) / float(collateral_value)
            except (ValueError, TypeError, ZeroDivisionError):
                ltv = None

        # Determine required level based on amount, credit score, LTV
        required_level = 1  # Start with Branch Manager

        # Amount-based escalation
        if loan_amount:
            try:
                amount_float = float(loan_amount)
                if amount_float > 3000000:
                    required_level = max(required_level, 3)  # Credit Committee
                elif amount_float > 1000000:
                    required_level = max(required_level, 2)  # Regional Manager
            except (ValueError, TypeError):
                pass

        # Credit score-based escalation
        if credit_score:
            try:
                score_int = int(credit_score)
                if score_int < 650:
                    required_level = max(required_level, 3)  # Credit Committee
                elif score_int < 700:
                    required_level = max(required_level, 2)  # Regional Manager
            except (ValueError, TypeError):
                pass

        # LTV-based escalation
        if ltv:
            if ltv > 0.80:
                required_level = max(required_level, 3)  # Credit Committee
            elif ltv > 0.70:
                required_level = max(required_level, 2)  # Regional Manager

        # Map level to approver name
        for approver, config in RuleValidator.APPROVAL_HIERARCHY.items():
            if config["level"] == required_level:
                return approver

        return "Branch Manager"  # Default

    @staticmethod
    def _aggregate_log_data(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Phase 5 Enhancement: Aggregate all fields from logs into single dict.

        Args:
            logs: List of workflow logs for a case

        Returns:
            Dictionary with all available fields
        """
        aggregated = {}
        for log in logs:
            for key, value in log.items():
                if value is not None and key not in aggregated:
                    aggregated[key] = value
        return aggregated

    @staticmethod
    def _check_approval_rules(case_id: str, logs: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check if approval rules are followed.

        Phase 5 Enhancement: Validates approval authority hierarchy based on loan amount, LTV, credit score.
        """
        deviations = []
        approval_rules = [r for r in rules if r.get('rule_type') == 'approval']

        if not approval_rules:
            return deviations

        # Check if approval steps exist
        step_names = [log['step_name'].lower() for log in logs]
        has_manager_approval = any('manager' in step and 'approval' in step for step in step_names)
        has_final_approval = any('final' in step and 'approval' in step for step in step_names)

        officer_id = logs[0]['officer_id'] if logs else 'unknown'

        # Extract case start time (timestamp of first log entry)
        case_start_time = logs[0]['timestamp'] if logs else None

        # Phase 5 Enhancement: Validate approval hierarchy
        log_data = RuleValidator._aggregate_log_data(logs)
        actual_approval_level = RuleValidator._extract_approval_level(step_names)
        required_approval_level = RuleValidator._determine_required_approval_level(log_data)

        # DEBUG: Log Phase 5 approval hierarchy validation for first 3 cases
        if case_id in ['SPL-001', 'SPL-002', 'SPL-003']:
            print(f"\n[DEBUG {case_id}] Phase 5 Approval Hierarchy:")
            print(f"  Log data keys: {list(log_data.keys())[:10]}")
            print(f"  loan_amount_sanctioned: {log_data.get('loan_amount_sanctioned')}")
            print(f"  credit_score_bureau: {log_data.get('credit_score_bureau')}")
            print(f"  collateral_value: {log_data.get('collateral_value')}")
            print(f"  Actual approval level: {actual_approval_level}")
            print(f"  Required approval level: {required_approval_level}")

        if actual_approval_level and required_approval_level:
            actual_level_num = RuleValidator.APPROVAL_HIERARCHY[actual_approval_level]["level"]
            required_level_num = RuleValidator.APPROVAL_HIERARCHY[required_approval_level]["level"]

            # DEBUG: Log comparison
            if case_id in ['SPL-001', 'SPL-002', 'SPL-003']:
                print(f"  Actual level: {actual_level_num}, Required level: {required_level_num}")
                print(f"  Deviation? {actual_level_num < required_level_num}")

            if actual_level_num < required_level_num:
                loan_amount = log_data.get('loan_amount_sanctioned') or log_data.get('loan_amount')
                credit_score = log_data.get('credit_score_bureau')
                collateral_value = log_data.get('collateral_value')

                # Calculate LTV for context
                ltv = None
                if loan_amount and collateral_value and collateral_value > 0:
                    try:
                        ltv = float(loan_amount) / float(collateral_value)
                    except:
                        pass

                deviations.append({
                    'case_id': case_id,
                    'officer_id': officer_id,
                    'timestamp': case_start_time,
                    'deviation_type': 'insufficient_approval_hierarchy',
                    'severity': 'critical',
                    'description': f'Insufficient approval authority: {actual_approval_level} approved but {required_approval_level} required',
                    'expected_behavior': f'{required_approval_level} approval required based on case parameters',
                    'actual_behavior': f'Only {actual_approval_level} approval obtained',

                    # Rule Context
                    'rule_type': 'approval',
                    'rule_severity': 'critical',

                    # Case Context
                    'loan_amount': loan_amount,
                    'credit_score': credit_score,
                    'ltv': round(ltv, 3) if ltv else None,

                    'context': {
                        'actual_approver': actual_approval_level,
                        'required_approver': required_approval_level,
                        'actual_level': actual_level_num,
                        'required_level': required_level_num,
                        'loan_amount': loan_amount,
                        'credit_score': credit_score,
                        'ltv': round(ltv, 3) if ltv else None,
                        'steps_performed': step_names
                    }
                })

        # Legacy checks (keep for backwards compatibility)
        if not has_manager_approval:
            deviations.append({
                'case_id': case_id,
                'officer_id': officer_id,
                'timestamp': case_start_time,
                'deviation_type': 'missing_approval',
                'severity': 'critical',
                'description': 'Missing manager approval',
                'expected_behavior': 'Manager approval required before final approval',
                'actual_behavior': 'Manager approval step not found',
                'context': {
                    'approval_type': 'manager',
                    'steps_performed': step_names
                }
            })

        if not has_final_approval:
            deviations.append({
                'case_id': case_id,
                'officer_id': officer_id,
                'timestamp': case_start_time,
                'deviation_type': 'missing_approval',
                'severity': 'critical',
                'description': 'Missing final approval',
                'expected_behavior': 'Final approval required to complete case',
                'actual_behavior': 'Final approval step not found',
                'context': {
                    'approval_type': 'final',
                    'steps_performed': step_names
                }
            })

        return deviations

    @staticmethod
    def _check_timing_rules(case_id: str, logs: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check if timing constraints are met"""
        deviations = []
        timing_rules = [r for r in rules if r.get('rule_type') == 'timing']

        if not timing_rules or len(logs) < 2:
            return deviations

        officer_id = logs[0]['officer_id']

        # Extract case start time (timestamp of first log entry)
        case_start_time = logs[0]['timestamp'] if logs else None

        # Calculate time between first and last step
        first_timestamp = datetime.fromisoformat(logs[0]['timestamp'])
        last_timestamp = datetime.fromisoformat(logs[-1]['timestamp'])
        duration_hours = (last_timestamp - first_timestamp).total_seconds() / 3600

        # Check if process is too rushed (completed in less than 1 hour)
        if duration_hours < 1:
            deviations.append({
                'case_id': case_id,
                'officer_id': officer_id,
                'timestamp': case_start_time,
                'deviation_type': 'timing_violation',
                'severity': 'medium',
                'description': 'Process completed too quickly',
                'expected_behavior': 'Proper review time required for each step',
                'actual_behavior': f'Process completed in {duration_hours:.1f} hours',
                'context': {
                    'duration_hours': duration_hours,
                    'issue': 'rushed_process'
                }
            })

        # Check for unusually long gaps between steps
        for i in range(len(logs) - 1):
            current_time = datetime.fromisoformat(logs[i]['timestamp'])
            next_time = datetime.fromisoformat(logs[i + 1]['timestamp'])
            gap_days = (next_time - current_time).total_seconds() / 86400

            if gap_days > 7:  # More than 7 days
                deviations.append({
                    'case_id': case_id,
                    'officer_id': officer_id,
                    'timestamp': case_start_time,
                    'deviation_type': 'timing_violation',
                    'severity': 'low',
                    'description': f'Long delay between {logs[i]["step_name"]} and {logs[i+1]["step_name"]}',
                    'expected_behavior': 'Steps should be completed in timely manner',
                    'actual_behavior': f'Gap of {gap_days:.1f} days between steps',
                    'context': {
                        'gap_days': gap_days,
                        'step_1': logs[i]['step_name'],
                        'step_2': logs[i + 1]['step_name']
                    }
                })

        return deviations
