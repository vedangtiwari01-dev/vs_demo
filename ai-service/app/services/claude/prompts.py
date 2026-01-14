"""
Centralized prompt templates for Claude API interactions.
"""
from typing import Dict, Any, List, Optional

# SOP Rule Extraction Prompt
SOP_RULE_EXTRACTION_PROMPT = """You are an expert at analyzing Standard Operating Procedures (SOPs) for loan processing and extracting compliance rules.

Analyze the following SOP document text and extract ALL compliance rules. For each rule, identify:

1. **Rule Type**: One of:
   - "sequence": Steps that must happen in a specific order
   - "approval": Requirements for manager/authority approval and escalation
   - "timing": Time constraints, SLAs, TATs, cut-off times
   - "eligibility": Age, tenure, income, employment, geography, product qualifications
   - "credit_risk": Bureau score, delinquency, EMI/DTI ratios, LTV, exposure limits
   - "kyc": KYC verification, documentation, refresh cycles
   - "aml": Sanctions/watchlist screening, PEP handling, enhanced due diligence
   - "documentation": Required document packs, authenticity, expiry, retention
   - "collateral": Valuation, security creation/perfection, margin, LTV caps (for secured loans)
   - "disbursement": Pre-disbursement conditions, disbursement modes, stage releases
   - "post_disbursement_qc": Post-disbursement quality checks and audit requirements
   - "collection": DPD-based escalation, repossession triggers
   - "restructuring": Restructuring and write-off approval requirements
   - "regulatory": NPA classification, provisioning, regulatory reporting requirements
   - "data_quality": Logging, audit trails, data completeness, consistency, reconciliation
   - "operational": Manual override rules, error handling, segregation of duties

2. **Rule Description**: Clear, concise description of the rule

3. **Step Number**: The step number in the process (if mentioned)
   - **CRITICAL FOR SEQUENCE RULES**: ALWAYS extract step numbers for sequence rules
   - If rule mentions "Step 13 and Step 14 before Step 16", create SEPARATE rules:
     * Rule 1: step_number: 13, rule_description: "Legal Security Creation must be completed before Loan Disbursement"
     * Rule 2: step_number: 14, rule_description: "EMI Mandate Setup must be completed before Loan Disbursement"
     * Rule 3: step_number: 16, rule_description: "Loan Disbursement (depends on steps 13, 14)"
   - Do NOT create one rule with the full compound text as rule_description
   - Each step in a sequence should have its own rule entry with proper step_number

4. **Severity**: Based on the language used:
   - "critical": Uses "must", "shall", "required", regulatory/legal requirements
   - "high": Uses "should", affects compliance or risk
   - "medium": Uses "recommended", "advised", affects process quality
   - "low": Uses "may", "optional", best practices

5. **Required Fields**: ANY data fields mentioned that must be present (e.g., income_verification, credit_score, loan_amount, collateral_value, emi_amount, product_type, customer_segment, etc.)

6. **Timing Constraint**: If it's a timing rule, extract the specific time requirement (e.g., "48 hours", "3 days", "immediately", "within 12 months")

7. **Condition Logic**: For conditional rules (IF-THEN logic), extract in structured JSON format:

   **Simple condition:**
   {{
     "condition": {{"field": "loan_amount_sanctioned", "operator": ">=", "value": 10000}},
     "then": {{"require_step": "Manager Approval", "severity": "critical"}}
   }}

   **With calculation (NEW - for LTV, EMI, etc.):**
   {{
     "condition": {{
       "calculation": {{"function": "DIVIDE", "args": [{{"field": "loan_amount"}}, {{"field": "collateral_value"}}]}},
       "operator": ">",
       "value": 0.8
     }},
     "then": {{"action": "flag_violation", "deviation_type": "ltv_breach", "severity": "high"}}
   }}

   **Complex AND/OR:**
   {{
     "condition": {{
       "operator": "AND",
       "conditions": [
         {{"field": "credit_score_bureau", "operator": "<", "value": 600}},
         {{"field": "loan_amount_sanctioned", "operator": ">", "value": 5000}}
       ]
     }},
     "then": {{"require_step": "Risk Head Approval", "severity": "high"}}
   }}

   **Supported operators:** ==, !=, <, >, <=, >=, IN, NOT_IN, AND, OR, NOT
   **Calculation functions:** DIVIDE, MULTIPLY, ADD, SUBTRACT, PERCENT, EMI, MAX, MIN, SUM

8. **Product Types** (NEW): List of product types this rule applies to (e.g., ["Home Loan"], ["Gold Loan", "Personal Loan"], or ["All"] if applies to all products)

9. **Customer Segments** (NEW): List of customer segments (e.g., ["Priority"], ["Retail"], ["All"])

10. **Channels** (NEW): List of channels (e.g., ["Branch"], ["Digital"], ["All"])

11. **Geography** (NEW): Geographic applicability (e.g., ["Urban"], ["Rural"], ["All"])

12. **Exceptions** (NEW): Any exception cases mentioned (e.g., [{{"condition": "customer_segment == Priority", "override": "EMI ratio can be 60%"}}])

13. **Calculation Formula** (NEW): For rules involving calculations, extract the formula as a string (e.g., "EMI = P * r * (1+r)^n / ((1+r)^n - 1)", "LTV = loan_amount / collateral_value")

14. **Temporal Constraint** (NEW): For step-to-step timing rules:
   {{
     "step_a": "Risk Assessment",
     "step_b": "Manager Approval",
     "max_hours": 48,
     "business_days_only": true
   }}

15. **Threshold Value** (NEW): Numeric threshold if rule involves a limit (e.g., 10000 for "$10,000+", 0.5 for "50%", 0.8 for "80%")

16. **Field Dependencies** (NEW): List of ALL fields this rule depends on (e.g., ["loan_amount", "collateral_value"] for LTV rule, ["emi_to_income_ratio", "customer_segment"] for EMI rule)

17. **Regulatory Reference** (NEW): Any legal/regulatory reference mentioned (e.g., "RBI Master Circular", "Basel III Norms", "Section 17(2)")

SOP Document Text:
{sop_text}

Return your analysis as a JSON array with this EXACT structure:

{{{{
  "rules": [
    {{{{
      "rule_type": "approval",
      "rule_description": "Loans $10,000 or more require manager approval",
      "step_number": 5,
      "severity": "critical",
      "required_fields": ["loan_amount_sanctioned", "approver_id"],
      "timing_constraint": null,
      "condition_logic": {{{{
        "condition": {{"field": "loan_amount_sanctioned", "operator": ">=", "value": 10000}},
        "then": {{"require_step": "Manager Approval", "severity": "critical"}}
      }}}},
      "product_types": ["All"],
      "customer_segments": ["All"],
      "channels": ["All"],
      "geography": ["All"],
      "exceptions": [],
      "calculation_formula": null,
      "temporal_constraint": null,
      "threshold_value": 10000,
      "field_dependencies": ["loan_amount_sanctioned"],
      "regulatory_reference": null
    }}}}
  ]
}}}}

CRITICAL INSTRUCTIONS:
- Extract EVERY field mentioned, even if optional
- For conditional rules, ALWAYS populate condition_logic
- For timing rules, ALWAYS populate temporal_constraint
- For calculation rules, ALWAYS populate calculation_formula
- ALWAYS list ALL fields the rule depends on in field_dependencies
- If a field is not applicable, use null (not empty string)
- If a list field applies to everything, use ["All"]
- Be thorough - extract every rule you can find
- Use exact field names as they appear in the document

EXAMPLE EXTRACTIONS:

0. "Legal Security Creation (Step 13) and EMI Mandate Setup (Step 14) shall be completed before Loan Disbursement (Step 16)" →
   **Create 3 SEPARATE rules:**
   {{
     "rule_type": "sequence",
     "rule_description": "Legal Security Creation must be completed before Loan Disbursement",
     "step_number": 13,
     "severity": "critical",
     "required_fields": ["step_name", "timestamp"],
     "temporal_constraint": {{"step_a": "Legal Security Creation", "step_b": "Loan Disbursement", "max_hours": null}},
     "field_dependencies": ["step_name"]
   }},
   {{
     "rule_type": "sequence",
     "rule_description": "EMI Mandate Setup must be completed before Loan Disbursement",
     "step_number": 14,
     "severity": "critical",
     "required_fields": ["step_name", "timestamp"],
     "temporal_constraint": {{"step_a": "EMI Mandate Setup", "step_b": "Loan Disbursement", "max_hours": null}},
     "field_dependencies": ["step_name"]
   }},
   {{
     "rule_type": "sequence",
     "rule_description": "Loan Disbursement (depends on Legal Security Creation and EMI Mandate Setup)",
     "step_number": 16,
     "severity": "critical",
     "required_fields": ["step_name", "timestamp"],
     "field_dependencies": ["step_name"]
   }}

1. "Loans of $10,000 or more require manager approval" →
   condition_logic: {{"condition": {{"field": "loan_amount_sanctioned", "operator": ">=", "value": 10000}}, "then": {{"require_step": "Manager Approval"}}}}
   threshold_value: 10000
   field_dependencies: ["loan_amount_sanctioned"]

2. "LTV must not exceed 80%" →
   condition_logic: {{"condition": {{"calculation": {{"function": "DIVIDE", "args": [{{"field": "loan_amount"}}, {{"field": "collateral_value"}}]}}, "operator": ">", "value": 0.8}}, "then": {{"action": "flag_violation"}}}}
   calculation_formula: "LTV = loan_amount / collateral_value"
   threshold_value: 0.8
   field_dependencies: ["loan_amount", "collateral_value"]

3. "Manager Approval must be completed within 48 hours of Risk Assessment" →
   temporal_constraint: {{"step_a": "Risk Assessment", "step_b": "Manager Approval", "max_hours": 48}}
   timing_constraint: "48 hours"
   field_dependencies: ["step_name", "timestamp"]

4. "Home loans require property valuation" →
   condition_logic: {{"condition": {{"field": "product_type", "operator": "==", "value": "Home Loan"}}, "then": {{"require_step": "Property Valuation"}}}}
   product_types: ["Home Loan"]
   field_dependencies: ["product_type"]

5. "Priority customers can have EMI ratio up to 60% (normal customers: 50%)" →
   condition_logic: {{"condition": {{"operator": "AND", "conditions": [{{"field": "emi_to_income_ratio", "operator": ">", "value": 0.6}}, {{"field": "customer_segment", "operator": "!=", "value": "Priority"}}]}}, "then": {{"action": "flag_violation"}}}}
   customer_segments: ["All"]
   exceptions: [{{"condition": "customer_segment == Priority", "override": "EMI ratio can be 60%"}}]
   threshold_value: 0.5
   field_dependencies: ["emi_to_income_ratio", "customer_segment"]

6. "Loans with LTV exceeding 80% require Credit Committee approval" →
   condition_logic: {{
     "condition": {{
       "calculation": {{"function": "DIVIDE", "args": [{{"field": "loan_amount_sanctioned"}}, {{"field": "collateral_value"}}]}},
       "operator": ">",
       "value": 0.8
     }},
     "then": {{"require_step": "Credit Approval (Level 3 - Credit Committee)", "severity": "critical"}}
   }}
   calculation_formula: "LTV = loan_amount_sanctioned / collateral_value"
   threshold_value: 0.8
   field_dependencies: ["loan_amount_sanctioned", "collateral_value"]

7. "Credit scores between 650-699 require Regional Credit Manager approval" →
   condition_logic: {{
     "condition": {{
       "operator": "AND",
       "conditions": [
         {{"field": "credit_score_bureau", "operator": ">=", "value": 650}},
         {{"field": "credit_score_bureau", "operator": "<=", "value": 699}}
       ]
     }},
     "then": {{"require_step": "Credit Approval (Level 2 - Regional Credit Manager)", "severity": "critical"}}
   }}
   threshold_value: 650
   field_dependencies: ["credit_score_bureau"]

8. "EMI Mandate must be Active before Loan Disbursement" →
   condition_logic: {{
     "condition": {{"field": "mandate_status", "operator": "!=", "value": "Active"}},
     "then": {{"action": "block_step", "blocked_step": "Loan Disbursement", "severity": "critical"}}
   }}
   rule_type: "disbursement"
   severity: "critical"
   field_dependencies: ["mandate_status", "step_name"]

IMPORTANT:
- Use "rule_type" NOT "type"
- Use "rule_description" NOT "description"
- Use "condition_logic" NOT "conditional_logic"
- Be thorough - extract every rule you can find, even if they seem minor
- ALWAYS fill in the new fields (product_types, customer_segments, etc.) even if ["All"]"""

