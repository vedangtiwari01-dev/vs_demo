# Complete Deviation Detection Logic - DETAILED EXPLANATION

## Overview: How Deviations Are Detected From Rules + Workflow Logs

Your system uses a **hybrid approach** combining **rule-based logic** and **AI analysis**:

```
SOP Rules + Workflow Logs → Rule-Based Detection → Store Deviations → AI Pattern Analysis
```

---

## Part 1: The Files and Their Roles

### Main Flow:

```
1. backend/src/controllers/workflow.controller.js (Line 359-511)
   ↓ Receives workflow logs + SOP rules
   ↓ Calls AI service

2. ai-service/app/routers/deviation_detector.py (Line 13-48)
   ↓ Receives HTTP request
   ↓ Calls deviation detection services

3. ai-service/app/services/deviation/sequence_checker.py
   ↓ Checks sequence violations

4. ai-service/app/services/deviation/rule_validator.py
   ↓ Checks approval, timing violations

5. Returns deviations → Backend saves to database
```

---

## Part 2: DETAILED LOGIC EXPLANATION

### A. Sequence Deviation Detection (sequence_checker.py)

**File:** `ai-service/app/services/deviation/sequence_checker.py`

#### Logic Flow:

```python
def check_sequence(logs, rules):
    """
    INPUT:
    - logs: [{case_id, officer_id, step_name, action, timestamp, ...}, ...]
    - rules: [{rule_type: 'sequence', rule_description, step_number, ...}, ...]

    OUTPUT:
    - deviations: [{case_id, officer_id, deviation_type, severity, description, ...}, ...]
    """

    # STEP 1: Extract sequence rules
    sequence_rules = [r for r in rules if r['rule_type'] == 'sequence']

    # STEP 2: Build expected sequence from rules
    expected_sequence = _build_expected_sequence(sequence_rules)
    # Example: ['Application Received', 'Document Verification', 'Credit Check', ...]

    # STEP 3: Group logs by case_id
    cases = group_by_case_id(logs)

    # STEP 4: For each case, check sequence
    for case_id, case_logs in cases.items():
        # Sort logs by timestamp (chronological order)
        case_logs.sort(by='timestamp')

        # Extract actual sequence
        actual_sequence = [log['step_name'] for log in case_logs]
        # Example: ['Application Received', 'Credit Check', 'Document Verification']

        # STEP 5: Compare expected vs actual
        deviations = _compare_sequences(expected, actual)
```

#### Algorithm for `_compare_sequences()`:

**1. Missing Steps Detection:**
```python
missing_steps = set(expected) - set(actual)
# Example:
#   expected = ['A', 'B', 'C', 'D']
#   actual = ['A', 'C', 'D']
#   missing_steps = {'B'}  ← DEVIATION!

for step in missing_steps:
    create_deviation(
        type='missing_step',
        severity='high',
        description=f'Missing required step: {step}'
    )
```

**2. Wrong Order Detection:**
```python
# Create index map for expected order
expected_idx = {'Application Received': 0, 'Document Verification': 1, 'Credit Check': 2, ...}

# Check each pair of consecutive steps in actual sequence
for i in range(len(actual) - 1):
    current_step = actual[i]  # e.g., 'Credit Check' (expected index: 2)
    next_step = actual[i + 1]  # e.g., 'Document Verification' (expected index: 1)

    if expected_idx[current_step] > expected_idx[next_step]:
        # Wrong order! 'Credit Check' (2) came before 'Document Verification' (1)
        create_deviation(
            type='wrong_sequence',
            severity='high',
            description=f'Wrong order: {next_step} before {current_step}'
        )
```

**3. Unexpected Steps Detection:**
```python
unexpected_steps = set(actual) - set(expected)
# Example:
#   expected = ['A', 'B', 'C']
#   actual = ['A', 'X', 'B', 'C']
#   unexpected_steps = {'X'}  ← DEVIATION!

for step in unexpected_steps:
    create_deviation(
        type='unexpected_step',
        severity='medium',
        description=f'Unexpected step: {step}'
    )
```

---

### B. Rule Validation (rule_validator.py)

**File:** `ai-service/app/services/deviation/rule_validator.py`

#### Logic Flow:

```python
def validate_all(logs, rules):
    """
    Validates workflow logs against SOP rules for:
    - Approval requirements
    - Timing constraints
    - Other rule types (16 types supported)
    """

    deviations = []

    # STEP 1: Group logs by case
    cases = group_by_case_id(logs)

    # STEP 2: For each case, run validations
    for case_id, case_logs in cases.items():
        case_logs.sort(by='timestamp')

        # Check approval rules
        approval_deviations = _check_approval_rules(case_id, case_logs, rules)

        # Check timing rules
        timing_deviations = _check_timing_rules(case_id, case_logs, rules)

        deviations.extend(approval_deviations + timing_deviations)

    return deviations
```

#### Algorithm for `_check_approval_rules()`:

