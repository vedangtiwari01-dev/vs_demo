"""
AI-Powered Generic Rule Evaluator

This module provides a generic rule evaluation system using Claude LLM to evaluate
compliance for ANY rule type based on rule descriptions and workflow logs.

This allows the system to support 150+ banking/compliance rule types without
writing hardcoded validation logic for each type.
"""

from typing import List, Dict, Any, Optional
import json
import re
from app.services.claude.client import ClaudeClient


class AIRuleEvaluator:
    """
    Generic rule evaluator using Claude LLM.

    Evaluates compliance for ANY rule type based on rule description + workflow logs.
    No need for type-specific hardcoded logic.

    Usage:
        evaluator = AIRuleEvaluator()
        deviations = await evaluator.evaluate_rules(rules, workflow_logs, case_id)
    """

    def __init__(self):
        """Initialize the AI rule evaluator with Claude client."""
        self.claude = ClaudeClient()

    async def evaluate_rules(
        self,
        rules: List[Dict[str, Any]],
        workflow_logs: List[Dict[str, Any]],
        case_id: str
    ) -> List[Dict[str, Any]]:
        """
        Evaluate a set of rules against workflow logs using AI.

        This method sends the rules and logs to Claude AI, which evaluates
        each rule against the actual workflow to detect compliance deviations.

        IMPORTANT: This method handles NULL/missing columns gracefully:
        - Only non-NULL fields are included in the evaluation context
        - Empty/sparse logs are still processed (won't cause errors)
        - At least basic identifiers (case_id, step_name, timestamp) are recommended

        Args:
            rules: List of SOP rules to check (any type, e.g., kyc_cdd, collateral_verification)
            workflow_logs: Chronological workflow logs for a case
            case_id: Case identifier

        Returns:
            List of detected deviations with full context

        Example:
            rules = [
                {
                    'rule_type': 'kyc_cdd',
                    'rule_description': 'Customer due diligence must be completed before account opening',
                    'severity': 'critical'
                },
                {
                    'rule_type': 'collateral_verification',
                    'rule_description': 'Collateral must be verified within 5 days',
                    'severity': 'high',
                    'timing_constraint': '5 days'
                }
            ]

            logs = [
                {'step_name': 'Account Opening', 'timestamp': '2025-01-01', ...},
                {'step_name': 'KYC Verification', 'timestamp': '2025-01-02', ...}
            ]

            deviations = await evaluator.evaluate_rules(rules, logs, 'CASE-001')
        """

        # Validation: Check for empty inputs (NULL/missing data handling)
        if not rules or len(rules) == 0:
            print(f"AI Rule Evaluation: No rules provided for case {case_id}, skipping")
            return []

        if not workflow_logs or len(workflow_logs) == 0:
            print(f"AI Rule Evaluation: No workflow logs provided for case {case_id}, skipping")
            return []

        # Validation: Ensure rules have minimum required fields
        valid_rules = []
        for rule in rules:
            if rule.get('rule_type') and rule.get('rule_description'):
                valid_rules.append(rule)
            else:
                print(f"AI Rule Evaluation: Skipping invalid rule (missing type or description): {rule}")

        if len(valid_rules) == 0:
            print(f"AI Rule Evaluation: No valid rules for case {case_id} after validation")
            return []

        # Build context prompt for Claude
        prompt = self._build_evaluation_prompt(valid_rules, workflow_logs, case_id)

        # Ask Claude to evaluate compliance
        try:
            response = await self.claude.generate(
                prompt=prompt,
                system="You are a banking compliance analyst evaluating loan processing workflows against SOP rules.",
                json_mode=True,
                max_tokens=4000
            )

            # Parse deviations from response
            deviations = self._parse_deviations(response, case_id)
            return deviations

        except Exception as e:
            # Log error and return empty list (graceful degradation)
            print(f"AI Rule Evaluation Error for case {case_id}: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []

    def _format_log_entry(self, log: Dict[str, Any]) -> str:
        """
        Format a single workflow log entry with all available columns organized by category.
        Only includes non-NULL/non-empty fields.

        Args:
            log: Single workflow log entry

        Returns:
            Formatted string with all available fields
        """
        output = []

        # Category 1: Core Identifiers (always show if present)
        core_fields = {
            'case_id': 'Case ID',
            'application_id': 'Application ID',
            'customer_id': 'Customer ID',
            'step_name': 'Step',
            'action': 'Action',
            'timestamp': 'Timestamp'
        }
        for field, label in core_fields.items():
            value = log.get(field)
            if value not in (None, '', 'Unknown', 'N/A'):
                output.append(f"   **{label}:** {value}")

        # Category 2: Customer Information
        customer_fields = {
            'customer_name': 'Customer Name',
            'customer_segment': 'Customer Segment',
            'customer_risk_rating': 'Customer Risk Rating',
            'group_id': 'Group ID',
            'related_party_flag': 'Related Party',
            'pep_flag': 'Politically Exposed Person',
            'aml_risk_rating': 'AML Risk Rating',
            'kyc_status': 'KYC Status'
        }
        customer_data = []
        for field, label in customer_fields.items():
            value = log.get(field)
            if value not in (None, '', 'Unknown', 'N/A'):
                customer_data.append(f"{label}: {value}")
        if customer_data:
            output.append(f"   **Customer:** {', '.join(customer_data)}")

        # Category 3: Organizational Structure
        org_fields = {
            'branch_code': 'Branch',
            'branch_name': 'Branch Name',
            'region': 'Region',
            'officer_id': 'Officer ID',
            'officer_name': 'Officer Name',
            'officer_role': 'Officer Role'
        }
        org_data = []
        for field, label in org_fields.items():
            value = log.get(field)
            if value not in (None, '', 'Unknown', 'N/A'):
                org_data.append(f"{label}: {value}")
        if org_data:
            output.append(f"   **Organization:** {', '.join(org_data)}")

        # Category 4: Product & Financial Details
        product_fields = {
            'product_type': 'Product Type',
            'product_code': 'Product Code',
            'loan_amount': 'Loan Amount',
            'requested_amount': 'Requested Amount',
            'sanctioned_amount': 'Sanctioned Amount',
            'disbursed_amount': 'Disbursed Amount',
            'interest_rate': 'Interest Rate',
            'tenure_months': 'Tenure (months)',
            'emi_amount': 'EMI Amount'
        }
        product_data = []
        for field, label in product_fields.items():
            value = log.get(field)
            if value not in (None, '', 'Unknown', 'N/A'):
                product_data.append(f"{label}: {value}")
        if product_data:
            output.append(f"   **Product/Financial:** {', '.join(product_data)}")

        # Category 5: Workflow Status & Timing
        workflow_fields = {
            'status': 'Status',
            'previous_status': 'Previous Status',
            'queue_name': 'Queue',
            'priority': 'Priority',
            'duration_seconds': 'Duration (sec)',
            'sla_remaining_hours': 'SLA Remaining (hrs)',
            'is_breach': 'SLA Breach'
        }
        workflow_data = []
        for field, label in workflow_fields.items():
            value = log.get(field)
            if value not in (None, '', 'Unknown', 'N/A'):
                workflow_data.append(f"{label}: {value}")
        if workflow_data:
            output.append(f"   **Workflow:** {', '.join(workflow_data)}")

        # Category 6: Approval & Authorization
        approval_fields = {
            'approver_id': 'Approver ID',
            'approver_name': 'Approver Name',
            'approver_role': 'Approver Role',
            'approval_level': 'Approval Level',
            'approval_status': 'Approval Status',
            'approval_comments': 'Approval Comments',
            'delegated_by': 'Delegated By',
            'override_reason': 'Override Reason'
        }
        approval_data = []
        for field, label in approval_fields.items():
            value = log.get(field)
            if value not in (None, '', 'Unknown', 'N/A'):
                approval_data.append(f"{label}: {value}")
        if approval_data:
            output.append(f"   **Approval:** {', '.join(approval_data)}")

        # Category 7: Credit & Risk Assessment
        risk_fields = {
            'credit_score': 'Credit Score',
            'credit_score_bureau': 'Credit Bureau',
            'pd_score': 'PD Score',
            'lgd_score': 'LGD Score',
            'risk_category': 'Risk Category',
            'collateral_type': 'Collateral Type',
            'collateral_value': 'Collateral Value',
            'ltv_ratio': 'LTV Ratio'
        }
        risk_data = []
        for field, label in risk_fields.items():
            value = log.get(field)
            if value not in (None, '', 'Unknown', 'N/A'):
                risk_data.append(f"{label}: {value}")
        if risk_data:
            output.append(f"   **Credit/Risk:** {', '.join(risk_data)}")

        # Category 8: Document Management
        doc_fields = {
            'documents_uploaded': 'Docs Uploaded',
            'documents_verified': 'Docs Verified',
            'documents_pending': 'Docs Pending',
            'document_names': 'Document Names',
            'signature_status': 'Signature Status'
        }
        doc_data = []
        for field, label in doc_fields.items():
            value = log.get(field)
            if value not in (None, '', 'Unknown', 'N/A'):
                doc_data.append(f"{label}: {value}")
        if doc_data:
            output.append(f"   **Documents:** {', '.join(doc_data)}")

        # Category 9: Exceptions & Issues
        exception_fields = {
            'exception_type': 'Exception Type',
            'exception_reason': 'Exception Reason',
            'exception_raised_by': 'Raised By',
            'remediation_action': 'Remediation Action',
            'remediation_status': 'Remediation Status',
            'error_code': 'Error Code',
            'error_message': 'Error Message'
        }
        exception_data = []
        for field, label in exception_fields.items():
            value = log.get(field)
            if value not in (None, '', 'Unknown', 'N/A'):
                exception_data.append(f"{label}: {value}")
        if exception_data:
            output.append(f"   **Exceptions/Issues:** {', '.join(exception_data)}")

        # Category 10: Notes & Comments (always show if present)
        if log.get('notes'):
            output.append(f"   **Notes:** {log['notes']}")
        if log.get('officer_comments'):
            output.append(f"   **Officer Comments:** {log['officer_comments']}")
        if log.get('system_comments'):
            output.append(f"   **System Comments:** {log['system_comments']}")

        # Category 11: Additional Context (any remaining non-standard fields)
        # This catches custom fields not in the predefined categories
        all_known_fields = set(core_fields.keys()) | set(customer_fields.keys()) | \
                          set(org_fields.keys()) | set(product_fields.keys()) | \
                          set(workflow_fields.keys()) | set(approval_fields.keys()) | \
                          set(risk_fields.keys()) | set(doc_fields.keys()) | \
                          set(exception_fields.keys()) | {'notes', 'officer_comments', 'system_comments'}

        additional_fields = []
        for field, value in log.items():
            if field not in all_known_fields and value not in (None, '', 'Unknown', 'N/A'):
                additional_fields.append(f"{field}: {value}")
        if additional_fields:
            output.append(f"   **Additional Context:** {', '.join(additional_fields)}")

        # Safeguard: If completely empty log entry (all fields were NULL), return minimal info
        if len(output) == 0:
            return "   **[SPARSE LOG ENTRY - All fields NULL/empty]**"

        return '\n'.join(output)

    def _build_evaluation_prompt(
        self,
        rules: List[Dict[str, Any]],
        workflow_logs: List[Dict[str, Any]],
        case_id: str
    ) -> str:
        """
        Build prompt for Claude to evaluate rules.

        Creates a comprehensive prompt that includes:
        - All SOP rules to check
        - Complete workflow log history with ALL available columns
        - Clear instructions for deviation detection

        Args:
            rules: SOP rules
            workflow_logs: Workflow logs
            case_id: Case ID

        Returns:
            Formatted prompt string
        """

        prompt = f"""
You are evaluating loan processing workflow compliance against Standard Operating Procedure (SOP) rules.

**Case ID:** {case_id}

**SOP Rules to Check:**

"""

        # Format rules with all available metadata
        for i, rule in enumerate(rules, 1):
            prompt += f"""
{i}. **Rule Type:** {rule.get('rule_type', 'unknown')}
   **Description:** {rule.get('rule_description', 'No description')}
   **Severity:** {rule.get('severity', 'medium')}
"""
            # Add optional fields if present
            if rule.get('timing_constraint'):
                prompt += f"   **Timing:** {rule['timing_constraint']}\n"
            if rule.get('threshold_value'):
                prompt += f"   **Threshold:** {rule['threshold_value']}\n"
            if rule.get('conditional_logic'):
                prompt += f"   **Conditions:** {rule['conditional_logic']}\n"
            if rule.get('approval_authority'):
                prompt += f"   **Approval Authority:** {rule['approval_authority']}\n"
            if rule.get('required_fields'):
                prompt += f"   **Required Fields:** {', '.join(rule['required_fields'])}\n"

        prompt += f"""

**Actual Workflow Logs (Chronological Order):**

Note: Each log entry shows ALL available data fields. Missing/NULL fields are omitted.
Use ALL available contextual information when evaluating rule compliance.

"""

        # Format workflow logs chronologically with ALL available columns
        for i, log in enumerate(workflow_logs, 1):
            prompt += f"\n{i}. WORKFLOW LOG ENTRY:\n"
            prompt += self._format_log_entry(log) + "\n"

        prompt += """

**Your Task:**

For EACH rule listed above, determine if the workflow complied with it by comparing:
1. What the rule REQUIRES (the rule description and constraints)
2. What ACTUALLY happened in the workflow (the logs)

Return a JSON array of deviations found:

{
  "deviations": [
    {
      "rule_type": "the_rule_type_violated",
      "severity": "critical|high|medium|low",
      "description": "Clear description of what went wrong",
      "expected_behavior": "What should have happened per SOP",
      "actual_behavior": "What actually happened in the workflow",
      "log_step_involved": "Which workflow step(s) caused deviation",
      "officer_id": "Officer responsible (if identifiable)"
    }
  ]
}

**IMPORTANT GUIDELINES:**

1. **Only flag CLEAR violations**: Don't flag deviations unless the rule was CLEARLY violated
2. **If compliant, don't include**: If a rule was followed correctly, do not include it in the output
3. **Be specific**: Reference specific workflow steps and timestamps
4. **Consider context**: If notes explain a valid reason (e.g., system downtime), acknowledge it but still flag the deviation
5. **No deviations = empty array**: If no deviations found, return {"deviations": []}
6. **Match severity**: Use the same severity level as the rule (or escalate if violation is more serious)

**Examples:**

Good deviation entry:
{
  "rule_type": "kyc_cdd",
  "severity": "critical",
  "description": "Customer due diligence was not completed before account opening",
  "expected_behavior": "KYC/CDD verification must be completed before account opening step",
  "actual_behavior": "Account was opened at 2025-01-01 10:00, but KYC verification only happened at 2025-01-02 14:00 (28 hours later)",
  "log_step_involved": "Step 1 (Account Opening) and Step 3 (KYC Verification)",
  "officer_id": "OFF001"
}

Return ONLY the JSON, no other text.
"""

        return prompt

    def _parse_deviations(
        self,
        response: str,
        case_id: str
    ) -> List[Dict[str, Any]]:
        """
        Parse Claude's response into deviation objects.

        Handles both clean JSON and JSON embedded in markdown code fences.

        Args:
            response: Claude's response text
            case_id: Case ID to add to each deviation

        Returns:
            List of deviation dictionaries
        """

        try:
            # Try parsing as direct JSON first
            data = json.loads(response)
            deviations = data.get('deviations', [])

            # Add metadata to each deviation
            for dev in deviations:
                dev['case_id'] = case_id
                dev['detection_method'] = 'ai_evaluator'

                # Ensure required fields exist
                if 'rule_type' not in dev:
                    dev['rule_type'] = 'unknown'
                if 'severity' not in dev:
                    dev['severity'] = 'medium'
                if 'description' not in dev:
                    dev['description'] = 'Compliance deviation detected'

            return deviations

        except json.JSONDecodeError:
            # Fallback: try to extract JSON from markdown code fence
            # Pattern: ```json\n{...}\n```
            json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    deviations = data.get('deviations', [])

                    # Add metadata
                    for dev in deviations:
                        dev['case_id'] = case_id
                        dev['detection_method'] = 'ai_evaluator'

                        # Ensure required fields
                        if 'rule_type' not in dev:
                            dev['rule_type'] = 'unknown'
                        if 'severity' not in dev:
                            dev['severity'] = 'medium'
                        if 'description' not in dev:
                            dev['description'] = 'Compliance deviation detected'

                    return deviations
                except json.JSONDecodeError:
                    pass

            # Could not parse - log and return empty
            print(f"Failed to parse AI response for case {case_id}: {response[:200]}")
            return []

    async def evaluate_rules_batch(
        self,
        rules: List[Dict[str, Any]],
        cases: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Evaluate rules for multiple cases in batch.

        More efficient than calling evaluate_rules() for each case individually,
        as it can batch API calls.

        Args:
            rules: List of SOP rules
            cases: Dict mapping case_id -> list of workflow logs
                   Example: {'CASE-001': [...logs...], 'CASE-002': [...logs...]}

        Returns:
            Dict mapping case_id -> list of deviations
            Example: {'CASE-001': [...deviations...], 'CASE-002': [...deviations...]}
        """

        results = {}

        # Evaluate each case
        # TODO: Optimize with parallel evaluation in future
        for case_id, logs in cases.items():
            deviations = await self.evaluate_rules(rules, logs, case_id)
            results[case_id] = deviations

        return results


# ==================================================================
# HELPER FUNCTIONS
# ==================================================================

async def evaluate_extended_rules(
    rules: List[Dict[str, Any]],
    workflow_logs: List[Dict[str, Any]],
    case_id: str
) -> List[Dict[str, Any]]:
    """
    Convenience function for evaluating extended (non-core) rules.

    This filters out core rules (sequence, approval, timing, validation)
    and only evaluates extended rules using AI.

    Args:
        rules: All SOP rules
        workflow_logs: Workflow logs
        case_id: Case ID

    Returns:
        Deviations for extended rules only
    """

    # Core rule types (handled by hardcoded logic)
    CORE_TYPES = {'sequence', 'approval', 'timing', 'validation'}

    # Filter to extended rules only
    extended_rules = [r for r in rules if r.get('rule_type') not in CORE_TYPES]

    if not extended_rules:
        return []

    # Evaluate with AI
    evaluator = AIRuleEvaluator()
    return await evaluator.evaluate_rules(extended_rules, workflow_logs, case_id)