# Column Mapping Prompt
COLUMN_MAPPING_PROMPT = """You are an expert at analyzing CSV column headers and mapping them to standardized system fields for loan processing workflow data.

I have a CSV file with the following columns:
{headers}

Sample data from first 3 rows:
{sample_rows}

**Required System Fields (MUST be present):**
- case_id: Unique identifier for the loan/case (aliases: application_id, loan_id)
- officer_id: ID of the officer/user handling the case
- step_name: Name of the workflow step/activity
- action: Action taken (e.g., approved, rejected, completed)
- timestamp: Date/time when the step occurred

**Optional System Fields (improve analysis when present):**
Core Workflow: duration_seconds, status, notes, comments, step_id, stage_name, workflow_version, action_type, sub_status
Entity IDs: application_id, loan_id, customer_id, customer_name, customer_segment, customer_type, customer_risk_rating, group_id, related_party_flag, staff_flag, portfolio_id
Product & Channel: product_type, sub_product_type, scheme_code, secured_unsecured_flag, channel, branch_code, branch_name, region, geo_code
Amounts & Terms: loan_amount_requested, loan_amount_sanctioned, loan_amount_disbursed, interest_rate, interest_type, processing_fee, other_charges, tenor_months, tenor_days, repayment_frequency, emi_amount, ltv_ratio, margin_pct, total_group_exposure, customer_total_exposure
Risk & Credit: credit_score_bureau, credit_score_internal, scorecard_version, score_band, emi_to_income_ratio, dti_ratio, risk_grade, risk_category
Collateral: collateral_type, collateral_description, collateral_value, collateral_value_date, valuation_status, valuation_firm_id, security_created_flag, security_perfected_flag
KYC/AML: kyc_status, kyc_completed_flag, kyc_date, kyc_mode, sanctions_hit_flag, watchlist_hit_flag, pep_flag, aml_risk_rating
Workflow Detail: officer_name, officer_role, approval_role, approval_level, timestamp_start, timestamp_end, step_time, business_date, queue_name, queue_priority, sla_target_timestamp, sla_breach_flag
Approvals & Exceptions: approver_id, approver_role, approval_decision, approval_timestamp, exception_flag, exception_reason, exception_approver_id, override_flag, override_reason, override_approver_id
Disbursement: disbursement_date, disbursement_amount, disbursement_mode, mandate_status, first_emi_date, statement_generated_flag, post_disbursement_qc_flag, post_disbursement_qc_date, qc_findings
Collections & Restructuring: overdue_days, bucket, collection_status, collection_agent_id, restructure_flag, restructure_date, restructure_type, writeoff_flag, writeoff_amount, writeoff_date
Audit & Data Quality: created_by, created_at, updated_by, updated_at, source_system, source_file_name, import_batch_id, audit_trail_id, log_level, error_code, error_message

**Your Task:**
1. Map each CSV column to the most appropriate system field (use simple string values ONLY)
2. Identify which column (if any) contains notes/comments
3. Flag any columns that don't map to system fields

**Important:**
- Use semantic meaning, not just exact name matches
- "Loan_ID" could map to "case_id"
- "User" or "Employee" could map to "officer_id"
- "Activity" or "Task" could map to "step_name"
- "Decision" could map to either "action" or "status"
- Notes columns might be named: "Notes", "Comments", "Remarks", "Explanation", "Justification"

**CRITICAL - Return Format:**
Return ONLY this exact JSON structure (simple string mappings, NO nested objects, NO confidence scores, NO reasoning):
{{
  "mappings": {{
    "CSV_Column_Name": "system_field_name"
  }},
  "notes_column": "Name of column containing notes/comments, or null",
  "unmapped_columns": ["columns", "that", "dont", "map"],
  "warnings": ["Any concerns or ambiguities to flag for the user"]
}}

Example of correct format:
{{
  "mappings": {{
    "Loan_ID": "case_id",
    "User": "officer_id",
    "Activity": "step_name",
    "Decision": "action",
    "Timestamp": "timestamp",
    "Notes": "notes"
  }},
  "notes_column": "Notes",
  "unmapped_columns": ["Loan_Amount", "Credit_Score"],
  "warnings": []
}}

DO NOT include nested objects. Each mapping value MUST be a simple string."""