```python
def _check_approval_rules(case_id, logs, rules):
    """
    Checks if required approvals are present in the workflow.
    """

    # STEP 1: Extract approval rules
    approval_rules = [r for r in rules if r['rule_type'] == 'approval']

    # STEP 2: Get all step names from logs
    step_names = [log['step_name'].lower() for log in logs]
    # Example: ['application received', 'credit check', 'final approval']

    # STEP 3: Check for required approvals
    has_manager_approval = any('manager' in step and 'approval' in step
                               for step in step_names)
    has_final_approval = any('final' in step and 'approval' in step
                             for step in step_names)

    # STEP 4: Create deviations if approvals missing
    if not has_manager_approval:
        create_deviation(
            case_id=case_id,
            type='missing_approval',
            severity='critical',
            description='Missing manager approval'
        )

    if not has_final_approval:
        create_deviation(
            case_id=case_id,
            type='missing_approval',
            severity='critical',
            description='Missing final approval'
        )
```

#### Algorithm for `_check_timing_rules()`:

```python
def _check_timing_rules(case_id, logs, rules):
    """
    Checks timing constraints:
    1. Process not too rushed
    2. No excessive gaps between steps
    """

    # STEP 1: Calculate total process duration
    first_timestamp = logs[0]['timestamp']  # '2025-01-15 09:00:00'
    last_timestamp = logs[-1]['timestamp']  # '2025-01-15 09:30:00'
    duration_hours = (last_timestamp - first_timestamp) / 3600

    # STEP 2: Check if too fast (< 1 hour)
    if duration_hours < 1:
        create_deviation(
            type='timing_violation',
            severity='medium',
            description=f'Process too rushed ({duration_hours:.1f} hours)'
        )

    # STEP 3: Check for long gaps between steps
    for i in range(len(logs) - 1):
        current_time = logs[i]['timestamp']
        next_time = logs[i + 1]['timestamp']
        gap_days = (next_time - current_time) / 86400

        if gap_days > 7:  # More than 7 days
            create_deviation(
                type='timing_violation',
                severity='low',
                description=f'Long delay: {gap_days:.1f} days between steps'
            )
```

---

## Part 3: Example Walkthrough

### Input Data:

**SOP Rules:**
```json
[
  {
    "id": 1,
    "rule_type": "sequence",
    "rule_description": "Application must be received first",
    "step_number": 1,
    "severity": "high"
  },
  {
    "id": 2,
    "rule_type": "sequence",
    "rule_description": "Document verification must follow application",
    "step_number": 2,
    "severity": "high"
  },
  {
    "id": 3,
    "rule_type": "sequence",
    "rule_description": "Credit check must be performed",
    "step_number": 3,
    "severity": "critical"
  },
  {
    "id": 4,
    "rule_type": "approval",
    "rule_description": "Manager approval required before final approval",
    "severity": "critical"
  }
]
```

**Workflow Logs (Case CASE001):**
```json
[
  {
    "case_id": "CASE001",
    "officer_id": "OFF123",
    "step_name": "Application Received",
    "action": "received",
    "timestamp": "2025-01-15 09:00:00"
  },
  {
    "case_id": "CASE001",
    "officer_id": "OFF123",
    "step_name": "Final Approval",
    "action": "approved",
    "timestamp": "2025-01-15 09:30:00"
  }
]
```

### Detection Process:

**Step 1: Build Expected Sequence**
```python
expected_sequence = [
    'Application Received',    # from rule 1
    'Document Verification',   # from rule 2
    'Credit Check',           # from rule 3
    'Manager Approval',       # from rule 4
    'Final Approval'          # standard step
]
```

**Step 2: Extract Actual Sequence**
```python
actual_sequence = [
    'Application Received',
    'Final Approval'
]
```

**Step 3: Compare Sequences**

**Missing Steps Detected:**
```python
missing = {'Document Verification', 'Credit Check', 'Manager Approval'}

DEVIATION 1:
{
  "case_id": "CASE001",
  "officer_id": "OFF123",
  "deviation_type": "missing_step",
  "severity": "high",
  "description": "Missing required step: Document Verification",
  "expected_behavior": "Step 'Document Verification' should be completed",
  "actual_behavior": "Step 'Document Verification' was skipped"
}

DEVIATION 2:
{
  "case_id": "CASE001",
  "officer_id": "OFF123",
  "deviation_type": "missing_step",
  "severity": "high",
  "description": "Missing required step: Credit Check",
  "expected_behavior": "Step 'Credit Check' should be completed",
  "actual_behavior": "Step 'Credit Check' was skipped"
}

DEVIATION 3:
{
  "case_id": "CASE001",
  "officer_id": "OFF123",
  "deviation_type": "missing_step",
  "severity": "high",
  "description": "Missing required step: Manager Approval",
  "expected_behavior": "Step 'Manager Approval' should be completed",
  "actual_behavior": "Step 'Manager Approval' was skipped"
}
```

**Step 4: Check Approval Rules**
```python
step_names = ['application received', 'final approval']
has_manager_approval = False  # No 'manager' + 'approval' in step names

DEVIATION 4:
{
  "case_id": "CASE001",
  "officer_id": "OFF123",
  "deviation_type": "missing_approval",
  "severity": "critical",
  "description": "Missing manager approval",
  "expected_behavior": "Manager approval required before final approval",
  "actual_behavior": "Manager approval step not found"
}
```

