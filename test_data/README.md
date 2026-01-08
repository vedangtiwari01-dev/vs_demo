# Integration Test Data for ZenWolf

This directory contains synthetic test data to verify the complete backend + AI service integration.

## Test Files

### 1. `test_sop_rules.txt`
A comprehensive SOP document with 7 sections covering:
- Mandatory workflow sequence (8 steps)
- Approval requirements (3 tiers based on loan amount)
- Timing requirements (TAT, min/max processing times)
- Credit and eligibility rules (credit score thresholds, age limits)
- Documentation requirements
- Disbursement conditions
- Data quality rules

### 2. `test_workflow_logs.csv`
Contains 44 workflow logs across 7 loan cases with diverse deviation scenarios:

| Case | Loan Amount | Officer(s) | Deviations Injected |
|------|-------------|------------|---------------------|
| LOAN-001 | $25,000 | EMP-101, EMP-102 | ✅ Clean - No deviations (baseline) |
| LOAN-002 | $8,000 | EMP-103 | Missing steps (Income Verification, Risk Assessment), Missing Manager Approval |
| LOAN-003 | $75,000 | EMP-101 | Wrong sequence (Income before Document), Low credit score (590) approved, Missing Senior Manager approval, Rushed processing (<2 hours), Self-approval |
| LOAN-004 | $35,000 | EMP-104 | Self-approval, Missing Manager Approval |
| LOAN-005 | $15,000 | EMP-105 | Missing steps (Income Verification, Risk Assessment), Missing Manager Approval, Rushed processing |
| LOAN-006 | $9,500 | EMP-103 | Wrong sequence (skipped Document Verification), Missing steps, Post-disbursement without proper verification |
| LOAN-007 | $120,000 | EMP-106, EMP-102 | Missing Final Approval step, Missing Senior Manager Approval for >$50k loan |

### Deviation Types Covered (13 types)

1. **Missing Steps** - Required steps skipped (Document Verification, Income Verification, Risk Assessment, Final Approval)
2. **Wrong Sequence** - Steps performed out of order
3. **Timing Violations** - Rushed processing (<2 hours total)
4. **Missing Approval** - Manager approval missing for loans >$10k
5. **Insufficient Hierarchy** - Senior Manager approval missing for loans >$50k
6. **Self Approval** - Same officer processing and approving
7. **Low Score Approved** - Credit score below threshold (600) approved without exception
8. **Incomplete Documentation** - Documents not verified before disbursement
9. **Data Quality Issues** - Missing core fields, inconsistent data
10. **Hidden Rules** - Small loans (<$10k) systematically skip steps (informal practice)

### Officer Behavioral Patterns

- **EMP-101**: Mixed behavior - handles high-value loans, sometimes rushes process
- **EMP-103**: Consistently skips verification steps for small loans (<$10k) - hidden rule follower
- **EMP-104**: Self-approval pattern - approves own work
- **EMP-105**: Rushes small loans, skips Manager approval
- **EMP-106**: Processes large loans but misses Senior Manager approval

## Running the Test

### Prerequisites

1. **Backend service running** on `http://localhost:3000`
   ```bash
   cd backend
   npm start
   ```

2. **AI service running** on `http://localhost:8000`
   ```bash
   cd ai-service
   python main.py
   ```

3. **Python 3.9+** with requests library
   ```bash
   pip install requests
   ```

### Execute Test

```bash
python test_integration.py
```

### What the Test Does

The script performs a complete end-to-end test:

1. **Step 0**: Health check - Verifies backend and AI services are running
2. **Step 1**: SOP Upload - Uploads `test_sop_rules.txt`
3. **Step 2**: Rule Extraction - Processes SOP with Claude AI to extract compliance rules
4. **Step 3**: Workflow Upload - Uploads and maps `test_workflow_logs.csv`
5. **Step 4**: Deviation Detection - Runs rule-based deviation detection (10 checkers)
6. **Step 5**: Pattern Analysis - Uses Claude AI to discover behavioral patterns, hidden rules, systemic issues

### Expected Output

The test will display:
- ✓ Green checkmarks for successful steps
- ℹ Blue info messages for progress
- ⚠ Yellow warnings if applicable
- ✗ Red errors if something fails

### Expected Results

Based on the test data, you should see:

**Deviations Detected**: ~40-60 deviations (remember: 1 log can have multiple violations)

**Deviation Breakdown**:
- Missing steps: ~15-20
- Wrong sequence: ~3-5
- Timing violations: ~2-3
- Missing approval: ~5-8
- Self-approval: ~2
- Insufficient hierarchy: ~2
- Low credit score issues: ~1

**Behavioral Patterns** (AI should discover):
1. **Shortcut Pattern**: EMP-103 systematically skips Risk Assessment for loans <$10k
2. **Self-Approval Pattern**: EMP-104 approves own work
3. **Rushed Processing**: EMP-101, EMP-105 complete loans in <2 hours
4. **Workload Correlation**: Officers handling more cases show more deviations

**Hidden Rules** (AI should discover):
1. "Small loans (<$10k) don't need Risk Assessment" - Informal practice by EMP-103
2. "Manager approval skipped for emergency loans" - EMP-105's practice
3. "Senior Manager approval often forgotten for high-value loans"

**Systemic Issues** (AI should identify):
1. Approval hierarchy not enforced by system (allows self-approval)
2. No automated gates preventing sequence violations
3. Credit score thresholds not enforced automatically
4. Senior Manager approval requirement not clear to officers

### Test Output Files

- `test_results.json` - Complete JSON output of all API responses
- Backend SQLite database will contain:
  - 1 SOP record
  - ~15-20 rules extracted
  - 44 workflow log records
  - ~40-60 deviation records
  - Behavioral patterns and profiles

## Troubleshooting

### Services Not Running
```
✗ Backend service is not reachable at http://localhost:3000
```
**Solution**: Start backend with `cd backend && npm start`

### AI Service Timeout
```
✗ Failed to analyze patterns. Status: 504
```
**Solution**: AI service may need more time. The script has 10-minute timeout, but check if Claude API key is configured.

### No Rules Extracted
```
✗ SOP processed successfully! Extracted 0 rules
```
**Solution**: Check `ANTHROPIC_API_KEY` in `ai-service/.env`

## Customizing Test Data

### Adding More Cases
Edit `test_workflow_logs.csv` and add more rows with:
- Unique case_id (LOAN-XXX)
- Valid officer_id (EMP-XXX)
- ISO timestamp format (YYYY-MM-DD HH:MM:SS)
- Inject specific deviations by violating SOP rules

### Adding More Rules
Edit `test_sop_rules.txt` and add new sections with:
- Clear rule descriptions
- Severity indicators (CRITICAL, MANDATORY)
- Specific thresholds/conditions

### Testing Specific Scenarios

**Test Sequence Violations**: Swap step order in CSV
**Test Approval Issues**: Remove approval steps for high-value loans
**Test Timing Issues**: Set timestamps very close together (<2 hours)
**Test Credit Issues**: Add credit_score column with values <600
**Test Hidden Patterns**: Have one officer consistently skip same steps

## Next Steps After Testing

1. **Review Results**: Check `test_results.json` for detailed API responses
2. **Verify Database**: Query SQLite to see stored deviations
3. **Test Frontend**: Open `http://localhost:5174` and view results in UI
4. **Scale Test**: Create larger CSV with 100+ logs to test ML sampling
5. **Custom Scenarios**: Modify test data to match your real-world use cases
