"""
Centralized prompt templates for Claude API interactions.
"""
from typing import Dict, Any, List

# SOP Rule Extraction Prompt
SOP_RULE_EXTRACTION_PROMPT = """You are an expert at analyzing Standard Operating Procedures (SOPs) for banking and loan processing to extract ALL compliance rules.

Analyze the following SOP document text and extract EVERY compliance rule, policy, and requirement from the document.

**Rule Categories (not exhaustive - extract ANY rule you find):**

Common rule types include:
- **Process rules**: sequence, approval, timing, validation, exception_handling
- **Risk/Compliance**: kyc_cdd, aml_screening, sanctions_screening, fraud_prevention, credit_risk_assessment, identity_verification, politically_exposed_person, enhanced_due_diligence
- **Authorization**: segregation_of_duties, dual_control, checker_maker, override_approval, threshold_based_approval, escalation
- **Documentation**: documentation_retention, documentation_completeness, signature_verification, document_authenticity, record_retention
- **Financial**: interest_calculation, fee_charging, limit_management, exposure_aggregation, high_value_transaction
- **Regulatory**: regulatory_limit, capital_adequacy, liquidity_limit, concentration_limit, reporting_regulatory, tax_compliance
- **Operations**: cutoff_time, turnaround_time, service_level_agreement, queue_prioritization, holiday_handling, grace_period
- **Security/Collateral**: collateral_verification, collateral_perfection, collateral_revaluation, security_creation
- **Customer**: customer_consent, eligibility, customer_communication, disclosure, privacy_confidentiality, data_protection
- **Monitoring**: monitoring_review, periodic_review, audit_trail, logging, early_warning_trigger
- **Product/Business**: product_eligibility, customer_segment_rule, geo_restriction, branch_level_limit, channel_restriction
- **Risk Management**: covenant_monitoring, repayment_schedule, pre_disbursement_condition, post_disbursement_monitoring, collection_escalation
- **Special Cases**: waiver_rule, restructure_rule, writeoff_rule, chargeback_rule, dispute_resolution, complaint_handling, moratorium_handling
- **System/Process**: system_fallback_manual, system_reconciliation, retry_logic, duplication_check, field_mandatory, field_format, range_check
- **Alerts/Case Management**: watchlist_hit_handling, alert_triage, case_assignment, case_closure, notification_escalation
- **Quality/Model**: quality_assurance_sample, quality_review_full, model_usage, model_override, model_input_validation
- **Staff/Internal**: staff_account_handling, insider_trading_control, conflict_of_interest, training_certification, attestation
- **Approval Variants**: backdating_control, post_facto_approval, partial_approval, conditional_approval, emergency_override
- **Limits/Thresholds**: limit_renewal, limit_reduction, temporary_enhancement, overlimit_transaction, threshold_alerting
- **Multi-currency/International**: multi_currency_handling, fx_rate_application, cross_sell_restriction, upsell_offer_rule
- **Compliance/Governance**: blacklist_whitelist, moderate_risk_override, access_control, business_continuity, incident_reporting
- **Environment/Social**: environment_social_risk, csr_compliance
- **And ANY other banking/compliance rule type you identify**

**CRITICAL INSTRUCTIONS:**
1. Extract ALL rules found, not just the common types listed above
2. Be creative with rule_type names - use the most specific, descriptive name that fits the rule
3. If a rule doesn't fit any standard category, create a new descriptive rule_type name
4. Examples of custom names: "politically_exposed_person_screening", "covenant_monitoring", "fee_waiver_approval"

For each rule, extract:

1. **Rule Type**: Use the most specific rule type name from above OR create a new descriptive name
2. **Rule Description**: Clear, concise description of what must/must not be done
3. **Step Number**: The step number in the process (if mentioned)
4. **Severity**: Based on the language used:
   - "critical": Uses "must", "shall", "required", regulatory/legal requirements
   - "high": Uses "should", affects compliance or risk
   - "medium": Uses "recommended", "advised", affects process quality
   - "low": Uses "may", "optional", best practices
5. **Required Fields**: Any specific data fields that must be present (e.g., income_verification, credit_score)
6. **Timing Constraint**: If it's a timing rule, extract the specific time requirement (e.g., "3 days", "within 48 hours", "immediately")
7. **Conditional Logic**: Any conditions when the rule applies (e.g., "for loans > $50K", "for high-risk customers")
8. **Threshold Value**: For numeric thresholds (e.g., amount > $50,000, score < 650)
9. **Approval Authority**: For approval rules, who must approve (e.g., "manager", "senior officer", "credit committee")

SOP Document Text:
{sop_text}

Return your analysis as a JSON array with this structure:
{{
  "rules": [
    {{
      "rule_type": "specific_category_name",
      "rule_description": "Clear description of the rule",
      "step_number": 1,
      "severity": "critical|high|medium|low",
      "required_fields": ["field1", "field2"],
      "timing_constraint": "X days/hours" or null,
      "conditional_logic": "any special conditions" or null,
      "threshold_value": null,
      "approval_authority": null
    }}
  ]
}}

**Important Notes:**
- Extract EVERY rule, even if it seems minor or doesn't fit the categories above
- Use descriptive, specific rule_type names (e.g., "covenant_monitoring" not "generic_check")
- Be thorough - missing rules can lead to undetected compliance violations"""