# Deviation Analysis Prompt
DEVIATION_ANALYSIS_PROMPT = """You are an expert compliance analyst for loan processing workflows. Your job is to analyze workflow logs against SOP rules and identify deviations.

**SOP Rules:**
{rules}

**Workflow Logs (chronological by case):**
{logs}

**Notes/Comments (context for understanding deviations):**
{notes}

**Your Task:**
Analyze each case's workflow and identify ALL deviations from the SOP rules. For each deviation:

1. **Deviation Type**: Choose the most specific type:

   **Process & Sequence:**
   - "missing_step": Required step was skipped
   - "wrong_sequence": Steps done in wrong order
   - "unexpected_step": Step not allowed for product/segment
   - "duplicate_step": Repeated steps where only one allowed
   - "skipped_mandatory_subprocess": No pre-sanction visit/legal opinion when required

   **Approval & Authority:**
   - "missing_approval": No approval at required role/level
   - "insufficient_approval_hierarchy": Amount/risk requires more approvers
   - "unauthorized_approver": Approver role/limit insufficient
   - "self_approval_violation": Same officer originates and approves
   - "escalation_missing": Mandatory escalation not done for high-risk cases

   **Timing & SLA:**
   - "timing_violation": Time constraint not met (too fast/slow between steps)
   - "tat_breach": SLA/TAT from application to decision exceeded
   - "cutoff_breach": Step processed after cut-off or on holiday
   - "post_disbursement_qc_delay": QC done outside allowed window

   **Eligibility & Credit Policy:**
   - "ineligible_age": Age outside product limits
   - "ineligible_tenor": Tenure not allowed for product
   - "emi_to_income_breach": EMI or DTI above threshold
   - "low_score_approved_without_exception": Approved despite low score, no exception

   **KYC / AML / Sanctions:**
   - "kyc_incomplete_progression": Advanced beyond allowed stage with incomplete KYC
   - "sanctions_hit_not_rejected": Sanctions/watchlist hit but not declined
   - "pep_no_edd_or_extra_approval": PEP case missing enhanced due diligence

   **Documentation & Legal:**
   - "missing_mandatory_document": Required documents absent at gate
   - "expired_document_used": Document expiry before decision/disbursement
   - "legal_clearance_missing": No legal opinion where required
   - "collateral_docs_incomplete": Security docs incomplete before disbursement

   **Collateral & Security:**
   - "ltv_breach": LTV above policy limit
   - "valuation_missing_or_stale": No valuation or valuation too old
   - "security_not_created": Disbursed without recording security

   **Disbursement & Post-Disbursement:**
   - "pre_disbursement_condition_unmet": Disbursed without satisfying conditions
   - "mandate_not_set_before_disbursement": No repayment mandate at disbursement
   - "incorrect_disbursement_amount": Disbursed not equal to sanctioned
   - "post_disbursement_qc_missing": QC not done for required cases

   **Collections & Restructuring:**
   - "collection_escalation_delay": DPD bucket escalated late
   - "unauthorized_restructure": Restructure with missing/inadequate approval
   - "unauthorized_writeoff": Write-off beyond delegated authority

   **Regulatory & Reporting:**
   - "classification_mismatch": Internal vs regulatory classification inconsistent
   - "provisioning_shortfall": Provision less than required for bucket
   - "regulatory_report_missing_or_late": Mandatory report not filed in time

   **Data Quality & Logging:**
   - "missing_core_field": Missing case_id/officer_id/step_name/action/timestamp
   - "invalid_format": Wrong data type or invalid pattern
   - "inconsistent_value_across_steps": Loan amount/branch/product changes without amendment
   - "duplicate_active_case": More than one active case per customer/product
   - "audit_trail_missing": Required log record not present

2. **Severity**: Based on impact and SOP rule severity:
   - "critical": Major compliance breach, regulatory risk
   - "high": Significant process violation
   - "medium": Minor violation, process quality issue
   - "low": Best practice not followed

3. **Description**: Clear explanation of what went wrong

4. **Expected Behavior**: What should have happened per SOP

5. **Actual Behavior**: What actually happened

6. **Justification Assessment**: If notes/comments exist:
   - Assess whether they provide valid justification
   - Consider if deviation was reasonable given circumstances
   - Adjust severity if justified (e.g., emergency situation)

7. **Reasoning**: Your analysis and reasoning for flagging this as a deviation

**Important Considerations:**
- Cross-reference notes/comments to understand WHY deviations occurred
- Some deviations may be justified (system downtime, emergency, etc.)
- If notes explain a valid reason, mention it but still flag the deviation
- Be thorough but reasonable - don't flag minor timing differences (< 1 hour) as critical

Return your analysis as JSON:
{{
  "deviations": [
    {{
      "case_id": "12345",
      "officer_id": "OFF001",
      "deviation_type": "Use one of the comprehensive deviation types listed above",
      "severity": "critical|high|medium|low",
      "rule_id": 123,
      "description": "Clear description of deviation",
      "expected_behavior": "What SOP required",
      "actual_behavior": "What actually happened",
      "justification_found": true/false,
      "justification_text": "Text from notes if applicable",
      "reasoning": "Your detailed analysis",
      "context": {{
        "additional": "context"
      }}
    }}
  ],
  "summary": {{
    "total_cases_analyzed": 50,
    "cases_with_deviations": 15,
    "total_deviations": 23,
    "deviation_by_severity": {{
      "critical": 2,
      "high": 8,
      "medium": 10,
      "low": 3
    }}
  }}
}}"""

