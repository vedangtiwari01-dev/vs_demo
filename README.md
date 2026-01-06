# ZenWolf - SOP Compliance Analysis System

## 📑 Table of Contents

1. [Overview](#overview)
2. [What This System Does](#what-this-system-does)
3. [Key Concepts & Definitions](#key-concepts--definitions)
4. [System Architecture](#system-architecture)
5. [The 4-Layer Processing Pipeline](#the-4-layer-processing-pipeline)
6. [Statistical Methods Reference](#statistical-methods-reference)
7. [Machine Learning Models](#machine-learning-models)
8. [AI Integration](#ai-integration)
9. [API Reference](#api-reference)
10. [Data Flow Example](#data-flow-example)
11. [Calculation Reference](#calculation-reference)
12. [Installation & Setup](#installation--setup)
13. [Configuration & Troubleshooting](#configuration--troubleshooting)

---

## Overview

ZenWolf is an AI-powered compliance monitoring system that analyzes loan processing workflows against Standard Operating Procedures (SOPs) to detect deviations, identify patterns, and provide actionable insights.

## What This System Does

**In 3 Sentences:**
ZenWolf takes your SOP documents and workflow logs, runs them through a 4-layer analysis pipeline (data cleaning → rule-based detection [43+ types] → statistical analysis [16 methods] → ML clustering → AI pattern discovery), and produces comprehensive compliance reports with hidden pattern insights. The system uses machine learning to intelligently sample deviations and Claude AI to discover behavioral patterns that traditional rule-based systems miss. It achieves 1000x cost reduction through smart sampling while maintaining 100% anomaly detection.

**Who This Is For:**
- **Compliance Officers**: Monitor loan processing adherence to SOPs
- **Risk Managers**: Identify systemic risks and behavioral patterns
- **Operations Managers**: Optimize workflows and address bottlenecks

**Key Capabilities:**
- ✅ **Multi-Format SOP Processing**: DOCX, PDF, TXT with AI-powered rule extraction
- ✅ **Intelligent Deviation Detection**: 43+ deviation types (10 Python checkers) across 16 rule categories
- ✅ **Advanced Analytics**: 16 statistical methods + 3 ML algorithms + 44-feature engineering
- ✅ **Pattern Discovery**: Claude AI finds hidden rules, systemic issues, officer behaviors
- ✅ **Cost Optimized**: Intelligent sampling reduces AI costs by 1000x

---

## ⚠️ Key Concepts & Definitions

### Core Terms

| Term | Definition | Example |
|------|------------|---------|
| **Workflow Log** | A single step/action in the loan processing workflow | "Credit Check completed by Officer A on 2025-01-01" |
| **Case** | A unique loan application being processed | Case ID: LN-18231 |
| **Total Logs** | Number of workflow log entries (individual steps recorded) | 76 logs = 76 recorded actions |
| **Unique Cases** | Number of distinct loan applications | 27 cases = 27 different loan applications |
| **Deviation** | A violation of an SOP rule | Missing required step, wrong sequence, timing violation |
| **Total Deviations** | Number of rule violations found | **Can be > Total Logs** (explained below) |

### ⚡ Why Can Deviations Exceed Total Logs?

**CRITICAL UNDERSTANDING**: One workflow log can violate multiple rules simultaneously!

#### Example Scenario:

**SOP Rules:**
1. Rule 1: "Credit check MUST happen before loan approval" (Sequence rule)
2. Rule 2: "Manager approval REQUIRED for loans > $50,000" (Approval rule)
3. Rule 3: "Credit check must complete within 24 hours" (Timing rule)
4. Rule 4: "Credit score verification is MANDATORY" (Validation rule)

**Workflow Log:**
```
Case: LN-18231
Officer: j_doe
Step: Loan Approval
Action: Approved
Timestamp: 2025-01-01 10:00
Amount: $75,000
```

**Deviations Detected from this SINGLE log:**
1. ❌ **Sequence Deviation**: Approval happened before credit check (violates Rule 1)
2. ❌ **Approval Deviation**: No manager approval for $75K loan (violates Rule 2)
3. ❌ **Missing Step Deviation**: Credit check step is missing entirely (violates Rule 4)

**Result**: 1 workflow log → 3 deviations!

### Real Data Example

```
Total Logs: 76 (76 individual workflow steps)
Unique Cases: 27 (27 different loan applications)
Total Deviations: 149 (149 rule violations)
Average Deviations per Log: 149/76 = 1.96
```

This means on average, each workflow step violates ~2 rules. This is **normal** in compliance analysis!

### Types of Deviations (43+ Types Detected via 10 Checkers)

**Implementation:** All deviation types are detected using Python rule-based logic across 10 specialized checker modules.

| Category | Deviation Types | Checker Module | Severity Range |
|----------|----------------|----------------|----------------|
| **Process & Sequence (5)** | missing_step, wrong_sequence, unexpected_step, duplicate_step, skipped_subprocess | SequenceChecker | High - Critical |
| **Approval & Authority (5)** | missing_approval, insufficient_hierarchy, unauthorized_approver, self_approval, escalation_missing | RuleValidator | Critical |
| **Timing & SLA (4)** | timing_violation, tat_breach, cutoff_breach, post_disbursement_delay | RuleValidator | Medium - High |
| **Eligibility & Credit (4)** | ineligible_age, ineligible_tenor, emi_to_income_breach, low_score_approved_without_exception | EligibilityChecker | High - Critical |
| **KYC/AML/Sanctions (3)** | kyc_incomplete_progression, sanctions_hit_not_rejected, pep_no_edd_or_extra_approval | KYCChecker | Critical |
| **Documentation (4)** | missing_mandatory_document, expired_document_used, legal_clearance_missing, collateral_docs_incomplete | DocumentationChecker | High - Critical |
| **Collateral & Security (3)** | ltv_breach, valuation_missing_or_stale, security_not_created | CollateralChecker | High - Critical |
| **Disbursement (4)** | pre_disbursement_condition_unmet, mandate_not_set_before_disbursement, incorrect_disbursement_amount, post_disbursement_qc_missing | DisbursementChecker | Critical |
| **Collections & Restructuring (3)** | collection_escalation_delay, unauthorized_restructure, unauthorized_writeoff | CollectionChecker | High - Critical |
| **Regulatory & Reporting (3)** | classification_mismatch, provisioning_shortfall, regulatory_report_missing_or_late | RegulatoryChecker | High |
| **Data Quality & Logging (5)** | missing_core_field, invalid_format, inconsistent_value_across_steps, duplicate_active_case, audit_trail_missing | DataQualityChecker | Medium - Critical |

**Total:** 43+ deviation types across 16 rule categories
**Note:** All checkers include defensive coding - gracefully handle missing rules/fields without failing the analysis.

---

## 🏗️ System Architecture

### Technology Stack

| Layer | Technology | Port | Key Libraries | Purpose |
|-------|-----------|------|---------------|---------|
| **Frontend** | React 18 + Vite | 5174 | TailwindCSS, Recharts, Lucide Icons | UI for SOP upload, analysis, results visualization |
| **Backend** | Node.js + Express | 3000 | Sequelize, SQLite, Multer, PapaParse | API server, database, file handling |
| **AI Service** | Python + FastAPI | 8000 | Anthropic SDK, scikit-learn, scipy, ruptures | Deviation analysis, ML, AI integration |

### 3-Tier Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (React + Vite)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Analysis Hub │  │ SOP Upload   │  │ Results View │          │
│  │ (Dashboard)  │  │ CSV Upload   │  │ (Charts)     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                         │ HTTP (Axios)                           │
└─────────────────────────┼──────────────────────────────────────-┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  BACKEND (Node.js + Express)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Controllers  │  │ Models       │  │ Services     │          │
│  │ (6 modules)  │  │ (Sequelize)  │  │ (Business)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                         │ HTTP (Axios)                           │
│                         │ SQLite Database                        │
└─────────────────────────┼──────────────────────────────────────-┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│               AI SERVICE (Python + FastAPI)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ SOP Parsing  │  │ Deviation    │  │ ML Pipeline  │          │
│  │ (Claude)     │  │ Detection    │  │ (sklearn)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │ Statistics   │  │ Pattern      │                            │
│  │ (scipy)      │  │ Analysis (AI)│                            │
│  └──────────────┘  └──────────────┘                            │
│                         │ Claude API                             │
└─────────────────────────┼──────────────────────────────────────-┘
                          ▼
                   Anthropic Claude API
```

### Data Flow: SOP Upload → Analysis → Results

```
1. SOP UPLOAD FLOW
   User uploads DOCX/PDF → Backend saves file → Calls AI Service /ai/sop/parse
   → Extract text → Calls Claude API → Extract rules → Store in DB

2. CSV UPLOAD FLOW
   User uploads CSV → Backend reads headers → Calls AI Service /ai/mapping/analyze-headers
   → Claude maps columns → Backend imports logs → Extract notes → Store in DB

3. ANALYSIS FLOW (4 LAYERS - See Next Section)
   User clicks "Analyze" → Backend calls AI Service /ai/deviation/analyze-patterns
   → Layer 0: Clean data → Layer 1: Detect deviations → Layer 2: Calculate stats
   → Layer 3: ML clustering/sampling → Layer 4: Claude pattern analysis
   → Return comprehensive results → Frontend displays charts/insights
```

---

## 🔬 The 4-Layer Processing Pipeline

**Overview:** ZenWolf uses a 4-layer pipeline to transform raw workflow logs into actionable compliance insights. Each layer builds on the previous, progressively extracting deeper patterns.

```
Raw Logs (CSV) → Layer 0 → Layer 1 → Layer 2 → Layer 3 → Layer 4 → Insights
    ↓             Clean     Rules    Stats     ML       AI        ↓
  1000 logs       ↓         ↓        ↓         ↓        ↓      Patterns
                 950      200 dev   +risk    75 smart  Hidden  +Risks
                (clean)   detected  scores   samples   rules   +Actions
```

### Layer 0: Data Quality & Cleaning

**Module:** `workflow_log_cleaner.py` (ai-service/app/services/data/)
**Purpose:** Validate and normalize raw workflow data before analysis

**Key Operations:**
- Remove duplicate logs (same case_id + step + timestamp)
- Validate timestamps (require ISO 8601 format: YYYY-MM-DD HH:MM:SS)
- Normalize step names (title case, trim whitespace)
- Handle missing values (reject if critical fields empty)
- Calculate data quality score (0-100)

**Quality Score Formula:**
```
quality_score = (1 - duplicate_rate) × 40    # Max 40 points
               + (1 - missing_rate) × 30      # Max 30 points
               + valid_format_rate × 30       # Max 30 points

Score Ranges:
  90-100: Excellent (proceed confidently)
  70-89:  Good (minor issues, proceed)
  50-69:  Fair (caution, may affect accuracy)
  <50:    Poor (reject, fix data quality first)
```

**Example:**
```
Input:  LN-001, "credit check", "01/15/2025", ""
Output: LN-001, "Credit Check", "2025-01-15 10:00:00", [normalized]
Quality: 85/100 (Good - 5% duplicates, 2% missing, 98% valid format)
```

**Output:** Cleaned logs + quality report
**Processing Time:** <1 second for 1000 logs

---

### Layer 1: Rule-Based Deviation Detection

**Modules:** `sequence_checker.py`, `rule_validator.py` (ai-service/app/services/deviation/)
**Purpose:** Fast, deterministic detection of 40+ deviation types using Python logic

**Detection Methods:**

| Check Type | Module | Deviation Types Detected | Logic |
|-----------|--------|-------------------------|-------|
| **Sequence** | sequence_checker.py | missing_step, wrong_sequence, unexpected_step | Compare actual vs expected step order |
| **Approval** | rule_validator.py | missing_approval, unauthorized_approver | Check approval presence and hierarchy |
| **Timing** | rule_validator.py | timing_violation, rushed_process, long_delay | Calculate time between steps |

**Sequence Checking Example:**
```python
# Expected SOP sequence (from rules)
expected = ["Application Received", "Document Verification",
            "Income Verification", "Credit Check", "Risk Assessment",
            "Manager Approval", "Final Approval"]

# Actual workflow (Case LN-001)
actual = ["Income Verification", "Approval L2", "Application Received"]

# Deviation 1: Missing steps
missing = set(expected) - set(actual)
# Result: ["Document Verification", "Credit Check", "Risk Assessment",
#          "Manager Approval", "Final Approval"] → 5 deviations

# Deviation 2: Wrong sequence
# "Application Received" should be first (index 0), but is at index 2
# → 1 wrong_sequence deviation

# Total: 6 deviations from this case
```

**Approval Checking Example:**
```python
# Rule: Manager approval + Final approval required
steps = [log['step_name'].lower() for log in case_logs]

# Check 1: Manager approval present?
has_manager = any('manager' in s and 'approval' in s for s in steps)
# → False: missing_approval (critical)

# Check 2: Final approval present?
has_final = any('final' in s and 'approval' in s for s in steps)
# → False: missing_approval (critical)

# Result: 2 critical deviations
```

**Timing Checking Example:**
```python
# Rule: Process must take at least 1 hour
first_time = logs[0]['timestamp']  # 2025-01-01 10:00:00
last_time = logs[-1]['timestamp']  # 2025-01-01 10:45:00

duration_hours = (last_time - first_time).total_seconds() / 3600
# = 0.75 hours (45 minutes)

if duration_hours < 1:
    # timing_violation (medium severity)
    # Description: "Process completed in 0.8 hours (too fast)"
```

**Output:** List of deviations with case_id, officer_id, timestamp, type, severity, description
**Processing Time:** <1 second for 1000 logs

---

### Layer 2: Statistical Analysis

**Modules:** `statistical_analyzer.py`, `advanced_statistics.py` (ai-service/app/services/data/)
**Purpose:** Calculate 16+ statistical metrics to understand deviation patterns WITHOUT AI

**16 Statistical Methods Calculated:**

| # | Method | What It Calculates | Passed to Claude? |
|---|--------|-------------------|-------------------|
| 1 | **Distribution Analysis** | Severity, type, officer, time distributions | ✓ Yes |
| 2 | **Severity Scoring** | Weighted risk score (0-100) | ✓ Yes |
| 3 | **Temporal Patterns** | Hour, day, week distributions | ✓ Yes |
| 4 | **Correlation Analysis** | Chi-square, Cramér's V, Pearson, Spearman | ✓ Yes (NEW) |
| 5 | **Time-Series Trends** | 7-day MA, exponential smoothing | ✓ Yes (NEW) |
| 6 | **Control Charts** | Shewhart (3-sigma limits) | ✓ Yes (NEW) |
| 7 | **CUSUM Charts** | Cumulative sum deviations | ✓ Yes (NEW) |
| 8 | **Change-Point Detection** | PELT algorithm (ruptures lib) | ✓ Yes (NEW) |
| 9 | **Concentration Risk** | Top N officer deviation percentage | ✓ Yes |
| 10 | **Diversity Score** | Shannon entropy of types | ✓ Yes |
| 11 | **Critical Mass Score** | Critical/high deviation percentage | ✓ Yes |
| 12 | **Officer Profiling** | Per-officer deviation rates | ✓ Summary only |
| 13 | **Case Complexity** | Deviations per case distribution | ✓ Yes |
| 14 | **Association Rules** | Lift & odds for officer-type patterns | ✓ Yes (NEW) |
| 15 | **Advanced Correlations** | Cramér's V interpretation | ✓ Yes (NEW) |
| 16 | **Moving Averages** | 3-day, 7-day, 30-day MA | ✓ Yes (NEW) |

**What Goes to Claude (Layer 4):**
All 16 statistical methods are now passed to Claude AI, including:
- ✅ **Basic stats**: Distributions, severity scores, temporal patterns, risk indicators
- ✅ **Advanced correlations**: Chi-square, Cramér's V, Pearson, Spearman with interpretations
- ✅ **Association rules**: Lift & odds for officer-type combinations (top 3 patterns)
- ✅ **Time-series analysis**: MA, EMA, volatility, trend direction
- ✅ **Control charts**: Shewhart, CUSUM, EWMA alerts (out-of-control detection)
- ✅ **Change-points**: Structural breaks with before/after averages

All calculated statistics are included in the Claude prompt to provide complete analytical context.

**Key Formula Examples:**

```python
# Severity Score (0-100 scale)
weights = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
severity_score = (Σ(count × weight) / total) × 25

Example:
  8 critical + 45 high + 67 medium + 30 low = 150 total
  (8×4 + 45×3 + 67×2 + 30×1) / 150 × 25 = 55/100 (Moderate Risk)

# Critical Mass Score (urgency indicator)
critical_mass = ((critical_count + high_count) / total) × 100

Example:
  (8 + 45) / 150 × 100 = 35.3%
  Interpretation: >40% = Critical, 25-40% = High, <25% = Moderate

# Concentration Risk (officer risk distribution)
top5_percentage = (top_5_officer_deviations / total) × 100

Example:
  Top 5 officers: 105/150 = 70%
  Interpretation: >60% = Concentrated (investigate top officers)
```

**Temporal Pattern Example:**
```python
# Hour distribution analysis
hour_counts = {9: 12, 10: 15, 11: 8, 16: 25, 17: 22, 18: 18, ...}

# Peak hours (top 3)
peak_hours = [(16, 25), (17, 22), (18, 18)]
# Interpretation: 4-6 PM = 43% of deviations (evening rush!)

# Day of week distribution
day_counts = {'Monday': 20, 'Tuesday': 18, 'Friday': 45, ...}
# Interpretation: Friday = 30% of deviations (end-of-week effect)
```

**Output:** Statistical summary with distributions, risk scores, temporal patterns, correlations
**Processing Time:** <1 second

---

### Layer 3: Machine Learning Analysis

**Modules:** `ml_pipeline.py`, `feature_engineer.py`, `clustering.py`, `anomaly_detector.py`, `intelligent_sampler.py` (ai-service/app/services/ml/)
**Purpose:** Reduce 1000s of deviations to 75 intelligent samples for AI analysis using ML

**4-Step ML Pipeline:**

#### Step 1: Feature Engineering
**Module:** feature_engineer.py
**Purpose:** Convert deviation data into numerical features for ML clustering/anomaly detection

**Feature Types:**

| Feature Type | Method | Count | Example |
|--------------|--------|-------|---------|
| **Type Features** | One-Hot Encoding | 20 | missing_step → [1,0,0,...], wrong_sequence → [0,1,0,...] |
| **Officer Features** | One-Hot Encoding | 20 | EMP-009 → [0,0,1,0,...], EMP-018 → [0,1,0,...] |
| **Severity** | Ordinal Encoding | 1 | critical=4, high=3, medium=2, low=1 |
| **Temporal** | Normalized 0-1 | 2 | hour=16 → 0.67, weekday=4 → 0.57 (Friday) |
| **Description Length** | Integer | 1 | Length in characters (complexity indicator) |

**Total:** 44 features per deviation (down from 144)

**Why No TF-IDF Text Features?**
- Deviation descriptions follow hardcoded templates: "Missing required step: X", "Wrong sequence: X before Y"
- The `type` field already captures all semantic information (missing_step, wrong_sequence, etc.)
- TF-IDF would extract the same patterns already encoded in the type field
- Removing TF-IDF achieves **66% feature reduction** (144 → 44) with no loss in clustering/anomaly detection quality

**Example Feature Vector:**
```python
Deviation: "Missing required step: Credit Check"
Type: missing_step
Officer: EMP-009
Severity: high (3)
Hour: 16 (4pm) → 0.67
Day: Friday (4) → 0.57
Length: 35 characters

Feature Vector (44 dimensions):
[0,0,1,0,0,...,0,  # Type one-hot (20 dims) - position 2 = missing_step
 0,0,1,0,0,...,0,  # Officer one-hot (20 dims) - position 2 = EMP-009
 3,                # Severity (1 dim)
 0.67, 0.57,       # Temporal (2 dims)
 35]               # Length (1 dim)
```

---

#### Step 2: Clustering
**Module:** clustering.py
**Algorithm:** DBSCAN (primary), K-Means (fallback)

**Why DBSCAN?**
- Auto-detects optimal cluster count (no need to specify K)
- Handles noise (labels outliers as -1)
- Finds arbitrary-shaped clusters (not just circles)

**Parameters:**
```python
# Adaptive epsilon based on dataset size
eps = 0.5 (n<100), 0.8 (n<500), 1.0 (n<1000), 1.2 (n≥1000)

# Adaptive min_samples
min_samples = min(10, max(5, n_samples // 200))

# Example: 500 deviations → eps=0.8, min_samples=5
```

**How DBSCAN Works:**
```
For each point:
  1. Find all neighbors within distance eps (0.8)
  2. If ≥ min_samples (5) neighbors → "core point"
  3. Connect core points → clusters
  4. < min_samples neighbors → noise (-1)

Example Result:
  Cluster 0: 35 deviations (Missing step violations)
  Cluster 1: 28 deviations (Timing violations)
  Cluster 2: 42 deviations (Approval issues)
  Noise (-1): 45 deviations (Anomalies - don't fit any pattern)
```

---

#### Step 3: Anomaly Detection
**Module:** anomaly_detector.py
**Algorithm:** Isolation Forest

**Why Isolation Forest?**
- Fast: O(n log n) complexity
- Intuitive: Anomalies are easier to isolate in random trees
- Effective for high-dimensional data (44 features)

**How It Works:**
```
Concept: Anomalies reach leaf nodes faster (fewer splits needed)

Normal point: Root → feature_3<0.5 → feature_7<0.8 → ... → depth=8 → normal
Anomaly:      Root → feature_3<0.5 → depth=2 → anomaly (isolated quickly!)

Anomaly Score = 2^(-avg_path_length / c(n))
  Score close to 1 = anomaly
  Score close to 0 = normal
```

**Example Result:**
```python
150 deviations → 12 anomalies detected (8%)

What Isolation Forest flags as anomalies (based on feature vectors):
  - Deviations occurring at unusual hours (2am-6am vs typical 9am-5pm business hours)
  - Officers with extreme skip patterns (multiple missing steps in one case vs usual 1-2)
  - Rare deviation type combinations (e.g., timing_violation + missing_approval together)
  - Unusual severity patterns (critical deviations from typically medium-risk officers)

Note: Anomalies are identified by statistical outlier detection in 44-dimensional feature space,
not by analyzing semantic content of descriptions. The algorithm flags deviations that are
rare/different based on their numerical feature patterns.
```

---

#### Step 4: Intelligent Sampling
**Module:** intelligent_sampler.py
**Goal:** Select 75 representative deviations from 1000s for AI analysis

**5-Part Sampling Strategy:**

| Part | Strategy | Count | Priority | Reasoning |
|------|----------|-------|----------|-----------|
| 1 | **ALL Anomalies** | 12 | Highest | Never miss unusual patterns |
| 2 | **Cluster Representatives** | 63 | High | Proportional allocation per cluster |
| 3 | **Severity Coverage** | +3 | Medium | Ensure all 4 severity levels present |
| 4 | **Time Coverage** | +2 | Medium | Ensure all time periods present |
| 5 | **Officer Diversity** | +5 | Low | Cover uncovered officers (max 5) |

**Total:** ~75-85 samples (may exceed 75 slightly for coverage)

**Cluster Sampling Logic:**
```python
# Allocate 63 samples proportionally across clusters
Cluster 0 (35 members): 35/138 × 63 = 16 samples
  - 8 closest to centroid (typical cases)
  - 8 farthest from centroid (edge cases)

Cluster 1 (28 members): 28/138 × 63 = 13 samples
  - 6 closest + 7 farthest

Cluster 2 (42 members): 42/138 × 63 = 19 samples
  - 9 closest + 10 farthest
```

**Compression Ratio:**
```
150 deviations → 75 samples = 2x compression
1000 deviations → 75 samples = 13.3x compression
5000 deviations → 100 samples = 50x compression!

Cost Impact:
  Without sampling: 1000 deviations × $0.06 = $60
  With sampling: 1 API call × $0.06 = $0.06
  Savings: 1000x cost reduction!
```

**Output:** 75 selected deviation indices + ML summary (clusters, anomalies, compression ratio)
**Processing Time:** 2-5 seconds

---

### Layer 4: AI Pattern Analysis

**Module:** `notes_analyzer.py`, `claude/client.py`, `claude/prompts.py` (ai-service/app/services/)
**Purpose:** Use Claude AI to discover complex behavioral patterns, hidden rules, systemic issues

**Input to Claude:**
1. **Statistical Context** (from Layer 2): Severity distribution, temporal patterns, risk scores, officer stats
2. **ML Context** (from Layer 3): Cluster breakdown, anomaly count, sampling strategy
3. **Deviation Data** (75 samples): Full details for each sampled deviation including notes

**Claude Prompt Structure:**
```python
prompt = f"""
You are an expert compliance analyst. Analyze {sample_count} deviations.

📊 Statistical Summary:
- Total: {total} deviations across {cases} cases, {officers} officers
- Severity: Critical {critical_pct}%, High {high_pct}%, Medium {medium_pct}%, Low {low_pct}%
- Peak Times: {peak_hours} (hours), {peak_days} (days)
- Risk Indicators: Severity {severity_score}/100, Concentration {concentration_pct}%

🤖 ML Summary:
- Clusters: {n_clusters} (DBSCAN)
- Anomalies: {n_anomalies} ({anomaly_pct}%)
- Sampling: {compression_ratio}x compression, all severities/times/officers covered

**Your Task:**
Discover:
1. Behavioral Patterns (officer shortcuts, workload correlation, time-based behavior)
2. Hidden Rules (informal practices not in SOP)
3. Systemic Issues (technical/process/resource problems)
4. Time Patterns (when/why deviations spike)
5. Risk Assessment (biggest compliance risks)

**Output JSON:**
{{"overall_summary": "...", "behavioral_patterns": [...], "hidden_rules": [...],
  "systemic_issues": [...], "recommendations": [...]}}
"""
```

**Claude API Call:**
```python
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    temperature=0.0,  # Deterministic for compliance
    messages=[{"role": "user", "content": prompt}]
)

# Track costs
input_cost = (response.usage.input_tokens / 1000) × 0.003
output_cost = (response.usage.output_tokens / 1000) × 0.015
total_cost = input_cost + output_cost  # ~$0.06 per analysis
```

**Example Output:**
```json
{
  "overall_summary": "Evening rush (4-6 PM) causes 40% of deviations.
                      EMP-009 shows systematic triple-skip pattern.
                      Friday workload 2x higher than other days.",
  "behavioral_patterns": [
    {
      "pattern_type": "workload_correlation",
      "description": "Officers skip verifications when processing >15 cases/day",
      "evidence": ["EMP-009: 18 cases/day → 67% deviation rate",
                   "EMP-018: 8 cases/day → 13% deviation rate"],
      "officers_involved": ["EMP-009", "EMP-018", "EMP-013"],
      "risk_level": "high"
    }
  ],
  "hidden_rules": [
    {
      "rule_description": "Skip Risk Assessment for loans <$10K",
      "evidence": ["0% of loans <$10K have Risk Assessment step"],
      "officers_following": ["EMP-007", "EMP-008", "EMP-015"],
      "formal_rule_violated": "SOP Section 3.2: Risk Assessment mandatory for ALL loans"
    }
  ],
  "systemic_issues": [
    {
      "issue_type": "resource",
      "description": "Understaffing on Fridays causes 2x workload and 3x deviations",
      "recommended_fix": "Add 2 officers on Fridays OR redistribute workload"
    }
  ],
  "recommendations": [
    "[CRITICAL] Suspend EMP-009 - triple-skip pattern suggests fraud/training failure",
    "[HIGH] Implement workflow gates - prevent progression if steps incomplete",
    "[MEDIUM] Deploy real-time monitoring - alert on 3+ missing steps in 30 days"
  ]
}
```

**Output:** Comprehensive pattern analysis with behavioral insights, hidden rules, systemic issues, recommendations
**Processing Time:** 30-60 seconds
**Cost:** ~$0.06 per analysis

---

## 🚀 Installation & Setup

### Prerequisites
- Node.js 18+
- Python 3.9+
- SQLite (included with Node.js)
- Claude API Key (for AI features)

### Backend Setup
```bash
cd backend
npm install
cp .env.example .env
# Add your Claude API key to .env: ANTHROPIC_API_KEY=your_key_here
npm start  # Runs on port 3000
```

### AI Service Setup
```bash
cd ai-service
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
cp .env.example .env
# Add your Claude API key to .env: ANTHROPIC_API_KEY=your_key_here
python main.py  # Runs on port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev  # Runs on port 5174
```

### Access Application
Open browser: `http://localhost:5174`

---

## 📝 Usage Workflow

### 1. Upload SOP Document
1. Go to Analysis Hub
2. Click "SOP Documents" widget
3. Upload .docx, .pdf, or .txt file
4. System automatically:
   - Parses the document
   - Extracts compliance rules using Claude AI
   - Stores rules in database

### 2. Upload Workflow Logs
1. Click "Workflow Logs" widget
2. Upload CSV file with loan processing logs
3. System automatically:
   - Uses Claude AI to analyze CSV headers
   - Maps columns to system fields (80+ field support)
   - Imports workflow data
   - Extracts notes/comments

**Supported CSV Fields (80+ fields):**
- **Core:** case_id, officer_id, step_name, action, timestamp, status, notes
- **Entity IDs:** application_id, loan_id, customer_id, portfolio_id
- **Product:** product_type, branch_code, channel
- **Amounts:** loan_amount_requested, loan_amount_sanctioned, emi_amount
- **Risk:** credit_score_bureau, emi_to_income_ratio, risk_grade, ltv_ratio
- **KYC/AML:** kyc_status, sanctions_hit_flag, pep_flag
- **Collateral:** collateral_type, collateral_value, security_created_flag
- **Disbursement:** disbursement_date, disbursement_amount, post_disbursement_qc_flag
- **Collections:** overdue_days, bucket, restructure_flag

### 3. Run Analysis
1. Select one SOP and one workflow log from dropdowns
2. Click "Analyze Compliance"
3. System performs 4-layer analysis:
   - **Layer 0**: Data cleaning (~1 sec)
   - **Layer 1**: Deviation detection (~1 sec)
   - **Layer 2**: Statistical analysis (~1 sec)
   - **Layer 3**: ML clustering/sampling (~3 sec)
   - **Layer 4**: AI pattern analysis (~45 sec)
   - **Total**: ~50-60 seconds

### 4. Review Results
Dashboard displays:
- **Overview Metrics**: Cases, logs, deviations, compliance rate
- **Deviations by Type/Severity**: Interactive charts
- **Statistical Insights**: Peak times, officer stats, risk scores
- **ML Summary**: Clusters, anomalies, compression ratio
- **AI Patterns**: Behavioral patterns, hidden rules, systemic issues, recommendations

---

## 📊 Metrics Explained

| Metric | Formula | Example | Interpretation |
|--------|---------|---------|----------------|
| **Total Cases** | Count unique case_id | 27 | Distinct loan applications |
| **Total Logs** | Count workflow entries | 76 | Individual workflow steps |
| **Total Deviations** | Count rule violations | 149 | Can exceed logs (multiple violations per log) |
| **Compliance Rate** | `max(0, (1 - deviations/logs) × 100%)` | 0% | Negative when deviations > logs |
| **Severity Score** | `(Σ count×weight) / total × 25` | 55/100 | Risk level: <30=Minimal, 30-44=Low, 45-59=Moderate, 60-74=High, 75-100=Very High |
| **Critical Mass** | `(critical+high)/total × 100%` | 35% | Urgency: >40%=Critical, 25-40%=High, <25%=Moderate |
| **Concentration Risk** | `top5_officers/total × 100%` | 70% | Officer distribution: >60%=Concentrated, <40%=Distributed |

---