**Step 5: Check Timing Rules**
```python
first_timestamp = '2025-01-15 09:00:00'
last_timestamp = '2025-01-15 09:30:00'
duration_hours = 0.5  # 30 minutes

if duration_hours < 1:  # TRUE
    DEVIATION 5:
    {
      "case_id": "CASE001",
      "officer_id": "OFF123",
      "deviation_type": "timing_violation",
      "severity": "medium",
      "description": "Process completed too quickly",
      "expected_behavior": "Proper review time required for each step",
      "actual_behavior": "Process completed in 0.5 hours"
    }
```

**Final Result: 5 Deviations Detected**

---

## Part 4: The Complete Flow in Your System

### Backend Controller (workflow.controller.js:359-511)

```javascript
// Line 359: analyzeWorkflow function
const analyzeWorkflow = async (req, res, next) => {
  // 1. Get workflow logs from database
  const logs = await WorkflowLog.findAll({
    where: { upload_id: req.params.upload_id }
  });

  // 2. Get SOP rules from database
  const rules = await SOPRule.findAll();

  // 3. Call AI service to detect deviations
  const deviations = await aiService.detectDeviations({
    logs: logs,
    rules: rules
  });

  // 4. Save deviations to database
  for (const deviation of deviations) {
    await Deviation.create(deviation);
  }

  // 5. Return results
  return res.json({ deviations });
};
```

### AI Service Router (deviation_detector.py:13-48)

```python
# Line 13: detect_deviations endpoint
@router.post('/detect')
async def detect_deviations(request: DeviationDetectionRequest):
    logs = request.logs    # From backend
    rules = request.rules  # From backend

    # 1. Check sequences
    sequence_deviations = SequenceChecker.check_sequence(logs, rules)
    # Returns: [deviation1, deviation2, ...]

    # 2. Validate other rules
    rule_deviations = RuleValidator.validate_all(logs, rules)
    # Returns: [deviation3, deviation4, ...]

    # 3. Combine all deviations
    all_deviations = sequence_deviations + rule_deviations

    # 4. Return to backend
    return DeviationDetectionResponse(deviations=all_deviations)
```

---

## Part 5: After Deviations Are Detected → Pattern Analysis

Once deviations are stored in the database, the pattern analysis happens:

```
User clicks "Analyze Patterns"
    ↓
Backend: Get ALL deviations from database
    ↓
Send to AI Service: /ai/deviation/analyze-patterns
    ↓
Layer 1: Data Cleaning (NEW in Phase 1)
    - Remove duplicates
    - Validate data
    ↓
Layer 2: Statistical Analysis (NEW in Phase 1)
    - Severity distribution
    - Temporal patterns
    - Officer statistics
    ↓
Layer 3: AI Pattern Analysis
    - LLM receives cleaned deviations + statistical context
    - Finds behavioral patterns
    - Identifies hidden rules
    - Makes recommendations
```

---

## Summary: Which Files Do What

| File | Responsibility | Key Logic |
|------|---------------|-----------|
| `backend/src/controllers/workflow.controller.js` | Orchestrates the flow | Gets logs + rules → Calls AI service → Saves deviations |
| `ai-service/app/routers/deviation_detector.py` | HTTP endpoints | Receives request → Calls checkers → Returns deviations |
| `ai-service/app/services/deviation/sequence_checker.py` | **Sequence validation** | Detects: missing_step, wrong_sequence, unexpected_step |
| `ai-service/app/services/deviation/rule_validator.py` | **Rule validation** | Detects: missing_approval, timing_violation |
| `ai-service/app/services/data/data_cleaner.py` | **Data cleaning** (Phase 1) | Removes duplicates, validates data |
| `ai-service/app/services/data/statistical_analyzer.py` | **Statistical analysis** (Phase 1) | Analyzes severity, temporal patterns, officer stats |
| `ai-service/app/services/deviation/notes_analyzer.py` | **AI pattern analysis** | LLM finds patterns, hidden rules, recommendations |

---

## Key Algorithms Used

1. **Set Difference (Missing Steps):** `expected - actual`
2. **Index Comparison (Wrong Order):** Compare position indices
3. **Set Difference (Unexpected Steps):** `actual - expected`
4. **String Matching (Approvals):** Check if keywords exist
5. **Time Delta Calculation (Timing):** Timestamp arithmetic
6. **Duplicate Detection (Phase 1):** Hash table with (case_id, officer_id, type) as key
7. **Statistical Aggregation (Phase 1):** Counter, distributions, correlations

---

## Notes

- **Rule-based detection is FAST** - No AI needed, just logic
- **Deterministic** - Same input always gives same output
- **Limited** - Can only detect patterns you explicitly code
- **Complemented by AI** - LLM catches subtle patterns rule-based logic misses
- **Phase 1 enhancement** - Data cleaning + statistics ensure high-quality input for all layers