# Batch deviation analysis for large datasets
BATCH_DEVIATION_ANALYSIS_PROMPT = """You are analyzing a batch of loan processing workflow logs for compliance deviations.

**SOP Rules:**
{rules}

**Case ID:** {case_id}

**Workflow Steps for this case (chronological):**
{case_logs}

**Notes for this case:**
{case_notes}

Analyze this single case and identify ALL deviations. Return JSON with the same structure as the main deviation analysis, but for this one case only."""

def format_sop_extraction_prompt(sop_text: str) -> str:
    """Format the SOP rule extraction prompt with actual SOP text."""
    return SOP_RULE_EXTRACTION_PROMPT.format(sop_text=sop_text)

def format_column_mapping_prompt(headers: list, sample_rows: list) -> str:
    """Format the column mapping prompt with CSV headers and sample data."""
    headers_str = ", ".join([f'"{h}"' for h in headers])
    sample_str = "\n".join([f"Row {i+1}: {row}" for i, row in enumerate(sample_rows[:3])])
    return COLUMN_MAPPING_PROMPT.format(headers=headers_str, sample_rows=sample_str)

def format_deviation_analysis_prompt(rules: list, logs: list, notes: dict = None) -> str:
    """Format the deviation analysis prompt with rules, logs, and notes."""
    # Format rules
    rules_str = "\n".join([
        f"{i+1}. [{r.get('rule_type', 'N/A')}] {r.get('rule_description', 'N/A')} (Severity: {r.get('severity', 'medium')})"
        for i, r in enumerate(rules)
    ])

    # Format logs
    logs_str = "\n".join([
        f"Case {log.get('case_id')}, Officer {log.get('officer_id')}, Step: {log.get('step_name')}, "
        f"Action: {log.get('action')}, Time: {log.get('timestamp')}, Status: {log.get('status', 'N/A')}"
        for log in logs
    ])

    # Format notes
    notes_str = "No notes available"
    if notes:
        notes_str = "\n".join([
            f"Case {case_id}: {note_text}"
            for case_id, note_text in notes.items()
        ])

    return DEVIATION_ANALYSIS_PROMPT.format(
        rules=rules_str,
        logs=logs_str,
        notes=notes_str
    )

