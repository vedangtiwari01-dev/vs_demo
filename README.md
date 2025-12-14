# ZenWolf - SOP Compliance Analysis System

## Overview

ZenWolf is an AI-powered compliance monitoring system that analyzes loan processing workflows against Standard Operating Procedures (SOPs) to detect deviations, identify patterns, and provide actionable insights.

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

## 📊 How Deviation Detection Works

### Step-by-Step Process

#### 1. SOP Rule Extraction

The system extracts rules from your SOP document:

```
SOP Text:
"Credit verification must be completed before proceeding to income assessment.
The credit check must be performed within 24 hours of application receipt.
All loans above $50,000 require manager approval."

Rules Extracted:
- Rule 1: type=sequence, description="Credit check before income assessment"
- Rule 2: type=timing, description="Credit check within 24 hours", constraint="24 hours"
- Rule 3: type=approval, description="Manager approval for loans >$50K"
```

#### 2. Workflow Log Analysis

The system analyzes each case's workflow chronologically:

**Example Case: LN-18231**

```csv
Loan_ID,Activity,User,Timestamp,Decision,Notes
LN-18231,Application Received,System,01-01-2025 08:00,Initiated,Customer applied online
LN-18231,Income Assessment,j_doe,01-01-2025 09:00,Completed,Income verified
LN-18231,Credit Check,j_doe,01-02-2025 10:00,Completed,Score: 720
LN-18231,Approval,j_doe,01-02-2025 11:00,Approved,Loan approved
```

#### 3. Rule-Based Deviation Detection

**Check Rule 1: Sequence** (Credit check before income assessment)
```python
# Get all steps for case LN-18231, ordered by timestamp
steps = ["Application Received", "Income Assessment", "Credit Check", "Approval"]

# Check: Did "Credit Check" happen before "Income Assessment"?
credit_check_index = 2
income_assessment_index = 1

if credit_check_index > income_assessment_index:
    # DEVIATION DETECTED!
    deviation = {
        "case_id": "LN-18231",
        "officer_id": "j_doe",
        "deviation_type": "wrong_sequence",
        "severity": "high",
        "description": "Credit check performed AFTER income assessment",
        "expected_behavior": "Credit check must happen before income assessment",
        "actual_behavior": "Income assessment at 09:00, Credit check at 10:00 (next day)"
    }
```

**Check Rule 2: Timing** (Credit check within 24 hours)
```python
application_time = datetime("01-01-2025 08:00")
credit_check_time = datetime("01-02-2025 10:00")
time_diff = credit_check_time - application_time  # 26 hours

if time_diff > timedelta(hours=24):
    # DEVIATION DETECTED!
    deviation = {
        "case_id": "LN-18231",
        "deviation_type": "timing_violation",
        "severity": "medium",
        "description": "Credit check completed 26 hours after application",
        "expected_behavior": "Credit check within 24 hours",
        "actual_behavior": "Took 26 hours (2 hours late)"
    }
```

**Check Rule 3: Approval** (Manager approval for >$50K)
```python
# Check if loan amount > $50,000 and if manager approved
if loan_amount > 50000:
    approval_logs = get_logs_for_case("LN-18231").filter(step="Approval")

    # Check if any approval was by a manager
    has_manager_approval = any(log.role == "Manager" for log in approval_logs)

    if not has_manager_approval:
        # DEVIATION DETECTED!
        deviation = {
            "case_id": "LN-18231",
            "deviation_type": "unauthorized_approval",
            "severity": "critical",
            "description": "Loan >$50K approved without manager authorization",
            "expected_behavior": "Manager approval required for loans >$50K",
            "actual_behavior": "Approved by j_doe (Loan Officer, not Manager)"
        }
```

**Result for Case LN-18231**: 3 deviations detected from 3 workflow logs!

#### 4. Comprehensive Example with Multiple Cases

**Your Data:**
- 27 cases (loan applications)
- 76 workflow logs (76 individual steps/actions across all 27 cases)
- 18 SOP rules to check

**Breakdown:**

```
Case LN-18231 (3 logs):
  Log 1: Application Received ✓ (0 deviations)
  Log 2: Income Assessment ✗ (2 deviations: wrong sequence, missing credit check)
  Log 3: Credit Check ✗ (1 deviation: timing violation)
  Total: 3 deviations from 3 logs

Case LN-18232 (2 logs):
  Log 1: Application Received ✓ (0 deviations)
  Log 2: Approval ✗ (4 deviations: missing steps, unauthorized approval, wrong sequence, no validation)
  Total: 4 deviations from 2 logs

Case LN-18233 (4 logs):
  All steps correct ✓ (0 deviations)
  Total: 0 deviations from 4 logs

... (24 more cases)

GRAND TOTAL: 149 deviations from 76 logs across 27 cases
```

### Types of Deviations

| Type | Description | Example |
|------|-------------|---------|
| **missing_step** | Required step was skipped | Credit check never performed |
| **wrong_sequence** | Steps done in incorrect order | Approval before credit check |
| **unauthorized_approval** | Wrong authority level | Officer approved $100K loan (needs manager) |
| **timing_violation** | Time constraint not met | Credit check took 48 hours (limit: 24) |
| **validation_failure** | Required validation not performed | Missing income verification |

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                         │
│  - Analysis Hub (upload SOP + workflow logs)                    │
│  - Results Viewer (deviations, patterns, metrics)               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (Node.js/Express)                     │
│  - Workflow Controller: Analyze, detect deviations              │
│  - SOP Controller: Upload, parse, extract rules                 │
│  - Database: Store workflows, SOPs, deviations                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                AI SERVICE (Python/FastAPI + Claude)              │
│  - SOP Parsing: Extract text from DOCX/PDF                      │
│  - Rule Extraction: Use Claude to identify compliance rules     │
│  - Column Mapping: AI-powered CSV header mapping                │
│  - Pattern Analysis: Discover behavioral patterns               │
└─────────────────────────────────────────────────────────────────┘
```

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
# Add your Claude API key to .env
npm start
```

