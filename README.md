# Loan Workflow Deviation Detection System

## Table of Contents
1. [Introduction](#introduction)
2. [System Purpose](#system-purpose)
3. [Core Concepts](#core-concepts)
4. [SOP Rule Extraction](#sop-rule-extraction)
5. [Field Mapping & Flexibility](#field-mapping--flexibility)
6. [Data Cleaning Pipeline](#data-cleaning-pipeline)
7. [Missing Field Analysis](#missing-field-analysis)
8. [Deviation Detection](#deviation-detection)
9. [Statistical Analysis](#statistical-analysis)
10. [Machine Learning Pipeline](#machine-learning-pipeline)
11. [AI Pattern Recognition](#ai-pattern-recognition)
12. [Frontend Architecture](#frontend-architecture)
13. [Data Flow](#data-flow)
14. [System Architecture](#system-architecture)
15. [Installation & Setup](#installation--setup)
16. [Configuration](#configuration)

---

## Introduction

### Why This Approach?

Instead of directly feeding all workflow logs and SOPs to an LLM, this system uses a **layered, structured approach**:

**Problem with Pure LLM Approach:**
- **Context Overflow:** Large datasets (1000+ workflow logs) exceed LLM token limits
- **Loss of Focus:** LLMs lose track of specific violations when processing massive amounts of data
- **Inconsistent Detection:** Without structured rules, LLMs may miss systematic patterns
- **No Reproducibility:** LLM outputs vary between runs, making audit trails unreliable

**Our Hybrid Solution:**
1. **Rule-Based Detection (Fast & Precise):** Extract structured rules from SOPs using LLM once, then apply them deterministically
2. **Statistical Pre-Processing:** Summarize 1000+ logs into key patterns and outliers
3. **ML Clustering:** Identify similar deviation groups and anomalies (1.9x data compression)
4. **Targeted LLM Analysis:** Feed only representative samples (69 out of 129 deviations) with statistical context
5. **Intelligent Synthesis:** LLM focuses on behavioral patterns, not individual rule violations

**Result:** Accurate, fast, scalable, and explainable deviation detection with human-like pattern recognition.

---

## System Purpose

This system automates the detection of **Standard Operating Procedure (SOP) violations** in loan processing workflows. It helps compliance teams:

1. **Detect Deviations:** Automatically identify SOP violations across thousands of loan cases
2. **Ensure Compliance:** Enforce regulatory and policy requirements consistently
3. **Identify Patterns:** Discover systemic issues, officer behavior patterns, and hidden informal rules
4. **Reduce Risk:** Flag high-risk violations (missing approvals, LTV breaches, KYC failures)
5. **Audit Workflows:** Maintain complete audit trails with detailed deviation explanations

**Use Case:** Banks, NBFCs, lending institutions processing secured/unsecured personal loans, home loans, business loans.

---

## Core Concepts

### 1. Workflow Logs

**Definition:** A chronological record of every action taken during loan processing.

**Structure:**
- **case_id:** Unique loan application identifier (e.g., SPL-001)
- **step_name:** Workflow stage (e.g., "Credit Bureau Check", "Disbursement")
- **timestamp:** When the action occurred
- **officer_id:** Who performed the action
- **Fields:** loan_amount, collateral_value, credit_score, ltv_ratio, etc.

**Example:**
```csv
case_id,officer_id,step_name,timestamp,loan_amount,credit_score,ltv_ratio
SPL-001,OFF001,Application Received,2025-01-06 09:15:00,450000,735,72.6
SPL-001,OFF001,Credit Bureau Check,2025-01-06 10:32:00,450000,735,72.6
SPL-001,OFF002,Approval,2025-01-06 13:05:00,450000,735,72.6
```

### 2. Cases

**Definition:** A complete loan application with all its workflow steps grouped by `case_id`.

**Relationship:**
- **One Case** = Multiple Workflow Steps (typically 5-15 steps)
- Example: Case SPL-001 might have 8 steps from application to disbursement

### 3. Deviations

**Definition:** An SOP violation detected in a case.

**Structure:**
- **deviation_type:** Type of violation (e.g., ltv_breach, missing_approval)
- **severity:** Impact level (critical, high, medium, low)
- **description:** What went wrong
- **expected_behavior:** What should have happened (per SOP)
- **actual_behavior:** What actually happened
- **context:** Additional data (thresholds, values, etc.)

**Relationship:**
- **One Case** can have **Multiple Deviations** (e.g., both LTV breach AND missing approval)
- **One Deviation Type** can occur across **Multiple Cases** (e.g., 42 cases with LTV breach)

**Example:**
```json
{
  "case_id": "SPL-003",
  "deviation_type": "emi_to_income_breach",
  "severity": "high",
  "description": "EMI-to-Income ratio 52.00% exceeds limit 50.00% for Self-Employed customers",
  "expected_behavior": "EMI-to-Income ratio must be ≤50.00% for Self-Employed customers (per SOP Section 2.4)",
  "actual_behavior": "Ratio is 52.00%",
  "context": {
    "emi_to_income_ratio": 0.52,
    "max_ratio": 0.50,
    "employment_type": "Self-Employed"
  }
}
```

---

## SOP Rule Extraction

### How It Works

The system uses **Claude AI (Sonnet 4.5)** to extract structured rules from text-based SOP documents.

### Process Flow

```
┌─────────────────────┐
│ Upload SOP Document │
│  (Text/PDF)         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ Send to Claude API with Structured      │
│ Prompt (app/services/claude/prompts.py) │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────┐
│ Claude Extracts Rules with Fields:          │
│ - rule_text: Original SOP text              │
│ - rule_type: eligibility/approval/sequence  │
│ - threshold_value: Numeric limit (e.g., 65) │
│ - field_dependencies: Required fields       │
│ - condition_logic: IF-THEN conditions       │
│ - severity: Policy importance level         │
└──────────┬──────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ Validate Rules with Pydantic Schema │
│ (app/models/schemas.py)             │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────┐
│ Store in Database   │
│ (SQLite database)   │
└─────────────────────┘
```

### Example Rule Extraction

**Input SOP Text:**
```
Section 2.1: Customer Age Eligibility
Minimum age: 21 years
Maximum age: 65 years
```

**Claude Output:**
```json
{
  "rule_text": "Customer age must be between 21 and 65 years",
  "rule_type": "eligibility",
  "threshold_value": 21,
  "field_dependencies": ["customer_age"],
  "condition_logic": {
    "field": "customer_age",
    "operator": "BETWEEN",
    "value": [21, 65]
  },
  "severity": "critical"
}
```

### Key Features

1. **Conditional Rule Support:** Extracts IF-THEN rules (e.g., "IF employment_type = Salaried THEN max_emi = 55%")
2. **Field Dependency Mapping:** Identifies which CSV fields are needed to evaluate each rule
3. **Threshold Extraction:** Captures numeric limits (60%, 100000, 84 months)
4. **Fallback Mechanism:** If Claude fails, uses regex-based extraction as backup

---

## Field Mapping & Flexibility

### The Challenge

Different organizations use different CSV column names:
- Bank A: `customer_age` vs Bank B: `applicant_age`
- Bank A: `loan_amount_sanctioned` vs Bank B: `approved_amount`

### Our Solution: Flexible Field Matching

**Location:** `ai-service/app/services/data/workflow_log_cleaner.py`

### Matching Logic

```python
# System expects: "customer_age"
# CSV might have: "customer_age", "applicant_age", "borrower_age", "age"

FIELD_ALIASES = {
    'customer_age': ['customer_age', 'applicant_age', 'borrower_age', 'age'],
    'loan_amount_sanctioned': ['loan_amount_sanctioned', 'sanctioned_amount', 'approved_amount', 'loan_amount'],
    'credit_score': ['credit_score', 'credit_score_bureau', 'cibil_score', 'bureau_score'],
    # ... 25+ field mappings
}
```

### How It Works

```
┌──────────────────────────┐
│ CSV Headers Received     │
│ [applicant_age, cibil_   │
│  score, approved_amount] │
└───────────┬──────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│ For each expected field:            │
│ 1. Check exact match                │
│ 2. Check aliases (case-insensitive) │
│ 3. Check partial matches            │
└───────────┬─────────────────────────┘
            │
            ▼
┌──────────────────────────────────────┐
│ Normalize to Standard Field Names   │
│ applicant_age → customer_age         │
│ cibil_score → credit_score           │
│ approved_amount → loan_amount_sanctioned │
└──────────────────────────────────────┘
```

**Result:** System works with ANY CSV format without manual configuration.

---

## Data Cleaning Pipeline

**Location:** `ai-service/app/services/data/workflow_log_cleaner.py`

### Cleaning Steps

#### 1. Duplicate Removal
```python
# Remove exact duplicate rows (same case_id, timestamp, step_name)
# Keeps only first occurrence
```

#### 2. Type Validation & Fixing
```python
# Fix common type issues:
- customer_age: Convert "34.0" → 34 (int)
- credit_score: Convert "735" → 735 (int)
- ltv_ratio: Convert "72.6" → 72.6 (float)
- emi_to_income_ratio: Normalize 42 → 0.42 or 0.42 → 0.42 (decimal)
- timestamps: Parse multiple formats (ISO, DD/MM/YYYY, etc.)
```

#### 3. Missing Value Handling
```python
# Strategy by field type:
- Numeric fields: Keep as null (don't fill with 0 - misleading)
- Text fields: Set to "unknown" or "not_specified"
- Boolean flags: Set to False if not "yes"/"true"/"1"
- Dates: Keep as null (don't fabricate dates)
```

#### 4. Text Normalization
```python
# Standardize text fields:
- Lowercase: "Application Received" → "application received"
- Trim whitespace: "  KYC Done  " → "kyc done"
- Remove special chars: "Approval (Branch)" → "approval branch"
- Standardize values:
  - "Y", "Yes", "TRUE", "1" → "yes"
  - "N", "No", "FALSE", "0" → "no"
```

#### 5. Data Quality Scoring
```python
# Calculate quality score (0-100):
score = (
    (fields_populated / total_fields) * 40 +
    (logs_valid / total_logs) * 30 +
    (1 - duplicate_rate) * 20 +
    (type_correctness) * 10
)
```

### Cleaning Report

After cleaning, system generates a report:

```json
{
  "total_logs": 434,
  "cleaned_logs": 434,
  "duplicates_removed": 0,
  "invalid_logs_removed": 0,
  "type_issues_fixed": 868,
  "missing_values_handled": 868,
  "text_fields_normalized": 868,
  "quality_score": 85.0,
  "quality_grade": "B"
}
```

---

## Missing Field Analysis

**Location:** `ai-service/app/services/data/missing_field_analyzer.py`

### Purpose

Identify which SOP rules **cannot be evaluated** due to missing CSV fields.

### Process

```
┌─────────────────────────────┐
│ Extract Required Fields     │
│ from SOP Rules              │
│ (field_dependencies array)  │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Get Available Fields from   │
│ CSV Headers                 │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ Compare: Required vs Available      │
│ Missing = Required - Available      │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ Identify Affected Rules             │
│ (rules that can't be evaluated)     │
└─────────────────────────────────────┘
```

### Example Output

```json
{
  "missing_fields": [
    "property_type",
    "monthly_income",
    "existing_loan_obligations",
    "pep_flag",
    "sanctions_screening"
  ],
  "affected_rules": [
    {
      "rule_id": "R-012",
      "rule_text": "LTV limits vary by property type",
      "missing_fields": ["property_type"],
      "impact": "Cannot apply conditional LTV limits"
    },
    {
      "rule_id": "R-008",
      "rule_text": "PEP customers require enhanced due diligence",
      "missing_fields": ["pep_flag"],
      "impact": "Cannot detect PEP violations"
    }
  ],
  "total_rules": 61,
  "evaluable_rules": 23,
  "unevaluable_rules": 38
}
```

### Why This Matters

- **Transparency:** Users know which rules are being checked
- **Data Quality Feedback:** Shows what fields need to be added to CSV
- **No False Negatives:** Won't silently skip rules due to missing data

---

## Deviation Detection

The system uses **13 specialized checker modules** to detect violations:

### Deviation Types & Detection Logic

#### 1. Data Quality Deviations
**Checker:** `DataQualityChecker`
**File:** `ai-service/app/services/deviation/data_quality_checker.py`

**Detects:**
- **missing_critical_field:** Required field is null/empty
- **invalid_data_type:** Field has wrong type (e.g., text in numeric field)
- **missing_audit_trail:** Critical step has no audit/notes field

**Logic:**
```python
# For each case:
1. Check if critical fields (loan_amount, customer_id) are missing
2. Validate data types match expected types
3. Check if critical steps (approval, disbursement) have audit notes
```

---

#### 2. Eligibility Deviations
**Checker:** `EligibilityChecker`
**File:** `ai-service/app/services/deviation/eligibility_checker.py`

**Detects:**
- **ineligible_age:** Customer age outside policy limits
- **ineligible_tenor:** Loan tenor exceeds maximum allowed
- **emi_to_income_breach:** EMI-to-Income ratio exceeds policy limit (conditional on employment type)
- **low_score_approved_without_exception:** Low credit score approved without documented exception

**Logic:**
```python
# Extract thresholds from SOP
min_age = 21, max_age = 65, max_emi = 0.6, min_credit_score = 650

# For each case:
1. Age Check:
   if customer_age < min_age OR customer_age > max_age:
       → ineligible_age deviation

2. Tenor Check:
   if tenor_months > max_tenor (84 months):
       → ineligible_tenor deviation

3. EMI Check (CONDITIONAL):
   # Apply different thresholds based on employment type
   if employment_type = "Salaried":
       threshold = 0.55  # 55%
   elif employment_type = "Self-Employed":
       threshold = 0.50  # 50%
   elif monthly_income > 100000:
       threshold = 0.60  # 60% for high income

   if emi_to_income_ratio > threshold:
       → emi_to_income_breach deviation

4. Credit Score Check:
   if credit_score < min_credit_score AND approved = True AND exception_flag != "yes":
       → low_score_approved_without_exception deviation
```

---

#### 3. Collateral Deviations
**Checker:** `CollateralChecker`
**File:** `ai-service/app/services/deviation/collateral_checker.py`

**Detects:**
- **ltv_breach:** Loan-to-Value ratio exceeds policy limit
- **valuation_missing_or_stale:** Collateral valuation missing or outdated (>90 days)
- **security_not_created:** Legal security not created before disbursement

**Logic:**
```python
# For secured loans only:
1. LTV Check (CONDITIONAL by collateral type):
   ltv_limits = {
       "Residential Self-Occupied": 0.75,  # 75%
       "Residential Rented": 0.70,         # 70%
       "Commercial": 0.65                  # 65%
   }

   if ltv_ratio > ltv_limits[collateral_type]:
       → ltv_breach deviation

2. Valuation Age Check:
   if disbursement_step exists:
       valuation_age = disbursement_date - collateral_value_date
       if valuation_age > 90 days:
           → valuation_missing_or_stale deviation

3. Security Creation Check:
   if disbursement_step exists AND security_created_flag != "yes":
       → security_not_created deviation
```

---

#### 4. KYC Deviations
**Checker:** `KYCChecker`
**File:** `ai-service/app/services/deviation/kyc_checker.py`

**Detects:**
- **kyc_incomplete:** KYC not completed before proceeding
- **kyc_expired:** KYC older than validity period (typically 180 days)
- **sanctions_hit_not_resolved:** Sanctions screening hit not cleared

**Logic:**
```python
# For each case:
1. KYC Completeness Check:
   if any_step_after("kyc verification") AND kyc_status != "completed":
       → kyc_incomplete deviation

2. KYC Expiry Check:
   kyc_age = current_step_date - kyc_completion_date
   if kyc_age > 180 days:
       → kyc_expired deviation

3. Sanctions Check:
   if sanctions_screening = "Hit" AND sanctions_clearance_flag != "yes":
       → sanctions_hit_not_resolved deviation
```

---

#### 5. Documentation Deviations
**Checker:** `DocumentationChecker`
**File:** `ai-service/app/services/deviation/documentation_checker.py`

**Detects:**
- **missing_required_document:** Required document not uploaded/verified
- **document_not_verified:** Document uploaded but not verified

**Logic:**
```python
# For each case:
required_docs = ["ID Proof", "Address Proof", "Income Proof", "Bank Statement"]

for doc in required_docs:
    if doc not in uploaded_documents:
        → missing_required_document deviation
    elif doc_status != "verified":
        → document_not_verified deviation
```

---

#### 6. Disbursement Deviations
**Checker:** `DisbursementChecker`
**File:** `ai-service/app/services/deviation/disbursement_checker.py`

**Detects:**
- **disbursement_without_approval:** Loan disbursed without approval step
- **partial_disbursement_violation:** Partial disbursement not allowed per SOP
- **mandate_not_set:** Auto-debit mandate not set before disbursement

**Logic:**
```python
# For each case with disbursement:
1. Approval Check:
   if "disbursement" step exists AND no "approval" step before it:
       → disbursement_without_approval deviation

2. Partial Disbursement Check:
   if disbursement_amount < sanctioned_amount AND partial_disbursement_allowed = False:
       → partial_disbursement_violation deviation

3. Mandate Check:
   if disbursement_step exists AND mandate_status != "set":
       → mandate_not_set deviation
```

---

#### 7. Collection Deviations
**Checker:** `CollectionChecker` (RegulatoryAggregator)
**File:** `ai-service/app/services/deviation/collection_checker.py`

**Detects:**
- **customer_exposure_limit_exceeded:** Total exposure to customer exceeds limit
- **overdue_not_escalated:** Overdue account not escalated per policy

**Logic:**
```python
# For each customer (group by customer_id):
1. Exposure Limit Check:
   total_exposure = sum(loan_amounts for all active loans)
   if total_exposure > customer_exposure_limit (e.g., 5,000,000):
       → customer_exposure_limit_exceeded deviation

2. Overdue Escalation Check:
   if dpd (days past due) > 30 AND escalation_flag != "yes":
       → overdue_not_escalated deviation
```

---

#### 8. Regulatory Deviations
**Checker:** `RegulatoryChecker`
**File:** `ai-service/app/services/deviation/regulatory_checker.py`

**Detects:**
- **regulatory_limit_breach:** Loan violates regulatory limits (e.g., RBI guidelines)
- **reporting_delay:** Regulatory reporting not done within mandated timeline

**Logic:**
```python
# For each case:
1. Regulatory Limit Check:
   if loan_amount > regulatory_single_borrower_limit:
       → regulatory_limit_breach deviation

2. Reporting Timeline Check:
   if reporting_required AND report_submission_date > deadline:
       → reporting_delay deviation
```

---

#### 9. Sequence Deviations
**Checker:** `SequenceChecker`
**File:** `ai-service/app/services/deviation/sequence_checker.py`

**Detects:**
- **out_of_sequence:** Workflow steps executed in wrong order
- **missing_prerequisite_step:** Required prerequisite step not completed

**Logic:**
```python
# Define expected sequence:
required_sequence = [
    "Application Received",
    "KYC Verification",
    "Credit Bureau Check",
    "Credit Assessment",
    "Approval",
    "Disbursement"
]

# For each case:
actual_sequence = extract_step_sequence(case_logs)

1. Sequence Check:
   for i, expected_step in enumerate(required_sequence):
       if actual_sequence[i] != expected_step:
           → out_of_sequence deviation

2. Prerequisite Check:
   if "Approval" step exists AND "Credit Bureau Check" not done before:
       → missing_prerequisite_step deviation
```

---

#### 10. Approval Authority Deviations
**Checker:** `RuleValidator`
**File:** `ai-service/app/services/deviation/rule_validator.py`

**Detects:**
- **missing_approval:** No approval step found in workflow
- **insufficient_approval_hierarchy:** Wrong approver for loan amount/risk grade

**Logic:**
```python
# Approval authority matrix (CONDITIONAL):
if loan_amount <= 500000 AND risk_grade in ["A", "B"]:
    required_approver = "Branch Manager"
elif loan_amount <= 3000000 AND risk_grade in ["A", "B", "C"]:
    required_approver = "Regional Credit Manager"
elif loan_amount > 3000000:
    required_approver = "Credit Committee"

# For each case:
1. Approval Existence Check:
   if no "approval" step found:
       → missing_approval deviation

2. Approver Authority Check:
   if actual_approver != required_approver:
       → insufficient_approval_hierarchy deviation
```

---

#### 11. Temporal Rule Deviations
**Checker:** `TemporalRuleEvaluator`
**File:** `ai-service/app/services/deviation/temporal_rule_evaluator.py`

**Detects:**
- **temporal_sla_breach:** Time between steps exceeds SLA
- **expired_offer:** Loan offer used after expiry period

**Logic:**
```python
# Define SLA rules:
sla_rules = {
    ("Application", "Credit Bureau Check"): 24 hours,
    ("Approval", "Disbursement"): 48 hours
}

# For each case:
1. SLA Check:
   for (step_a, step_b), max_hours in sla_rules.items():
       time_diff = timestamp(step_b) - timestamp(step_a)
       if time_diff > max_hours:
           → temporal_sla_breach deviation

2. Offer Expiry Check:
   offer_age = disbursement_date - approval_date
   if offer_age > offer_validity_days (e.g., 30 days):
       → expired_offer deviation
```

---

#### 12. Conditional Rule Deviations
**Checker:** `ConditionalRuleEvaluator`
**File:** `ai-service/app/services/deviation/conditional_rule_evaluator.py`

**Detects:**
- **conditional_rule_violation:** IF-THEN rule violated

**Logic:**
```python
# Example conditional rules:
# Rule: "IF pep_flag = 'Yes' THEN require enhanced_due_diligence = 'Yes'"
# Rule: "IF property_type = 'Commercial' THEN max_ltv = 65%"

# For each conditional rule:
1. Evaluate condition (IF part):
   condition_met = evaluate_condition(rule.condition_logic, case_data)

2. If condition is true, check action (THEN part):
   if condition_met:
       expected_result = rule.then_clause
       actual_result = case_data[rule.field]
       if actual_result != expected_result:
           → conditional_rule_violation deviation
```

**Note:** Most conditional logic is now handled within specialized checkers (EligibilityChecker for conditional EMI, CollateralChecker for conditional LTV). This checker handles remaining generic conditional rules.

---

#### 13. Regulatory Portfolio Deviations
**Checker:** `RegulatoryAggregator`
**File:** `ai-service/app/services/deviation/regulatory_aggregator.py`

**Detects:**
- **customer_exposure_limit_exceeded:** Total exposure to customer exceeds regulatory limit
- **sector_concentration_risk:** Sector concentration exceeds limit
- **branch_concentration_risk:** Branch handling too much volume

**Logic:**
```python
# Aggregate across all cases:
1. Customer Exposure:
   for each customer_id:
       total_exposure = sum(loan_amounts)
       if total_exposure > exposure_limit (25% of capital):
           → customer_exposure_limit_exceeded

2. Sector Concentration:
   for each sector:
       sector_percentage = sector_loans / total_loans
       if sector_percentage > 15%:
           → sector_concentration_risk

3. Branch Concentration:
   for each branch:
       branch_percentage = branch_cases / total_cases
       if branch_percentage > 30%:
           → branch_concentration_risk
```

---

### Detection Summary

**Total Deviation Types Detected:** 20+

**Coverage:**
- ✅ Eligibility violations (age, tenor, EMI, credit score)
- ✅ Collateral violations (LTV, valuation, security)
- ✅ Process violations (sequence, approvals, KYC)
- ✅ Documentation violations (missing/unverified docs)
- ✅ Regulatory violations (exposure limits, sanctions)
- ✅ Temporal violations (SLA breaches, expired offers)
- ✅ Conditional rules (IF-THEN logic)

---

## Statistical Analysis

**Location:** `ai-service/app/services/data/statistical_analyzer.py`, `advanced_statistics.py`

After detecting deviations, the system performs comprehensive statistical analysis:

### Basic Statistics

#### 1. Overview Metrics
```python
- Total deviations: 129
- Unique cases with deviations: 50
- Unique officers involved: 5
- Average deviations per case: 2.58
- Average deviations per officer: 25.8
```

#### 2. Severity Distribution
```python
severity_counts = {
    "critical": 31,  # 24.0%
    "high": 98,      # 76.0%
    "medium": 0,     # 0%
    "low": 0         # 0%
}
```

#### 3. Deviation Type Distribution
```python
type_counts = {
    "ltv_breach": 42,                           # 32.6%
    "customer_exposure_limit_exceeded": 32,     # 24.8%
    "missing_approval": 31,                     # 24.0%
    "valuation_missing_or_stale": 16,          # 12.4%
    "ineligible_tenor": 5,                      # 3.9%
    "emi_to_income_breach": 5                   # 3.9%
}
```

#### 4. Temporal Patterns (Workflow Activity)
```python
# Uses WORKFLOW LOG timestamps (not deviation timestamps)
temporal_patterns = {
    "peak_hours": ["10:00", "11:00", "13:00"],        # When most work happens
    "peak_days": ["Monday", "Tuesday", "Wednesday"],  # Busiest days
    "hour_distribution": {
        "09:00": 45,  # 45 workflow steps at 9 AM
        "10:00": 68,  # 68 workflow steps at 10 AM
        ...
    },
    "period_distribution": {
        "morning": 48.0%,    # 9 AM - 12 PM
        "afternoon": 52.0%   # 12 PM - 6 PM
    }
}
```

#### 5. Officer Statistics
```python
officer_stats = {
    "OFF001": {
        "total_deviations": 47,
        "severity_breakdown": {"critical": 10, "high": 37},
        "top_deviation_types": ["ltv_breach", "missing_approval"],
        "cases_handled": 18
    },
    ...
}
```

#### 6. Case Statistics
```python
case_stats = {
    "cases_with_deviations": 50,
    "cases_without_deviations": 0,
    "cases_with_multiple_deviations": 35,
    "max_deviations_per_case": 5,
    "avg_deviations_per_case": 2.58
}
```

---

### Advanced Statistics

#### 7. Correlation Analysis
```python
# Measures association between categorical variables using Cramér's V
correlations = {
    "officer_id vs deviation_type": 0.42,  # Moderate correlation
    "deviation_type vs severity": 0.85,    # Strong correlation
    "case_id vs deviation_type": 0.15      # Weak correlation
}
```

**Interpretation:**
- High correlation (>0.5): Officers may have specialization or bias patterns
- Low correlation (<0.3): Random distribution, no pattern

#### 8. Lift & Odds Ratios
```python
# Measures how much more likely an officer is to make a specific deviation type

lift_analysis = {
    "OFF001 → ltv_breach": {
        "lift": 2.5,        # 2.5x more likely than average
        "odds_ratio": 4.2,  # 4.2x higher odds
        "confidence": 0.95  # 95% confidence level
    }
}
```

**Interpretation:**
- Lift > 2.0: Strong association (officer frequently makes this error)
- Odds Ratio > 3.0: Significant risk factor

#### 9. Time-Series Analysis (on Workflow Logs)
```python
# Analyzes workflow processing trends over time
time_series = {
    "daily_volume": {
        "2025-01-06": 71,   # 71 workflow steps
        "2025-01-07": 116,  # Peak day
        "2025-01-08": 89
    },
    "moving_average_7d": [82, 94, 98, ...],  # Trend line
    "std_dev": 15.4  # Variability
}
```

#### 10. Control Charts (Quality Control)
```python
# Statistical process control for detecting unusual patterns
control_charts = {
    "mean": 87.0,           # Average daily workflow volume
    "upper_limit": 113.2,   # 3-sigma upper limit
    "lower_limit": 60.8,    # 3-sigma lower limit
    "out_of_control": []    # Days exceeding limits
}
```

**Interpretation:**
- Points above upper limit: Overload/rush periods
- Points below lower limit: Underutilization/holidays

#### 11. Change-Point Detection
```python
# Identifies when workflow patterns change significantly
change_points = {
    "detected_changes": [
        {
            "date": "2025-01-07",
            "type": "volume_spike",
            "magnitude": "+62%",
            "confidence": 0.88
        }
    ]
}
```

**Use Case:** Detect policy changes, system upgrades, or process modifications

---

## Machine Learning Pipeline

**Location:** `ai-service/app/services/ml/ml_pipeline.py`

The ML layer reduces data volume while preserving important patterns:

### ML Processing Steps

```
┌─────────────────────────┐
│ 129 Deviations          │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ STEP 1: Feature Engineering         │
│ (ml/feature_engineer.py)             │
│ - Encode categorical features       │
│ - Create numerical features         │
│ - Generate TF-IDF vectors           │
└──────────┬──────────────────────────┘
           │ (16 features per deviation)
           ▼
┌─────────────────────────────────────┐
│ STEP 2: Clustering (ml/clustering.py)│
│ - DBSCAN algorithm                  │
│ - Group similar deviations          │
│ - Identify noise (outliers)         │
└──────────┬──────────────────────────┘
           │ (21 clusters + 51 noise points)
           ▼
┌─────────────────────────────────────────┐
│ STEP 3: Anomaly Detection               │
│ (ml/anomaly_detector.py)                │
│ - Isolation Forest algorithm            │
│ - Flag unusual deviations               │
└──────────┬──────────────────────────────┘
           │ (13 anomalies detected)
           ▼
┌─────────────────────────────────────────┐
│ STEP 4: Intelligent Sampling            │
│ (ml/intelligent_sampler.py)             │
│ - Select ALL anomalies (13)            │
│ - Select cluster representatives (56)   │
│ - Total: 69 samples (1.9x compression) │
└─────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────┐
│ Send 69 Deviations to   │
│ Claude for Pattern      │
│ Analysis (not 129!)     │
└─────────────────────────┘
```

### Detailed ML Steps

#### STEP 1: Feature Engineering

**Purpose:** Convert text and categorical data into numeric vectors for ML algorithms

**Process:**
```python
# For each deviation, create:
1. Categorical Features (One-Hot Encoding):
   - deviation_type_ltv_breach = 1/0
   - deviation_type_missing_approval = 1/0
   - severity_critical = 1/0
   - severity_high = 1/0
   (7 binary features)

2. Numerical Features:
   - case_id_hash: Hash of case_id (numeric representation)
   - officer_id_hash: Hash of officer_id
   - description_length: Length of description text
   - has_context: Whether context field is present (1/0)
   - timestamp_hour: Hour of day (0-23)
   - timestamp_day: Day of week (0-6)
   (9 numeric features)

Total: 16 features per deviation
```

**Output:** Numerical matrix (129 rows × 16 columns)

---

#### STEP 2: Clustering (DBSCAN)

**Purpose:** Group similar deviations together

**Algorithm:** DBSCAN (Density-Based Spatial Clustering)
- **Why DBSCAN?** Automatically determines number of clusters, handles outliers well
- **Parameters:**
  - `eps = 0.25`: Maximum distance between points in same cluster
  - `min_samples = 2`: Minimum points to form a cluster (adaptive based on data size)

**Process:**
```python
1. Calculate pairwise distances between all deviations (using feature vectors)
2. For each deviation:
   - Count how many neighbors are within eps distance
   - If neighbors >= min_samples, start a cluster
3. Expand cluster by adding neighbors of neighbors
4. Mark isolated points as noise (outliers)
```

**Output:**
```python
{
    "clusters": 21,
    "noise_points": 51,  # Outliers/anomalies
    "cluster_assignments": [0, 0, 1, -1, 2, ...],  # -1 = noise
    "cluster_sizes": [8, 6, 12, 4, ...]
}
```

**Example Clusters:**
- **Cluster 0:** All LTV breach deviations for residential properties (42 deviations)
- **Cluster 1:** Missing approval deviations by Branch Managers (15 deviations)
- **Cluster 5:** Self-employed EMI violations (3 deviations)
- **Noise:** Unique/rare deviations (51 deviations)

---

#### STEP 3: Anomaly Detection (Isolation Forest)

**Purpose:** Identify unusual/rare deviations that stand out

**Algorithm:** Isolation Forest
- **Why Isolation Forest?** Fast, works well with high-dimensional data, no assumptions about data distribution
- **Parameters:**
  - `contamination = 0.1`: Expect 10% of data to be anomalies
  - `n_estimators = 100`: Use 100 decision trees

**Process:**
```python
1. Build 100 random decision trees
2. For each deviation:
   - Measure how many splits needed to isolate it
   - Anomalies are isolated quickly (few splits)
   - Normal points need many splits
3. Calculate anomaly score (0 to 1)
4. Mark top 10% as anomalies
```

**Output:**
```python
{
    "anomalies_detected": 13,
    "anomaly_percentage": 10.1,
    "anomaly_scores": [-0.42, 0.15, 0.38, ...],  # Negative = anomaly
    "is_anomaly": [False, False, True, ...]
}
```

**Example Anomalies:**
- Case SPL-015 with 5 different deviation types (unusual)
- OFF003 with only 1 deviation total (outlier officer)
- Rare deviation type: expired_offer (only 1 occurrence)

---

#### STEP 4: Intelligent Sampling

**Purpose:** Select most important deviations for LLM analysis

**Strategy:**
```python
1. Include ALL anomalies (13 deviations)
   - Reason: Anomalies are by definition important/unusual

2. Include cluster representatives (56 deviations)
   - For each cluster, select:
     a) Centroid: Deviation closest to cluster center (most representative)
     b) Boundary points: Deviations at cluster edges (diversity)

3. Total: 69 out of 129 deviations (1.9x compression)
```

**Output:**
```python
{
    "original_count": 129,
    "selected_count": 69,
    "compression_ratio": 1.9,
    "selection_breakdown": {
        "anomalies": 13,           # ALL anomalies included
        "cluster_representatives": 56  # Most important from each cluster
    }
}
```

**Why This Works:**
- **No information loss:** LLM sees all important patterns (anomalies + representatives)
- **Faster analysis:** 53% fewer deviations to analyze
- **Better focus:** LLM doesn't get overwhelmed by repetitive patterns

---

## AI Pattern Recognition

**Location:** `ai-service/app/services/deviation/notes_analyzer.py`

### Purpose

Use Claude AI to identify **behavioral patterns**, **hidden rules**, and **systemic issues** that statistical/ML analysis cannot detect.

### Input to Claude

```
┌─────────────────────────────────────────┐
│ 69 Representative Deviations (sampled)  │
│ + Statistical Context                   │
│ + ML Context (clusters, anomalies)      │
│ + SOP Rules                             │
└──────────────────────────────────────────┘
```

**Prompt Structure:**
```
You are analyzing loan workflow deviations.

STATISTICAL CONTEXT:
- Total deviations: 129
- Severity: 76% high, 24% critical
- Top deviation types: ltv_breach (42), customer_exposure (32)
- Peak hours: 10:00, 11:00 (business hours)

ML INSIGHTS:
- 21 clusters detected (grouped similar deviations)
- 13 anomalies flagged (unusual cases)
- Cluster 0: LTV breaches on residential properties (42 cases)

DEVIATIONS TO ANALYZE (69 samples):
[
  {
    "case_id": "SPL-003",
    "deviation_type": "emi_to_income_breach",
    "description": "EMI 52% exceeds 50% for Self-Employed",
    "is_anomaly": false,
    "cluster_id": 5
  },
  ...
]

TASK:
1. Identify behavioral patterns (officer habits, shortcuts)
2. Discover hidden rules (informal practices not in SOP)
3. Find systemic issues (root causes, process gaps)
4. Provide actionable recommendations
```

### Claude's Analysis Process

Claude performs:

1. **Cross-Case Pattern Analysis**
   - "All OFF001's LTV breaches involve residential properties"
   - "Self-employed customers consistently exceed EMI limits"

2. **Temporal Pattern Recognition**
   - "Missing approvals spike on Fridays (end-of-week rush)"
   - "Valuation staleness increases after 30+ day gaps"

3. **Officer Behavior Analysis**
   - "OFF001 frequently skips collateral verification step"
   - "OFF002 always documents exceptions, others don't"

4. **Root Cause Identification**
   - "High exposure violations due to lack of real-time limit checking"
   - "Missing approvals caused by approval workflow not enforced in system"

5. **Hidden Rule Discovery**
   - "Officers approve 500k-600k loans without escalation (informal threshold)"
   - "Commercial property LTV often exceeds limit by exactly 5% (accepted practice?)"

---

### Output Generated

#### 1. Behavioral Patterns (10 patterns)
```json
[
  {
    "pattern": "Officer OFF001 frequently approves loans with LTV ratios exceeding 75%",
    "affected_cases": ["SPL-001", "SPL-005", "SPL-009"],
    "frequency": "18 out of 20 cases",
    "risk_level": "high",
    "recommendation": "Implement hard stop at 75% LTV or require exception approval"
  }
]
```

#### 2. Hidden Rules (8 rules)
```json
[
  {
    "informal_rule": "Loans between 500k-600k approved by Branch Manager without Regional approval",
    "sop_says": "Branch Manager can approve only up to 500k",
    "actual_practice": "Branch Managers routinely approve up to 600k",
    "cases": ["SPL-008", "SPL-014"],
    "risk": "Authority delegation violation, audit risk"
  }
]
```

#### 3. Systemic Issues
```json
[
  {
    "issue": "No real-time customer exposure limit checking",
    "evidence": "32 cases exceeded exposure limit, all discovered post-facto",
    "root_cause": "System calculates exposure only during monthly reports",
    "impact": "High credit risk, regulatory violations",
    "fix_priority": "critical"
  }
]
```

#### 4. Risk Insights (10 insights)
```json
[
  "42 LTV breaches (32.6% of deviations) indicate weak collateral validation controls",
  "All 5 EMI violations involve self-employed customers - affordability assessment gap",
  "Missing approval deviations concentrated on Fridays - workflow bottleneck"
]
```

#### 5. Recommendations (20 recommendations)
```json
[
  {
    "priority": "high",
    "category": "process",
    "recommendation": "Implement hard LTV limits in loan origination system (75% residential, 65% commercial)",
    "expected_impact": "Eliminate 42 LTV breach deviations",
    "effort": "medium"
  },
  {
    "priority": "critical",
    "category": "technology",
    "recommendation": "Add real-time customer exposure limit checking during application stage",
    "expected_impact": "Prevent 32 exposure limit violations",
    "effort": "high"
  }
]
```

---

## Frontend Architecture

**Technology Stack:**
- **Framework:** React 18 with Vite
- **Styling:** Tailwind CSS
- **Charts:** Recharts library
- **State Management:** React hooks (useState, useEffect)
- **API Communication:** Fetch API

### Component Structure

```
┌─────────────────────────────────────────────────────────────┐
│                         App.jsx                             │
│                    (Main Application)                       │
└────────────────────────────┬────────────────────────────────┘
                             │
            ┌────────────────┴────────────────┐
            │                                  │
            ▼                                  ▼
┌─────────────────────┐          ┌─────────────────────────┐
│  AnalyzeButton.jsx  │          │  ResultsViewer.jsx      │
│  (Input Panel)      │          │  (Output Panel)         │
│                     │          │                         │
│  • Upload SOP       │          │  • Overview Stats       │
│  • Upload CSV       │          │  • Deviation List       │
│  • Run Analysis     │          │  • Charts & Graphs      │
│  • Progress Bar     │          │  • Pattern Analysis     │
└─────────────────────┘          └─────────────────────────┘
            │                                  │
            │                                  │
            └──────────────┬───────────────────┘
                           │
                           ▼
               ┌────────────────────────┐
               │  ModernLoading.jsx     │
               │  (Loading Animation)   │
               └────────────────────────┘
```

### User Flow

```
┌──────────────┐
│ User Opens   │
│ Application  │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────┐
│ STEP 1: Upload SOP Document         │
│ • Click "Upload SOP"                │
│ • Select .txt file                  │
│ • System extracts rules with Claude │
│ • Shows success message             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ STEP 2: Upload Workflow Logs        │
│ • Click "Upload Workflow Logs"      │
│ • Select .csv file                  │
│ • System validates format           │
│ • Shows row count                   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ STEP 3: Run Analysis                │
│ • Click "Analyze Deviations"        │
│ • Progress bar shows:               │
│   - Data Cleaning (5s)              │
│   - Deviation Detection (3s)        │
│   - Pattern Analysis (3min)         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ STEP 4: View Results                │
│ • Overview Tab: Key metrics         │
│ • Deviations Tab: Full list         │
│ • Analytics Tab: Charts             │
│ • Patterns Tab: AI insights         │
│ • Download JSON report              │
└─────────────────────────────────────┘
```

### Results Viewer Layout

```
┌─────────────────────────────────────────────────────────────┐
│                        HEADER                                │
│  [Overview] [Deviations] [Analytics] [Patterns]  [Download] │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    OVERVIEW TAB                              │
│                                                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌─────────┐  │
│  │ Total      │ │ Cases with │ │ Severity   │ │ Data    │  │
│  │ Deviations │ │ Issues     │ │ Score      │ │ Quality │  │
│  │    129     │ │     50     │ │  90.7/100  │ │ 85/100  │  │
│  └────────────┘ └────────────┘ └────────────┘ └─────────┘  │
│                                                              │
│  Top Deviation Types:                                       │
│  ┌──────────────────────────────────────┐                  │
│  │ ltv_breach                 42 █████  │                  │
│  │ customer_exposure_limit    32 ████   │                  │
│  │ missing_approval           31 ████   │                  │
│  └──────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   DEVIATIONS TAB                             │
│                                                              │
│  [Filter: All Types ▼] [Severity: All ▼] [Officer: All ▼]  │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ SPL-003 | emi_to_income_breach | HIGH               │   │
│  │ EMI-to-Income ratio 52.00% exceeds limit 50.00%     │   │
│  │ Officer: OFF001 | Date: 2025-01-06                  │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ SPL-006 | ltv_breach | HIGH                         │   │
│  │ LTV ratio 78.50% exceeds limit 75.00%               │   │
│  │ Officer: OFF001 | Date: 2025-01-07                  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   ANALYTICS TAB                              │
│                                                              │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │ Hourly Working Trend │  │ Daily Working Trend  │        │
│  │  (Line Chart)        │  │  (Line Chart)        │        │
│  └──────────────────────┘  └──────────────────────┘        │
│                                                              │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │ Officer Deviations   │  │ Deviation Type Dist. │        │
│  │  (Stacked Bar)       │  │  (Pie Chart)         │        │
│  └──────────────────────┘  └──────────────────────┘        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   PATTERNS TAB                               │
│                                                              │
│  📊 Behavioral Patterns (10)                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ OFF001 frequently approves loans with LTV > 75%     │   │
│  │ Risk: High | Frequency: 18/20 cases                 │   │
│  │ Recommendation: Implement hard LTV limit            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  🔍 Hidden Rules (8)                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Branch Managers approve 500k-600k without escalation│   │
│  │ SOP Says: Max 500k for Branch Manager              │   │
│  │ Actual: Routinely approve up to 600k               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  💡 Recommendations (20)                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ [HIGH] Implement real-time exposure limit checking  │   │
│  │ Impact: Prevent 32 violations | Effort: Medium     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow

```
┌───────────────────────────────────────────────────────────────────────┐
│                         CLIENT (Browser)                              │
│                                                                       │
│  User → Upload SOP & CSV → Click "Analyze" → View Results          │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ HTTP POST /ai/sop/upload
                             │ (SOP text document)
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND (Node.js)                               │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ POST /api/sop/upload                                         │  │
│  │ • Validate SOP format                                        │  │
│  │ • Forward to AI Service                                      │  │
│  └────────────────────────┬─────────────────────────────────────┘  │
│                           │                                         │
│                           │ Forward to AI Service                   │
│                           ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Store SOP in Database                                        │  │
│  │ (SQLite database)                                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ HTTP POST (forward)
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AI SERVICE (FastAPI/Python)                       │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ POST /ai/sop/upload                                          │  │
│  │ • Extract rules using Claude LLM                             │  │
│  │ • Parse conditional logic                                    │  │
│  │ • Return structured rules                                    │  │
│  └────────────────────────┬─────────────────────────────────────┘  │
│                           │                                         │
│                           │ Call Claude API                         │
│                           ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ CLAUDE API (Anthropic)                                       │  │
│  │ • Analyze SOP text                                           │  │
│  │ • Extract structured rules                                   │  │
│  │ • Return JSON with rules                                     │  │
│  └────────────────────────┬─────────────────────────────────────┘  │
│                           │                                         │
│                           │ Rules JSON                              │
│                           ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Return rules to Backend                                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Rules JSON response
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND (Node.js)                               │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Store Rules in Database                                      │  │
│  │ (SQLite: sops.rules array)                                   │  │
│  └────────────────────────┬─────────────────────────────────────┘  │
│                           │                                         │
│                           │ Success response                        │
│                           ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Return to Client                                             │  │
│  │ "SOP uploaded successfully, 61 rules extracted"              │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                              │
│  Display success message                                            │
└─────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════
                        WORKFLOW LOGS UPLOAD
═══════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                              │
│  User → Upload CSV file                                             │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ HTTP POST /api/workflow/upload
                             │ (CSV file, multipart/form-data)
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND (Node.js)                               │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ POST /api/workflow/upload                                    │  │
│  │ • Parse CSV file                                             │  │
│  │ • Validate format (has required columns)                     │  │
│  │ • Store in Database                                          │  │
│  └────────────────────────┬─────────────────────────────────────┘  │
│                           │                                         │
│                           │ Store in DB                             │
│                           ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ SQLite: workflow_logs table                                  │  │
│  │ • Insert 434 log entries                                     │  │
│  └────────────────────────┬─────────────────────────────────────┘  │
│                           │                                         │
│                           │ Success                                 │
│                           ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Return to Client                                             │  │
│  │ "434 workflow logs uploaded successfully"                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                              │
│  Display success message                                            │
└─────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════
                       DEVIATION ANALYSIS
═══════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                              │
│  User → Click "Analyze Deviations"                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ HTTP POST /api/workflow/analyze
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND (Node.js)                               │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ POST /api/workflow/analyze                                   │  │
│  │ • Fetch SOP rules from Database                              │  │
│  │ • Fetch workflow logs from Database                          │  │
│  │ • Forward to AI Service                                      │  │
│  └────────────────────────┬─────────────────────────────────────┘  │
│                           │                                         │
│                           │ Forward data                            │
│                           ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ POST to AI Service: /ai/deviation/detect                     │  │
│  │ Body: { logs: [...], rules: [...] }                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ HTTP POST
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AI SERVICE (FastAPI/Python)                       │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ POST /ai/deviation/detect                                    │  │
│  │                                                              │  │
│  │ LAYER 1: Data Cleaning (5s)                                 │  │
│  │ • Remove duplicates                                          │  │
│  │ • Validate types                                             │  │
│  │ • Handle missing values                                      │  │
│  │ • Normalize text                                             │  │
│  │ • Map CSV fields to system fields                            │  │
│  │ • Analyze missing fields                                     │  │
│  └────────────────────────┬─────────────────────────────────────┘  │
│                           │ Clean logs                              │
│                           ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ LAYER 2: Deviation Detection (3s)                           │  │
│  │ Run 13 checkers in sequence:                                │  │
│  │ 1. DataQualityChecker                                        │  │
│  │ 2. EligibilityChecker                                        │  │
│  │ 3. CollateralChecker                                         │  │
│  │ 4. KYCChecker                                                │  │
│  │ 5. DocumentationChecker                                      │  │
│  │ 6. DisbursementChecker                                       │  │
│  │ 7. CollectionChecker (RegulatoryAggregator)                  │  │
│  │ 8. RegulatoryChecker                                         │  │
│  │ 9. SequenceChecker                                           │  │
│  │ 10. RuleValidator (approval hierarchy)                       │  │
│  │ 11. TemporalRuleEvaluator                                    │  │
│  │ 12. ConditionalRuleEvaluator                                 │  │
│  │ 13. NotesAnalyzer (initial check)                            │  │
│  │                                                              │  │
│  │ Result: 129 deviations detected                              │  │
│  └────────────────────────┬─────────────────────────────────────┘  │
│                           │ Deviations list                         │
│                           ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Return deviations to Backend                                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Deviations JSON
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND (Node.js)                               │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ POST to AI Service: /ai/deviation/analyze-patterns           │  │
│  │ Body: { deviations: [...], workflow_logs: [...] }           │  │
│  └────────────────────────┬─────────────────────────────────────┘  │
│                           │                                         │
│                           │ Forward for pattern analysis            │
│                           ▼                                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ HTTP POST
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AI SERVICE (FastAPI/Python)                       │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ POST /ai/deviation/analyze-patterns                          │  │
│  │                                                              │  │
│  │ LAYER 3: Statistical Analysis (5s)                          │  │
│  │ • Calculate overview metrics                                 │  │
│  │ • Severity distribution                                      │  │
│  │ • Deviation type distribution                                │  │
│  │ • Temporal patterns (using workflow log timestamps)          │  │
│  │ • Officer statistics                                         │  │
│  │ • Correlation analysis                                       │  │
│  │ • Lift & odds ratios                                         │  │
│  │ • Time-series analysis                                       │  │
│  │ • Control charts                                             │  │
│  │ • Change-point detection                                     │  │
│  └────────────────────────┬─────────────────────────────────────┘  │
│                           │ Statistical report                      │
│                           ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ LAYER 4: Machine Learning (3s)                               │  │
│  │ • Feature engineering (16 features)                          │  │
│  │ • Clustering with DBSCAN (21 clusters)                       │  │
│  │ • Anomaly detection (13 anomalies)                           │  │
│  │ • Intelligent sampling (69 samples)                          │  │
│  └────────────────────────┬─────────────────────────────────────┘  │
│                           │ ML insights                             │
│                           ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ LAYER 5: AI Pattern Recognition (3 min)                     │  │
│  │ • Build comprehensive prompt                                 │  │
│  │ • Include statistical context                                │  │
│  │ • Include ML context                                         │  │
│  │ • Include 69 sampled deviations                              │  │
│  │ • Send to Claude API                                         │  │
│  └────────────────────────┬─────────────────────────────────────┘  │
│                           │                                         │
│                           │ Call Claude API                         │
│                           ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ CLAUDE API (Anthropic)                                       │  │
│  │ • Analyze 69 deviations + context                            │  │
│  │ • Identify behavioral patterns                               │  │
│  │ • Discover hidden rules                                      │  │
│  │ • Find systemic issues                                       │  │
│  │ • Generate recommendations                                   │  │
│  └────────────────────────┬─────────────────────────────────────┘  │
│                           │                                         │
│                           │ Pattern analysis JSON                   │
│                           ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Return complete analysis to Backend                          │  │
│  │ • Deviations: 129                                            │  │
│  │ • Statistical analysis                                       │  │
│  │ • ML insights                                                │  │
│  │ • Behavioral patterns: 10                                    │  │
│  │ • Hidden rules: 8                                            │  │
│  │ • Recommendations: 20                                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Complete results JSON
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND (Node.js)                               │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Store results in Database                                    │  │
│  │ • Deviations table                                           │  │
│  │ • Analysis results table                                     │  │
│  └────────────────────────┬─────────────────────────────────────┘  │
│                           │                                         │
│                           │ Return to Client                        │
│                           ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ HTTP Response with complete analysis                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                              │
│  • Display deviations list                                          │
│  • Render charts (temporal, officer, type distribution)             │
│  • Show behavioral patterns                                         │
│  • Show hidden rules                                                │
│  • Show recommendations                                             │
│  • Enable download as JSON                                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## System Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                                │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                   React Frontend (Port 5173)                 │    │
│  │                                                              │    │
│  │  Components:                                                 │    │
│  │  • AnalyzeButton.jsx - Upload & trigger analysis            │    │
│  │  • ResultsViewer.jsx - Display results & charts             │    │
│  │  • ModernLoading.jsx - Loading animations                   │    │
│  │                                                              │    │
│  │  Libraries:                                                  │    │
│  │  • Recharts - Data visualization                            │    │
│  │  • Tailwind CSS - Styling                                   │    │
│  │  • Lucide React - Icons                                     │    │
│  └───────────────────────────┬──────────────────────────────────┘    │
└───────────────────────────────┼───────────────────────────────────────┘
                                │
                                │ HTTP REST API (Port 3000)
                                │
┌───────────────────────────────▼───────────────────────────────────────┐
│                       BACKEND SERVICE                                 │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                Node.js + Express (Port 3000)                 │    │
│  │                                                              │    │
│  │  Routes:                                                     │    │
│  │  • POST /api/sop/upload - Upload SOP documents              │    │
│  │  • GET  /api/sop/:id - Retrieve SOP by ID                   │    │
│  │  • POST /api/workflow/upload - Upload workflow CSV          │    │
│  │  • POST /api/workflow/analyze - Trigger deviation analysis  │    │
│  │  • GET  /api/workflow/results/:id - Retrieve analysis       │    │
│  │                                                              │    │
│  │  Controllers:                                                │    │
│  │  • sop.controller.js - SOP management                       │    │
│  │  • workflow.controller.js - Workflow analysis               │    │
│  │                                                              │    │
│  │  Services:                                                   │    │
│  │  • Forwards requests to AI Service                          │    │
│  │  • Manages Database connections                             │    │
│  │  • Handles file uploads (multer)                            │    │
│  └───────────────────────────┬──────────────────────────────────┘    │
└───────────────────────────────┼───────────────────────────────────────┘
                                │
                        ┌───────┴────────┐
                        │                │
                        ▼                ▼
        ┌─────────────────────┐   ┌─────────────────────┐
        │  SQLite Database    │   │ AI Service (8000)   │
        │                     │   │                     │
        │  Tables:            │   │  (Forward requests) │
        │  • sops             │   └─────────────────────┘
        │  • workflow_logs    │
        │  • deviations       │
        │  • analysis_results │
        └─────────────────────┘

┌───────────────────────────────────────────────────────────────────────┐
│                         AI SERVICE                                    │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                FastAPI + Python (Port 8000)                  │    │
│  │                                                              │    │
│  │  Endpoints:                                                  │    │
│  │  • POST /ai/sop/upload - Extract rules from SOP             │    │
│  │  • POST /ai/deviation/detect - Detect deviations            │    │
│  │  • POST /ai/deviation/analyze-patterns - Pattern analysis   │    │
│  │                                                              │    │
│  │  Routers:                                                    │    │
│  │  • deviation_detector.py - Main analysis endpoints          │    │
│  │                                                              │    │
│  │  Services:                                                   │    │
│  │  ┌───────────────────────────────────────────────────┐      │    │
│  │  │ Data Processing (app/services/data/)              │      │    │
│  │  │ • workflow_log_cleaner.py                         │      │    │
│  │  │ • missing_field_analyzer.py                       │      │    │
│  │  │ • statistical_analyzer.py                         │      │    │
│  │  │ • advanced_statistics.py                          │      │    │
│  │  └───────────────────────────────────────────────────┘      │    │
│  │  ┌───────────────────────────────────────────────────┐      │    │
│  │  │ Deviation Detection (app/services/deviation/)     │      │    │
│  │  │ • data_quality_checker.py                         │      │    │
│  │  │ • eligibility_checker.py                          │      │    │
│  │  │ • collateral_checker.py                           │      │    │
│  │  │ • kyc_checker.py                                  │      │    │
│  │  │ • documentation_checker.py                        │      │    │
│  │  │ • disbursement_checker.py                         │      │    │
│  │  │ • collection_checker.py                           │      │    │
│  │  │ • regulatory_checker.py                           │      │    │
│  │  │ • sequence_checker.py                             │      │    │
│  │  │ • rule_validator.py                               │      │    │
│  │  │ • temporal_rule_evaluator.py                      │      │    │
│  │  │ • conditional_rule_evaluator.py                   │      │    │
│  │  │ • notes_analyzer.py                               │      │    │
│  │  └───────────────────────────────────────────────────┘      │    │
│  │  ┌───────────────────────────────────────────────────┐      │    │
│  │  │ Machine Learning (app/services/ml/)               │      │    │
│  │  │ • ml_pipeline.py                                  │      │    │
│  │  │ • feature_engineer.py                             │      │    │
│  │  │ • clustering.py (DBSCAN)                          │      │    │
│  │  │ • anomaly_detector.py (Isolation Forest)          │      │    │
│  │  │ • intelligent_sampler.py                          │      │    │
│  │  └───────────────────────────────────────────────────┘      │    │
│  │  ┌───────────────────────────────────────────────────┐      │    │
│  │  │ Claude Integration (app/services/claude/)         │      │    │
│  │  │ • client.py - API client                          │      │    │
│  │  │ • prompts.py - Prompt templates                   │      │    │
│  │  └───────────────────────────────────────────────────┘      │    │
│  │  ┌───────────────────────────────────────────────────┐      │    │
│  │  │ NLP Services (app/services/nlp/)                  │      │    │
│  │  │ • llm_rule_parser.py - SOP rule extraction        │      │    │
│  │  └───────────────────────────────────────────────────┘      │    │
│  └─────────────────────────┬──────────────────────────────────┘    │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
                            │ HTTPS API Calls
                            ▼
        ┌───────────────────────────────────────┐
        │   Claude API (Anthropic)              │
        │   api.anthropic.com                   │
        │                                       │
        │   Model: claude-sonnet-4-5            │
        │   • Rule extraction from SOPs         │
        │   • Pattern analysis on deviations    │
        └───────────────────────────────────────┘
```

### Component Communication

```
Frontend (React)
    ↕ HTTP REST (JSON)
Backend (Node.js)
    ↕ HTTP REST (JSON)
AI Service (FastAPI)
    ↕ HTTPS API (JSON)
Claude API (Anthropic)

Backend → SQLite Database
AI Service → Claude API
```

### Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React 18 + Vite | User interface |
| Frontend | Tailwind CSS | Styling |
| Frontend | Recharts | Data visualization |
| Backend | Node.js + Express | API server |
| Backend | SQLite | Data persistence |
| AI Service | Python + FastAPI | ML & AI processing |
| AI Service | scikit-learn | Machine learning |
| AI Service | pandas, numpy | Data processing |
| AI Service | Claude API | LLM for rule extraction & pattern analysis |

---

## Installation & Setup

### Prerequisites

- **Node.js:** v18+ (for backend and frontend)
- **Python:** v3.9+ (for AI service)
- **SQLite:** Included with Node.js
- **Anthropic API Key:** Required for Claude integration

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd vs_demo
```

### Step 2: Install Backend Dependencies

```bash
cd backend
npm install
```

**Dependencies installed:**
- express, cors, dotenv
- sequelize (SQLite ORM)
- multer (file uploads)
- axios (HTTP client)

### Step 3: Install Frontend Dependencies

```bash
cd ../frontend
npm install
```

**Dependencies installed:**
- react, react-dom
- recharts (charts)
- tailwindcss (styling)
- lucide-react (icons)

### Step 4: Install AI Service Dependencies

```bash
cd ../ai-service
pip install -r requirements.txt
```

**Dependencies installed:**
- fastapi, uvicorn (web server)
- anthropic (Claude API client)
- pandas, numpy (data processing)
- scikit-learn (machine learning)
- pydantic (data validation)

### Step 5: Configure Environment Variables

#### Backend (.env)
```bash
cd backend
cp .env.example .env
```

Edit `backend/.env`:
```env
PORT=3000
AI_SERVICE_URL=http://localhost:8000
NODE_ENV=development
```

#### AI Service (.env)
```bash
cd ../ai-service
cp .env.example .env
```

Edit `ai-service/.env`:
```env
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
PORT=8000
```

**Get Anthropic API Key:**
1. Visit https://console.anthropic.com/
2. Sign up / Log in
3. Go to API Keys section
4. Create new key
5. Copy key to `.env` file

### Step 6: Start Services

**Terminal 1 - Backend:**
```bash
cd backend
npm start
```
Output: `Server running on http://localhost:3000`

**Terminal 2 - AI Service:**
```bash
cd ai-service
python -m uvicorn app.main:app --reload --port 8000
```
Output: `Uvicorn running on http://0.0.0.0:8000`

**Terminal 3 - Frontend:**
```bash
cd frontend
npm run dev
```
Output: `Local: http://localhost:5173`

### Step 7: Verify Installation

1. Open browser: http://localhost:5173
2. You should see the application interface
3. Check browser console for errors (F12)

---

## Configuration

### Backend Configuration

**File:** `backend/src/config/index.js`

```javascript
module.exports = {
  port: process.env.PORT || 3000,
  aiService: {
    url: process.env.AI_SERVICE_URL || 'http://localhost:8000',
    timeout: 600000  // 10 minutes (for pattern analysis)
  },
  upload: {
    maxFileSize: 50 * 1024 * 1024,  // 50MB
    allowedMimeTypes: ['text/plain', 'text/csv', 'application/pdf']
  }
}
```

### AI Service Configuration

**File:** `ai-service/app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Claude API
    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-4-5-20250929"

    # ML Parameters
    dbscan_eps: float = 0.25
    dbscan_min_samples: int = 2
    isolation_forest_contamination: float = 0.1

    # Data Cleaning
    max_valuation_age_days: int = 90
    duplicate_threshold: float = 0.9

    # Sampling
    max_samples_for_llm: int = 75

    class Config:
        env_file = ".env"

settings = Settings()
```

### Customizing Deviation Detection

**File:** `ai-service/app/services/deviation/eligibility_checker.py`

Modify thresholds:
```python
# Line 62-65: Age limits
min_age = 21  # Change to 18 for broader eligibility
max_age = 65  # Change to 70 for senior customers

# Line 155-172: EMI thresholds
if 'salaried' in employment_type:
    conditional_threshold = 0.55  # Change to 0.60 for relaxed policy
elif 'self' in employment_type:
    conditional_threshold = 0.50  # Change to 0.45 for stricter policy
```

### Customizing ML Parameters

**File:** `ai-service/app/services/ml/clustering.py`

Modify clustering sensitivity:
```python
# Line 45-46: DBSCAN parameters
eps = 0.25  # Increase for fewer, larger clusters (0.3-0.4)
            # Decrease for more, smaller clusters (0.15-0.2)

min_samples = 2  # Increase for stricter cluster formation (3-5)
```

**File:** `ai-service/app/services/ml/anomaly_detector.py`

Modify anomaly sensitivity:
```python
# Line 32: Contamination rate
contamination = 0.1  # Increase to flag more anomalies (0.15-0.2)
                     # Decrease to flag fewer anomalies (0.05-0.08)
```

### Adding New Deviation Types

1. **Create new checker:**
   - File: `ai-service/app/services/deviation/my_custom_checker.py`
   - Implement detection logic

2. **Register checker:**
   - File: `ai-service/app/routers/deviation_detector.py`
   - Add import: `from app.services.deviation.my_custom_checker import MyCustomChecker`
   - Add to detection pipeline (line 150): `custom_deviations = MyCustomChecker.check_custom(logs, rules)`
   - Append to deviations list: `all_deviations.extend(custom_deviations)`

---

## Troubleshooting

### Common Issues

#### Issue 1: "ANTHROPIC_API_KEY not found"
**Solution:**
```bash
cd ai-service
echo 'ANTHROPIC_API_KEY=sk-ant-your-key-here' >> .env
```

#### Issue 2: Database connection failed
**Solution:**
```bash
# SQLite database is auto-created
# Check if backend/database.sqlite exists
# If corrupted, delete it and restart backend
rm backend/database.sqlite
```

#### Issue 3: Port already in use
**Solution:**
```bash
# Find process using port 3000
lsof -i :3000  # Mac/Linux
netstat -ano | findstr :3000  # Windows

# Kill process
kill -9 <PID>  # Mac/Linux
taskkill /PID <PID> /F  # Windows
```

#### Issue 4: Frontend can't reach backend
**Check CORS configuration:**
```javascript
// backend/src/index.js
app.use(cors({
  origin: 'http://localhost:5173',  // Must match frontend URL
  credentials: true
}));
```

#### Issue 5: AI Service timeout during pattern analysis
**Increase timeout:**
```javascript
// backend/src/config/index.js
aiService: {
  timeout: 900000  // Increase to 15 minutes
}
```

---

## System Monitoring

### Performance Metrics

**Expected processing times:**
- SOP upload: 2-10 seconds (depends on SOP size)
- Workflow upload: <1 second (434 logs)
- Data cleaning: 5 seconds
- Deviation detection: 3 seconds (13 checkers)
- Statistical analysis: 5 seconds
- ML processing: 3 seconds
- Pattern analysis: 3 minutes (Claude API call)
- **Total analysis time:** ~3.5 minutes

### Log Locations

**Backend logs:**
```bash
backend/logs/app.log
```

**AI Service logs:**
```bash
ai-service/logs/uvicorn.log
```

**View real-time logs:**
```bash
# Backend
tail -f backend/logs/app.log

# AI Service
tail -f ai-service/logs/uvicorn.log
```

---

## License

This project is proprietary and confidential.

---

## Support

For issues, questions, or feature requests:
- Check troubleshooting section above
- Review logs for error details
- Verify environment variables are set correctly
- Ensure all services are running

---

**Document Version:** 2.0
**Last Updated:** 2026-01-15
**System Version:** 1.0.0