def format_batch_deviation_prompt(rules: list, case_id: str, case_logs: list, case_notes: str = None) -> str:
    """Format the batch deviation analysis prompt for a single case."""
    # Format rules
    rules_str = "\n".join([
        f"{i+1}. [{r.get('rule_type', 'N/A')}] {r.get('rule_description', 'N/A')} (Severity: {r.get('severity', 'medium')})"
        for i, r in enumerate(rules)
    ])

    # Format case logs
    logs_str = "\n".join([
        f"{i+1}. Step: {log.get('step_name')}, Action: {log.get('action')}, "
        f"Time: {log.get('timestamp')}, Status: {log.get('status', 'N/A')}"
        for i, log in enumerate(case_logs)
    ])

    # Format notes
    notes_str = case_notes or "No notes available for this case"

    return BATCH_DEVIATION_ANALYSIS_PROMPT.format(
        rules=rules_str,
        case_id=case_id,
        case_logs=logs_str,
        case_notes=notes_str
    )

# Notes Analysis Prompt (for detected deviations only)
NOTES_ANALYSIS_PROMPT = """You are a compliance analyst examining why deviations occurred in loan processing workflows.

A deviation has been detected by our rule-based system. Your job is to analyze the notes/comments associated with this deviation to understand:
1. WHY did this deviation occur?
2. Was it justified given the circumstances?
3. Does it represent a compliance risk or a reasonable exception?

**Deviation Details:**
- Case ID: {case_id}
- Officer ID: {officer_id}
- Deviation Type: {deviation_type}
- Severity: {severity}
- Description: {description}
- Expected Behavior: {expected_behavior}
- Actual Behavior: {actual_behavior}

**Notes/Comments:**
{notes}

**Your Task:**
Analyze the notes and provide:

1. **Reason for Deviation**: Extract and summarize WHY this deviation occurred based on the notes
2. **Justification Assessment**:
   - "justified": Valid reason, reasonable exception (e.g., system downtime, emergency)
   - "partially_justified": Some valid reasoning but still concerning
   - "not_justified": No valid reason provided or weak excuse
   - "unclear": Notes don't clearly explain the deviation
3. **Risk Level**: Based on the notes, assess the risk:
   - "low": Well-documented exception, no compliance concern
   - "medium": Some concern, needs monitoring
   - "high": Significant compliance risk despite notes
   - "critical": Major violation, notes don't justify the action
4. **Key Insights**: Important points extracted from the notes
5. **Recommended Action**: What should be done about this deviation

Return your analysis as JSON:
{{
  "reason_summary": "Clear summary of why deviation occurred",
  "justification": "justified|partially_justified|not_justified|unclear",
  "risk_level": "low|medium|high|critical",
  "key_insights": ["insight 1", "insight 2"],
  "recommended_action": "What should be done",
  "severity_adjustment": "increase|maintain|decrease",
  "severity_reasoning": "Why severity should be adjusted or maintained"
}}

Be objective - if notes provide valid justification, acknowledge it. If they don't, flag it."""

def format_notes_analysis_prompt(deviation: Dict[str, Any], notes: str) -> str:
    """Format the notes analysis prompt for a specific deviation."""
    return NOTES_ANALYSIS_PROMPT.format(
        case_id=deviation.get('case_id', 'N/A'),
        officer_id=deviation.get('officer_id', 'N/A'),
        deviation_type=deviation.get('deviation_type', 'N/A'),
        severity=deviation.get('severity', 'N/A'),
        description=deviation.get('description', 'N/A'),
        expected_behavior=deviation.get('expected_behavior', 'N/A'),
        actual_behavior=deviation.get('actual_behavior', 'N/A'),
        notes=notes or "No notes provided"
    )

