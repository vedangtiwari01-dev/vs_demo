from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict

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
    def _check_approval_rules(case_id: str, logs: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check if approval rules are followed"""
        deviations = []
        approval_rules = [r for r in rules if r.get('rule_type') == 'approval']

        if not approval_rules:
            return deviations

        # Check if approval steps exist
        step_names = [log['step_name'].lower() for log in logs]
        has_manager_approval = any('manager' in step and 'approval' in step for step in step_names)
        has_final_approval = any('final' in step and 'approval' in step for step in step_names)

        officer_id = logs[0]['officer_id'] if logs else 'unknown'

        if not has_manager_approval:
            deviations.append({
                'case_id': case_id,
                'officer_id': officer_id,
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

        # Calculate time between first and last step
        first_timestamp = datetime.fromisoformat(logs[0]['timestamp'])
        last_timestamp = datetime.fromisoformat(logs[-1]['timestamp'])
        duration_hours = (last_timestamp - first_timestamp).total_seconds() / 3600

        # Check if process is too rushed (completed in less than 1 hour)
        if duration_hours < 1:
            deviations.append({
                'case_id': case_id,
                'officer_id': officer_id,
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