### AI Service Setup
```bash
cd ai-service
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
cp .env.example .env
# Add your Claude API key to .env
python main.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 📝 Usage Workflow

### 1. Upload SOP Document
1. Go to Analysis Hub
2. Click "SOP Documents" widget
3. Upload .docx, .pdf, or .txt file
4. System automatically:
   - Parses the document
   - Extracts compliance rules using AI
   - Stores rules in database

### 2. Upload Workflow Logs
1. Click "Workflow Logs" widget
2. Upload CSV file with loan processing logs
3. System automatically:
   - Analyzes CSV headers with AI
   - Maps columns to system fields
   - Imports workflow data
   - Extracts notes/comments

### 3. Run Analysis
1. Select one SOP and one workflow log
2. Click "Analyze Compliance"
3. System performs:
   - **Step 1**: Deviation detection (rule-based, ~5 sec)
   - **Step 2**: Pattern analysis (AI-powered, ~30-60 sec)

### 4. Review Results
- **Overview Metrics**: Total cases, logs, deviations, compliance rate
- **Deviations by Type**: Breakdown by severity (critical, high, medium, low)
- **Behavioral Patterns**: AI-discovered officer habits and shortcuts
- **Hidden Rules**: Informal practices not in the SOP
- **Systemic Issues**: Recurring problems needing process fixes
- **Recommendations**: Actionable steps to improve compliance

## 📊 Metrics Explained

### Overview Metrics

| Metric | Formula | Example | Explanation |
|--------|---------|---------|-------------|
| **Total Cases** | Count of unique loan applications | 27 distinct cases | Number of different loans being processed |
| **Total Logs** | Count of workflow step records | 76 individual steps | Total number of actions recorded in the workflow |
| **Total Officers** | Count of unique staff members | 5 different officers | Number of people involved in processing |
| **Total Deviations** | Count of rule violations | 149 violations detected | **Can exceed Total Logs** - one log can have multiple violations |
| **Compliance Rate** | `(1 - deviations/logs) × 100%` | `(1 - 149/76) × 100% = 0%`* | Percentage of compliant workflow steps |

*Note: Compliance rate can be negative or 0% when deviations exceed logs, indicating severe non-compliance where multiple rules are violated per step.

### Severity Breakdown

| Severity | Criteria | Impact | Action Required |
|----------|----------|--------|-----------------|
| **Critical** | Regulatory violation, major risk | Legal/financial exposure | Immediate action required |
| **High** | SOP violation, significant risk | Operational risk | Priority remediation |
| **Medium** | Process quality issue | Minor risk | Should be addressed |
| **Low** | Best practice not followed | Minimal risk | Monitor and improve |

## 📁 Project Structure

```
vs_demo/
├── backend/              # Node.js/Express API
│   ├── src/
│   │   ├── controllers/  # Request handlers
│   │   ├── models/       # Sequelize database models
│   │   ├── routes/       # API endpoints
│   │   └── services/     # Business logic
│   └── database.sqlite   # SQLite database
├── ai-service/           # Python/FastAPI AI service
│   ├── app/
│   │   ├── routers/      # API endpoints
│   │   ├── services/     # Claude integration
│   │   └── models/       # Pydantic schemas
│   └── main.py          # FastAPI entry point
├── frontend/             # React application
│   └── src/
│       ├── components/   # React components
│       ├── pages/        # Page components
│       └── api/          # API client functions
└── README.md            # This file
```

## 🔧 Troubleshooting

### AI Service Won't Stop
```bash
# Use the kill script
kill_ai_service.bat

# Or manually
netstat -ano | findstr :8000
taskkill /F /PID <PID>
```

### Analysis Times Out
- Reduce deviation limit in `backend/src/controllers/workflow.controller.js` line 495
- Change `limit: 50` to `limit: 20`

### Wrong Metrics in UI
1. Run `python test_complete_analysis.py`
2. Check response structure matches frontend expectations
3. Compare with `ResultsViewer.jsx` requirements

## 🌐 API Endpoints

### Backend (Port 3000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sops` | GET | List all SOPs |
| `/api/sops` | POST | Upload SOP document |
| `/api/sops/:id/process` | POST | Extract rules from SOP |
| `/api/workflows/upload-with-mapping` | POST | Upload workflow CSV |
| `/api/workflows/analyze` | POST | Detect deviations |
| `/api/workflows/analyze-patterns` | POST | AI pattern analysis |
| `/api/workflows/list-files` | GET | List uploaded workflows |

### AI Service (Port 8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ai/sop/parse` | POST | Parse SOP document |
| `/ai/sop/extract-rules` | POST | Extract compliance rules |
| `/ai/mapping/analyze-headers` | POST | Map CSV columns |
| `/ai/deviation/analyze-patterns` | POST | Analyze deviation patterns |

## 📄 License

Proprietary - All Rights Reserved

## 💬 Support

For issues or questions, please contact the development team.