# Batch Pattern Analysis Prompt (analyze ALL deviations together for trends)
BATCH_PATTERN_ANALYSIS_PROMPT = """You are an expert compliance analyst examining patterns, trends, and hidden rules in loan processing deviations.

You have been given {deviation_count} deviations that were detected by rule-based logic. Some deviations have notes/comments, others don't.

**Your Task:**
Find PATTERNS, TRENDS, HABITS, and HIDDEN RULES across the entire dataset by analyzing:
1. **Structured Data Patterns** (ALWAYS analyze these):
   - Officer IDs: Which officers have most deviations?
   - Case IDs: Distribution across cases
   - Deviation Types: Most common violations
   - Severity: Distribution of critical vs. low severity
   - Timestamps: Time-based patterns (if available)
   - Descriptions: Common themes in violation descriptions

2. **Contextual Patterns** (when notes are available):
   - Notes/comments explaining WHY deviations occurred
   - Justifications provided by officers
   - Systemic issues mentioned

**IMPORTANT:** You MUST find patterns even when notes are not available. Focus on the structured data (officer IDs, types, severity, descriptions).

**Deviations with Notes:**
{deviations_with_notes}

**Questions to Answer:**
1. **Behavioral Patterns**: Do certain officers consistently deviate in specific ways?
2. **Workload Patterns**: Are deviations more common when workload is high?
3. **Time-Based Patterns**: Do deviations spike during certain times (month-end, quarter-end)?
4. **Hidden Rules**: What informal practices or "shortcuts" do officers follow?
   - Example: "Skip Step X when customer is VIP"
   - Example: "Fast-track approval if senior manager verbally approved"
5. **Systemic Issues**: Are there recurring technical or process issues mentioned in notes?
   - Example: "System downtime causes step skipping"
   - Example: "Missing data forces workarounds"
6. **Justification Clusters**: What are the most common reasons given for deviations?
7. **Risk Indicators**: What patterns suggest higher compliance risk?

**Output Format:**
Return your analysis as JSON:
{{
  "overall_summary": "High-level summary of deviation patterns",
  "behavioral_patterns": [
    {{
      "pattern": "Officers X, Y, Z consistently skip income verification when workload > 20 cases/day",
      "frequency": "High (60% of cases)",
      "risk_level": "high",
      "officers_involved": ["OFF001", "OFF002"],
      "supporting_evidence": "Notes mention 'too busy', 'backlog', 'time pressure'"
    }}
  ],
  "hidden_rules": [
    {{
      "rule": "VIP customers get expedited processing by skipping credit check",
      "confidence": "high",
      "evidence": "10 cases mention 'VIP', 'priority client', 'relationship customer'",
      "compliance_impact": "Critical - violates SOP requirement for universal credit checks"
    }}
  ],
  "systemic_issues": [
    {{
      "issue": "System downtime during 2-4 PM causes batch processing delays",
      "frequency": "15 occurrences",
      "impact": "Officers skip steps and batch process later",
      "recommended_fix": "Improve system reliability or adjust SOP for downtime procedures"
    }}
  ],
  "time_patterns": [
    {{
      "pattern": "Deviation rate increases 3x during month-end (25th-31st)",
      "reason": "Officers rush to meet monthly targets",
      "recommendation": "Consider staggered targets or additional QA during month-end"
    }}
  ],
  "justification_analysis": {{
    "most_common_reasons": [
      {{"reason": "Time pressure / workload", "count": 22}},
      {{"reason": "System issues", "count": 12}},
      {{"reason": "Customer urgency", "count": 8}}
    ],
    "justified_count": 15,
    "not_justified_count": 28,
    "unclear_count": 7
  }},
  "risk_insights": [
    "Officers under high workload consistently bypass critical controls",
    "Informal VIP fast-track practice creates compliance blind spot",
    "Month-end pressure leads to 70% of critical deviations"
  ],
  "recommendations": [
    "Implement workload monitoring and redistribution",
    "Formalize VIP handling procedures with proper controls",
    "Add automated reminders during high-risk periods"
  ]
}}

CRITICAL JSON FORMATTING RULES - READ CAREFULLY:
1. "recommendations" MUST be an array of simple strings ONLY - NO objects with fields
2. Each recommendation is just a plain string - do NOT add "priority", "timeline", "impact" fields
3. Keep recommendations concise (1-2 sentences each)
4. Do NOT add trailing commas before closing brackets ] or braces }}
5. If you want to show priority, include it IN the string: "[HIGH] Do this immediately"
6. Do NOT create objects inside the recommendations array
7. WRONG: {{"recommendation": "text", "timeline": "2 months"}}
8. CORRECT: "Do this within 2 months"
9. CRITICAL: Ensure ALL commas are present between array/object elements
10. CRITICAL: Do NOT include any text, explanations, or comments outside the JSON object
11. CRITICAL: Ensure all string values have properly escaped quotes
12. CRITICAL: The response must be ONLY valid JSON - no markdown, no explanations, just the JSON object
13. CRITICAL: Do not add // comments or /* */ comments in the JSON
14. CRITICAL: Every opening bracket {{ or [ must have a matching closing bracket }} or ]

Focus on finding PATTERNS across multiple deviations, not analyzing individual cases."""