# Column Mapping Prompt - Expanded to Support 175+ Fields
COLUMN_MAPPING_PROMPT = """You are an expert at analyzing CSV column headers and mapping them to standardized system fields for comprehensive loan processing workflow data.

I have a CSV file with the following columns:
{headers}

Sample data from first 3 rows:
{sample_rows}

**COMPREHENSIVE SYSTEM FIELDS (175+ fields organized by category):**

**[CRITICAL - Core Identifiers]**
- case_id: Unique case/loan identifier
- application_id: Application identifier
- customer_id: Customer identifier
- customer_name: Customer full name

**[Customer Information]**
- customer_segment: Customer segment (retail, corporate, SME)
- customer_risk_rating: Customer risk rating/score
- group_id: Group/conglomerate identifier
- related_party_flag: Related party transaction flag
- pep_flag: Politically Exposed Person flag
- aml_risk_rating: AML risk rating
- kyc_status: KYC completion status
- kyc_refresh_due_date: KYC refresh due date

**[Organizational Structure]**
- branch_code: Branch code
- branch_name: Branch name
- region: Geographic region
- officer_id: Processing officer ID
- officer_name: Officer name
- officer_role: Officer role/designation

**[Product Details]**
- product_type: Product type (home loan, personal loan, etc.)
- sub_product_type: Sub-product category
- scheme_code: Scheme/program code
- loan_type: Loan type (secured, unsecured)
- loan_purpose: Purpose of loan
- channel: Application channel (branch, online, mobile)
- application_source: Source of application

**[Workflow & Process]**
- step_id: Step identifier
- step_name: Step/activity name
- step_category: Step category
- stage_name: Workflow stage name
- workflow_stage: Current workflow stage
- workflow_version: Workflow version
- action: Action taken
- action_detail: Detailed action description
- previous_action: Previous action in sequence
- next_action: Next expected action
- status: Current status
- sub_status: Detailed sub-status
- decision: Decision made (approved, rejected, etc.)
- decision_reason: Reason for decision
- decision_code: Decision code

**[Exceptions & Overrides]**
- exception_flag: Exception raised flag
- exception_code: Exception code
- exception_reason: Exception reason
- override_flag: Override applied flag
- override_reason: Override reason

**[Approval Hierarchy]**
- approval_level: Approval level (L1, L2, manager, etc.)
- approver_id: Approver identifier
- approver_name: Approver name
- approval_hierarchy: Approval hierarchy/path

**[Queue & SLA Management]**
- queue_name: Queue name
- queue_priority: Queue priority
- sla_target_timestamp: SLA target time
- sla_breach_flag: SLA breach flag
- sla_breach_reason: SLA breach reason

**[Timestamps & Durations]**
- timestamp: Primary timestamp
- timestamp_start: Start timestamp
- timestamp_end: End timestamp
- application_date: Application date
- decision_date: Decision date
- disbursement_date: Disbursement date
- closure_date: Case closure date
- duration_seconds: Duration in seconds
- duration_minutes: Duration in minutes
- business_date: Business date
- business_day_of_week: Day of week
- business_hour: Hour of day

**[Financial Amounts]**
- loan_amount: Loan amount
- requested_amount: Requested amount
- approved_amount: Approved amount
- disbursed_amount: Disbursed amount
- outstanding_amount: Outstanding balance
- overdue_amount: Overdue amount
- emi_amount: EMI/installment amount

**[Loan Terms & Conditions]**
- interest_rate: Interest rate
- interest_type: Interest type (fixed, floating)
- tenor_months: Tenor in months
- tenor_days: Tenor in days
- repayment_frequency: Repayment frequency
- installment_number: Installment number

**[Collateral & Security]**
- collateral_type: Type of collateral
- collateral_description: Collateral description
- collateral_value: Collateral value
- collateral_value_date: Collateral valuation date
- ltv_ratio: Loan-to-value ratio
- security_coverage_ratio: Security coverage ratio
- guarantor_flag: Guarantor present flag
- guarantor_id: Guarantor identifier

**[Credit & Risk Scoring]**
- credit_score_bureau: Bureau credit score
- credit_score_internal: Internal credit score
- scorecard_version: Scorecard version used
- score_band: Score band/category
- probability_of_default: PD estimate
- loss_given_default: LGD estimate
- exposure_at_default: EAD estimate
- total_exposure_group: Total group exposure
- total_exposure_customer: Total customer exposure

**[Document Management]**
- document_type: Document type
- document_id: Document identifier
- document_name: Document name
- document_version: Document version
- document_expiry_date: Document expiry date
- document_collection_date: Document collection date
- document_verification_status: Verification status
- document_verifier_id: Verifier identifier
- document_exception_flag: Document exception flag

**[Remediation & Follow-up]**
- remediation_due_date: Remediation due date
- remediation_status: Remediation status
- reminder_count: Number of reminders sent
- contact_attempts: Contact attempts count
- contact_outcome: Contact outcome
- customer_response: Customer response

**[Communication]**
- communication_channel: Communication channel used
- notification_sent_flag: Notification sent flag
- notification_type: Type of notification

**[Notes & Comments]**
- notes: General notes
- comments: Comments
- internal_remarks: Internal remarks only

**[Audit & Tracking]**
- audit_trail_id: Audit trail identifier
- created_by: Created by user
- created_at: Created timestamp
- updated_by: Last updated by
- updated_at: Last updated timestamp
- source_system: Source system
- source_file_name: Source file name
- source_file_row_number: Row number in source
- import_batch_id: Import batch identifier

**[Error Handling]**
- error_flag: Error flag
- error_code: Error code
- error_message: Error message
- retry_count: Retry count
- duplicate_flag: Duplicate record flag

**[Case Relationships]**
- reference_case_id: Reference case ID
- parent_case_id: Parent case ID
- related_case_id: Related case ID

**[Rules & Deviations]**
- rule_version: Rule version applied
- deviation_flag: Deviation detected flag
- deviation_type: Type of deviation
- deviation_severity: Deviation severity
- deviation_detected_at: Deviation detection time
- deviation_resolved_at: Deviation resolution time
- deviation_resolution: Resolution details

**[Pattern & Anomaly Detection]**
- pattern_cluster_id: Pattern cluster identifier
- pattern_cluster_score: Cluster score
- anomaly_score: Anomaly score
- anomaly_reason: Anomaly reason

**[Custom/Flexible Fields]**
- custom_field_1: Custom field 1
- custom_field_2: Custom field 2
- custom_field_3: Custom field 3
- custom_field_4: Custom field 4
- custom_field_5: Custom field 5

**Your Task:**
1. Map EACH CSV column to the MOST APPROPRIATE system field from above
2. Use semantic meaning, not just exact name matches
3. Identify notes/comments columns
4. Flag any columns that truly don't fit any of the 175+ fields above

**Mapping Guidelines:**
- "Loan_ID" / "Application_No" → case_id
- "Customer_Name" / "Borrower" → customer_name
- "User" / "Employee" / "Staff_ID" → officer_id
- "Activity" / "Task" / "Process_Step" → step_name
- "Decision" / "Outcome" → decision or action
- "Date" / "Time" / "DateTime" → timestamp
- "Amount" / "Value" / "Principal" → loan_amount or requested_amount
- "Rate" / "Interest" / "ROI" → interest_rate
- "Remarks" / "Notes" / "Comments" / "Explanation" → notes
- Use the BEST FIT field from the 175+ options above

**CRITICAL - Return Format:**
Return ONLY this exact JSON structure (simple string mappings):
{{
  "mappings": {{
    "CSV_Column_Name": "system_field_name"
  }},
  "notes_column": "Name of column containing notes/comments, or null",
  "unmapped_columns": ["columns", "that", "truly", "dont", "fit"],
  "warnings": ["Any concerns or ambiguities"]
}}

**Important:**
- DO NOT include nested objects
- Each mapping value MUST be a simple string (one of the 175+ field names above)
- If unsure between 2 fields, pick the MORE SPECIFIC one
- Unmapped should be RARE (most things should map to the 175+ fields)
- Missing columns in upload = NULL values (perfectly fine, won't break analysis)

Example:
{{
  "mappings": {{
    "Loan_ID": "case_id",
    "Cust_Name": "customer_name",
    "User": "officer_id",
    "Activity": "step_name",
    "Decision": "decision",
    "Date": "timestamp",
    "Amount": "loan_amount",
    "Interest": "interest_rate",
    "Remarks": "notes"
  }},
  "notes_column": "Remarks",
  "unmapped_columns": [],
  "warnings": []
}}"""

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

1. **Deviation Type**: One of:
   - "missing_step": Required step was skipped
   - "wrong_sequence": Steps done in wrong order
   - "unauthorized_approval": Approval by wrong authority
   - "timing_violation": Time constraint not met
   - "validation_failure": Required validation not performed

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
      "deviation_type": "missing_step|wrong_sequence|unauthorized_approval|timing_violation|validation_failure",
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

Focus on finding PATTERNS across multiple deviations, not analyzing individual cases."""

def format_batch_pattern_analysis_prompt(deviations_with_notes: List[Dict[str, Any]]) -> str:
    """Format the batch pattern analysis prompt."""
    deviation_count = len(deviations_with_notes)

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

    return BATCH_PATTERN_ANALYSIS_PROMPT.format(
        deviation_count=deviation_count,
        deviations_with_notes=deviations_formatted
    )