def format_batch_pattern_analysis_prompt(
    deviations_with_notes: List[Dict[str, Any]],
    statistical_context: Optional[Dict[str, Any]] = None,
    ml_context: Optional[str] = None
) -> str:
    """
    Format the batch pattern analysis prompt with optional statistical and ML context.

    Args:
        deviations_with_notes: List of deviations to analyze
        statistical_context: Optional statistical analysis to provide context
        ml_context: Optional ML analysis context (clustering, anomalies)

    Returns:
        Formatted prompt string
    """
    deviation_count = len(deviations_with_notes)

    # Format ML context if provided
    ml_section = ""
    if ml_context:
        ml_section = ml_context + "\n\n---\n\n"

    # Format statistical context if provided
    stats_section = ""
    if statistical_context:
        severity_dist = statistical_context.get('severity_distribution', {})
        overview = statistical_context.get('overview', {})
        deviation_types = statistical_context.get('deviation_type_distribution', {})
        temporal = statistical_context.get('temporal_patterns', {})
        risk_indicators = statistical_context.get('risk_indicators', {})

        stats_section = f"""
**STATISTICAL CONTEXT (Analyzed ALL {overview.get('total_deviations', 0)} deviations):**

📊 **Overview:**
- Total Deviations: {overview.get('total_deviations', 0)}
- Unique Cases: {overview.get('unique_cases', 0)}
- Unique Officers: {overview.get('unique_officers', 0)}
- Avg Deviations/Case: {overview.get('average_deviations_per_case', 0)}
- Avg Deviations/Officer: {overview.get('average_deviations_per_officer', 0)}

🔴 **Severity Distribution:**
- Severity Score: {severity_dist.get('severity_score', 0)}/100
- Assessment: {severity_dist.get('severity_assessment', 'Unknown')}
- Critical: {severity_dist.get('distribution', {}).get('critical', {}).get('count', 0)} ({severity_dist.get('distribution', {}).get('critical', {}).get('percentage', 0)}%)
- High: {severity_dist.get('distribution', {}).get('high', {}).get('count', 0)} ({severity_dist.get('distribution', {}).get('high', {}).get('percentage', 0)}%)
- Medium: {severity_dist.get('distribution', {}).get('medium', {}).get('count', 0)} ({severity_dist.get('distribution', {}).get('medium', {}).get('percentage', 0)}%)
- Low: {severity_dist.get('distribution', {}).get('low', {}).get('count', 0)} ({severity_dist.get('distribution', {}).get('low', {}).get('percentage', 0)}%)

📈 **Top 5 Deviation Types:**
{_format_top_types(deviation_types.get('top_10_types', [])[:5])}

⚠️ **Risk Indicators:**
- Critical Mass Score: {risk_indicators.get('critical_mass_score', 0)}/100
- Risk Assessment: {risk_indicators.get('critical_mass_assessment', 'Unknown')}
- Concentration Risk: Top 5 officers account for {risk_indicators.get('concentration_risk', {}).get('top_5_officer_percentage', 0)}% of deviations
- Issue Diversity: {risk_indicators.get('issue_diversity', {}).get('unique_types', 0)} unique deviation types

{_format_advanced_correlations(statistical_context.get('advanced_correlations', {}))}

{_format_association_rules(statistical_context.get('lift_and_odds', {}))}

{_format_time_series(statistical_context.get('time_series', {}))}

{_format_control_charts(statistical_context.get('control_charts', {}))}

{_format_change_points(statistical_context.get('change_points', {}))}

{_format_temporal_patterns(temporal)}

**USE THIS CONTEXT** to:
1. Validate your findings against the statistics
2. Focus on the highest-risk areas identified
3. Explain why certain patterns emerge
4. Make data-driven recommendations

---
"""

    # Format ALL deviations (with or without notes) into readable text
    deviations_text = []
    for i, dev in enumerate(deviations_with_notes, 1):
        notes = dev.get('notes', None)
        notes_text = notes if notes else 'No notes/comments available'

        dev_text = f"""
Deviation {i}:
- Case ID: {dev.get('case_id')}
- Officer ID: {dev.get('officer_id')}
- Type: {dev.get('deviation_type')}
- Severity: {dev.get('severity')}
- Description: {dev.get('description')}
- Expected: {dev.get('expected_behavior', 'N/A')}
- Actual: {dev.get('actual_behavior', 'N/A')}
- Timestamp: {dev.get('detected_at', dev.get('created_at', 'N/A'))}
- Notes: {notes_text}
"""
        deviations_text.append(dev_text.strip())

    deviations_formatted = "\n\n".join(deviations_text)

    # Assemble prompt: ML context + Stats context + Main prompt
    prompt_template = ml_section + stats_section + BATCH_PATTERN_ANALYSIS_PROMPT

    return prompt_template.format(
        deviation_count=deviation_count,
        deviations_with_notes=deviations_formatted
    )


def _format_top_types(top_types: List[Dict[str, Any]]) -> str:
    """Format top deviation types for display."""
    if not top_types:
        return "No data available"

    lines = []
    for i, dtype in enumerate(top_types, 1):
        lines.append(f"  {i}. {dtype.get('type', 'unknown')}: {dtype.get('count', 0)} ({dtype.get('percentage', 0)}%)")

    return "\n".join(lines)


def _format_temporal_patterns(temporal: Dict[str, Any]) -> str:
    """Format temporal patterns for display."""
    if not temporal.get('has_temporal_data'):
        return ""

    period_dist = temporal.get('period_distribution', {})
    peak_hours = temporal.get('peak_hours', [])[:3]
    peak_days = temporal.get('peak_days', [])[:3]

    return f"""⏰ **Temporal Patterns:**
- Morning (6am-12pm): {period_dist.get('morning', {}).get('count', 0)} ({period_dist.get('morning', {}).get('percentage', 0)}%)
- Afternoon (12pm-6pm): {period_dist.get('afternoon', {}).get('count', 0)} ({period_dist.get('afternoon', {}).get('percentage', 0)}%)
- Evening (6pm-12am): {period_dist.get('evening', {}).get('count', 0)} ({period_dist.get('evening', {}).get('percentage', 0)}%)
- Night (12am-6am): {period_dist.get('night', {}).get('count', 0)} ({period_dist.get('night', {}).get('percentage', 0)}%)
- Peak Hours: {', '.join(peak_hours)}
- Peak Days: {', '.join(peak_days)}
"""


def _format_advanced_correlations(adv_corr: Dict[str, Any]) -> str:
    """Format advanced correlation analysis for display."""
    if not adv_corr:
        return ""

    return f"""📊 **Advanced Correlations:**
- Severity ↔ Type: Cramér's V = {adv_corr.get('severity_type_cramers_v', 'N/A')}
  → Interpretation: {adv_corr.get('severity_type_interpretation', 'No significant correlation')}
- Officer ↔ Type: Chi-square p-value = {adv_corr.get('officer_type_chi2_pvalue', 'N/A')}
  → Significant: {'Yes - Officers show distinct deviation patterns' if adv_corr.get('officer_type_chi2_pvalue', 1) < 0.05 else 'No - Officer behavior appears random'}
- Officer ↔ Severity: Cramér's V = {adv_corr.get('officer_severity_cramers_v', 'N/A')}
  → Interpretation: {adv_corr.get('officer_severity_interpretation', 'No significant correlation')}
"""


def _format_association_rules(lift_odds: Dict[str, Any]) -> str:
    """Format association rules (lift & odds) for display."""
    if not lift_odds or not lift_odds.get('top_officer_type_associations'):
        return ""

    rules = lift_odds.get('top_officer_type_associations', [])[:3]
    if not rules:
        return ""

    lines = ["🔗 **Association Rules (Top 3 Officer-Type Patterns):**"]
    for rule in rules:
        officer = rule.get('officer', 'unknown')
        dtype = rule.get('deviation_type', 'unknown')
        lift = rule.get('lift', 0)
        confidence = rule.get('confidence', 0)

        interpretation = f"{lift:.1f}x more likely than average" if lift > 1 else f"{1/lift:.1f}x less likely than average"
        lines.append(f"  • Officer {officer} → {dtype}: Lift = {lift:.2f}x, Confidence = {confidence:.1%}")
        lines.append(f"    → This officer is {interpretation} to commit this deviation type")

    return "\n".join(lines) + "\n"


def _format_time_series(ts: Dict[str, Any]) -> str:
    """Format time series trend analysis for display."""
    if not ts or not ts.get('has_time_series_data'):
        return ""

    trend = ts.get('trend_direction', 'stable')
    ma_trend = ts.get('ma_7day_trend', 'N/A')
    ema_latest = ts.get('ema_latest', 'N/A')
    volatility = ts.get('volatility', 'N/A')

    trend_emoji = "📈" if trend == "increasing" else "📉" if trend == "decreasing" else "📊"

    return f"""{trend_emoji} **Time Series Trends:**
- 7-day Moving Average: {ma_trend} deviations/day (trend: {trend})
- Latest EMA Forecast: {ema_latest} deviations/day
- Volatility (Std Dev): {volatility}
- Trend Direction: {trend.upper()}
  → {'⚠️ Deviation rate is INCREASING - investigate root causes' if trend == 'increasing' else '✅ Deviation rate is DECREASING - controls working' if trend == 'decreasing' else 'Deviation rate is STABLE'}
"""


def _format_control_charts(cc: Dict[str, Any]) -> str:
    """Format control chart analysis for display."""
    if not cc or not cc.get('has_control_chart_data'):
        return ""

    shewhart_out = cc.get('shewhart_out_of_control_count', 0)
    cusum_alert = cc.get('cusum_alert', False)
    ewma_alert = cc.get('ewma_alert', False)

    alert_emoji = "🚨" if (shewhart_out > 0 or cusum_alert or ewma_alert) else "✅"

    lines = [f"{alert_emoji} **Control Chart Alerts:**"]
    lines.append(f"  • Shewhart Chart: {shewhart_out} out-of-control points detected")

    if shewhart_out > 0:
        lines.append(f"    → ⚠️ Process showing unusual spikes beyond 3-sigma control limits")

    if cusum_alert:
        lines.append(f"  • CUSUM Chart: ⚠️ ALERT - Sustained shift detected in process mean")
        lines.append(f"    → Deviation rate has persistently changed (policy/system change?)")
    else:
        lines.append(f"  • CUSUM Chart: ✅ Normal - No sustained shifts detected")

    if ewma_alert:
        lines.append(f"  • EWMA Chart: ⚠️ ALERT - Recent drift detected")
    else:
        lines.append(f"  • EWMA Chart: ✅ Normal - No recent drift")

    return "\n".join(lines) + "\n"


def _format_change_points(cp: Dict[str, Any]) -> str:
    """Format change-point detection results for display."""
    if not cp or not cp.get('change_points'):
        return ""

    change_points = cp.get('change_points', [])[:5]  # Top 5 change points
    if not change_points:
        return ""

    lines = ["🔄 **Change Points Detected (Process Structural Breaks):**"]
    for point in change_points:
        day = point.get('day', 'N/A')
        date = point.get('date', 'N/A')
        before_avg = point.get('before_avg', 'N/A')
        after_avg = point.get('after_avg', 'N/A')

        change_type = "INCREASE" if after_avg > before_avg else "DECREASE"
        emoji = "📈" if change_type == "INCREASE" else "📉"

        lines.append(f"  {emoji} Day {day} ({date}): {change_type} detected")
        lines.append(f"    → Before: {before_avg:.1f} dev/day → After: {after_avg:.1f} dev/day")
        lines.append(f"    → Possible policy change, system update, or training intervention")

    return "\n".join(lines) + "\n"
