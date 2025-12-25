# Testing Instructions for 5-Layer Pipeline

## Quick Start (Automated Test)

### 1. Start Both Services

**Terminal 1 - Backend:**
```bash
cd backend
npm install  # If not done already
npm start
```
Wait for: `Server running on port 5000`

**Terminal 2 - AI Service:**
```bash
cd ai-service
pip install -r requirements.txt  # If not done already
python main.py
```
Wait for: `Uvicorn running on http://0.0.0.0:8000`

### 2. Run Automated Test

**Terminal 3 - Test Script:**
```bash
# From project root
python test_complete_pipeline.py
```

This will:
- ✅ Check if both services are running
- ✅ Verify ML dependencies are installed
- ✅ Create sample SOP document
- ✅ Create sample workflow CSV (100 cases with intentional deviations)
- ✅ Upload SOP and extract rules
- ✅ Upload workflow logs with data cleaning
- ✅ Run comprehensive 5-layer analysis
- ✅ Display detailed results

**Expected Output:**
```
================================================================================
                    5-LAYER PIPELINE COMPREHENSIVE TEST
================================================================================

================================================================================
                           STEP 0: Checking Services
================================================================================

✓ Backend is running at http://localhost:5000
✓ AI Service is running at http://localhost:8000
✓ ML dependencies are installed
  - numpy: 1.24.3
  - pandas: 2.0.2
  - scikit-learn: 1.3.0

================================================================================
                         STEP 1: Upload SOP Document
================================================================================

✓ SOP uploaded successfully
ℹ   - SOP ID: 1
ℹ   - Rules extracted: 5
ℹ   - Extraction method: llm

================================================================================
                        STEP 2: Analyze CSV Headers
================================================================================

✓ Headers analyzed successfully
ℹ   - Detected 8 column mappings

================================================================================
                   STEP 3: Upload Workflow Logs with Mapping
================================================================================

✓ Workflow logs uploaded successfully
ℹ   - Total rows processed: 580
ℹ   - Logs saved: 580
ℹ   - Unique cases: 100
ℹ   - Unique officers: 10
ℹ   - Data Cleaning:
ℹ     • Clean rows: 580 (100.0%)
ℹ     • Duplicates removed: 0
ℹ     • Garbage removed: 0

================================================================================
              STEP 4: Run Comprehensive Analysis (5-Layer Pipeline)
================================================================================

✓ Comprehensive analysis completed in 125.3s

📊 SUMMARY:
ℹ   - Total deviations found: 45
ℹ   - Representatives analyzed by LLM: 45
ℹ   - Total processing time: 125.3s
ℹ   - Pipeline layers completed: 5/5

📈 STATISTICAL INSIGHTS (ALL 45 deviations):
ℹ   Severity Distribution:
ℹ     • high: 20 (44.4%)
ℹ     • critical: 15 (33.3%)
ℹ     • medium: 10 (22.2%)

🤖 ML ANALYSIS:
ℹ   - Compression ratio: 1.0x (small dataset, all included)
ℹ   - Clusters found: 3
ℹ   - Anomalies detected: 5

🔍 AI PATTERN ANALYSIS:
ℹ   Summary: Found 3 behavioral patterns and 2 hidden rules...

💰 COST SAVINGS:
ℹ   - Full analysis cost: $0.45
ℹ   - Actual cost (ML sampling): $0.45
ℹ   - Savings: 0% (dataset too small for compression)

================================================================================
                            ✅ ALL TESTS PASSED!
================================================================================
```

---

## Manual Testing (Step by Step)

If you want to test manually or use your own data:

### Step 1: Check Services Health

```bash
# Check backend
curl http://localhost:5000/health

# Check AI service
curl http://localhost:8000/ai/health

# Check ML service
curl http://localhost:8000/ml/health
```

### Step 2: Test ML Service Independently

```bash
# Test ML sampling with dummy data
curl -X POST http://localhost:8000/ml/test-sample
```

Expected response:
```json
{
  "message": "Test sampling successful",
  "input_size": 100,
  "output_size": 20,
  "metadata": {
    "compression_ratio": "5.0x",
    "num_clusters": 3,
    "num_anomalies": 2
  }
}
```

### Step 3: Upload Your Own SOP

```bash
# Using curl
curl -X POST http://localhost:5000/sop/upload \
  -F "sop=@/path/to/your/sop.pdf" \
  -F "use_llm=true"

# Using Postman
POST http://localhost:5000/sop/upload
Body: form-data
  - sop: [select your SOP file]
  - use_llm: true
```

### Step 4: Upload Your Own Workflow Logs

**First, analyze headers:**
```bash
curl -X POST http://localhost:5000/workflow/analyze-headers \
  -F "logs=@/path/to/your/worklog.csv"
```

**Then, upload with mapping:**
```bash
curl -X POST http://localhost:5000/workflow/upload-with-mapping \
  -F "logs=@/path/to/your/worklog.csv" \
  -F "sop_id=1" \
  -F 'column_mapping={"mappings":[...]}'
```

### Step 5: Run Comprehensive Analysis

```bash
curl -X POST http://localhost:5000/workflow/analyze-comprehensive
```

---

## Testing with Different Data Sizes

### Small Dataset (100 cases)
- Run the automated test script
- Expected time: ~2 minutes
- ML compression: Minimal (dataset too small)

### Medium Dataset (500-1000 cases)
- Create your own CSV with 500-1000 unique case_ids
- Each case should have 5-10 workflow steps
- Expected time: ~3 minutes
- ML compression: 5-10x

### Large Dataset (1500-3000 cases)
- Use real production data or generate synthetic data
- Expected time: ~4-6 minutes
- ML compression: 15-25x
- Cost savings: 90-95%

---

## What to Look For

### ✅ Success Indicators

1. **Data Cleaning (Layer 1)**
   - Check upload response for `cleaning_report`
   - Should show duplicates and garbage removed
   - Success rate should be >95%

2. **Deviation Detection (Layer 2)**
   - Check `total_deviations` in comprehensive analysis response
   - Should find deviations based on rules
   - Processing should be fast (<2 min for 1000 cases)

3. **Statistical Analysis (Layer 3)**
   - Check `statistical_insights` in response
   - Should have distributions, correlations, time series
   - Should analyze ALL deviations (100% coverage)

4. **ML Sampling (Layer 4)**
   - Check `ml_analysis.sampling_metadata`
   - Compression ratio should be >10x for large datasets
   - Should find clusters (typically 5-15)
   - Should detect anomalies (typically 5-10%)

5. **AI Pattern Analysis (Layer 5)**
   - Check `pattern_analysis`
   - Should have behavioral patterns
   - Should have hidden rules
   - Should have recommendations

6. **Cost Savings**
   - Check `cost_savings`
   - For datasets >500 deviations, should show 80-95% savings
   - Compression ratio should match ML sampling ratio

### ⚠️ Warning Signs

1. **Timeout Errors**
   - If analysis takes >10 minutes, something is wrong
   - Check AI service logs for errors
   - Check if Claude API key is set

2. **Memory Issues**
   - If backend crashes, reduce batch size
   - Check system memory usage
   - Consider processing in smaller batches

3. **ML Errors**
   - If ML sampling fails, system falls back to statistical sampling
   - Check `ml_analysis.sampling_metadata.method` for "fallback_statistical"
   - Ensure ML dependencies are installed correctly

4. **No Deviations Found**
   - If `total_deviations = 0`, check:
     - Are rules extracted from SOP?
     - Does worklog data match expected format?
     - Are column mappings correct?

5. **Low Compression Ratio**
   - If compression ratio is 1.0x, dataset might be too small
   - ML sampling only compresses when there are >100 deviations
   - This is normal for small test datasets

---

## Troubleshooting

### Problem: ML dependencies not found

**Symptoms:**
```
Error: No module named 'sklearn'
```

**Solution:**
```bash
cd ai-service
pip install numpy>=1.24.0 pandas>=2.0.0 scikit-learn>=1.3.0 scipy>=1.11.0
```

### Problem: Backend can't connect to AI service

**Symptoms:**
```
Error: ECONNREFUSED localhost:8000
```

**Solution:**
1. Check if AI service is running: `curl http://localhost:8000/ai/health`
2. Check AI service URL in backend config: `backend/src/config/ai-service.js`
3. Restart AI service

### Problem: Out of memory during analysis

**Symptoms:**
```
Error: JavaScript heap out of memory
```

**Solution:**
```bash
# Increase Node.js memory limit
export NODE_OPTIONS="--max-old-space-size=4096"
cd backend
npm start
```

### Problem: Analysis taking too long

**Symptoms:**
- Stuck at Layer 4 or Layer 5
- No progress for >5 minutes

**Solution:**
1. Check AI service logs: Look for errors in Python console
2. Check Claude API quota: Make sure API key is valid
3. Reduce dataset size: Test with smaller sample first

### Problem: Cleaning report shows 100% garbage

**Symptoms:**
```
cleaning_report: {
  garbage_removed: 580,
  clean_output: 0
}
```

**Solution:**
1. Check CSV format: Ensure timestamps are valid dates
2. Check for test data: Remove rows with "test", "dummy" in case_id
3. Review data cleaning patterns in `data-cleaning.service.js`

---

## Understanding the Results

### Deviation Count Clarification

**Example Scenario:**
```
1500 loan applications (cases)
    ↓
Each case has ~10 workflow steps
    ↓
= 15,000 workflow log rows
    ↓
System checks against 50+ rules
    ↓
Finds 800 deviations (5.3% violation rate)
    ↓
ML sampling: 800 → 75 representatives (10.7x compression)
    ↓
LLM analyzes 75 with full context of 800
```

**What each number means:**
- **1500** = Number of loan applications (unique case_ids)
- **15,000** = Number of workflow log rows (steps × cases)
- **800** = Number of deviations found (violations)
- **75** = Number of representatives sent to LLM
- **10.7x** = Compression ratio (800 ÷ 75)

### Cost Calculation

**Without ML sampling:**
```
800 deviations × $0.01 per deviation = $8.00
```

**With ML sampling:**
```
75 representatives × $0.01 per deviation = $0.75
Savings = ($8.00 - $0.75) / $8.00 = 90.6%
```

**Coverage:**
- Old system (first 50): 50/800 = 6.25% coverage
- New system (ML): 100% coverage via statistical analysis + intelligent sampling

---

## Next Steps After Testing

### If Tests Pass ✅

1. **Test with Real Data**
   - Upload your actual SOP documents
   - Upload real workflow logs (start with small sample)
   - Verify results match expectations

2. **Fine-Tune Parameters**
   - Adjust target_sample_size (default: 75)
   - Modify DBSCAN parameters if needed
   - Customize cleaning patterns for your data

3. **Production Deployment**
   - Set up proper logging
   - Configure error monitoring
   - Set up API rate limiting
   - Add authentication if needed

### If Tests Fail ❌

1. **Check Prerequisites**
   - Node.js v16+ installed
   - Python 3.8+ installed
   - All dependencies installed
   - Services running on correct ports

2. **Review Logs**
   - Backend console output
   - AI service console output
   - Check for error messages

3. **Ask for Help**
   - Share error messages
   - Share service logs
   - Share test results

---

## Additional Test Commands

### Test Individual Layers

**Layer 1 - Data Cleaning (implicit in upload):**
```bash
# Check cleaning report in upload response
curl -X POST http://localhost:5000/workflow/upload-with-mapping \
  -F "logs=@test.csv" \
  -F "sop_id=1" \
  -F 'column_mapping={...}' | jq '.data.cleaning_report'
```

**Layer 2 - Deviation Detection:**
```bash
# Use existing analyze endpoint (batched internally)
curl -X POST http://localhost:5000/workflow/analyze
```

**Layer 3 - Statistical Analysis:**
```bash
# Included in comprehensive analysis response
curl -X POST http://localhost:5000/workflow/analyze-comprehensive | jq '.data.statistical_insights'
```

**Layer 4 - ML Sampling:**
```bash
# Direct ML API test
curl -X POST http://localhost:8000/ml/sample \
  -H "Content-Type: application/json" \
  -d '{
    "deviations": [...],
    "statistical_insights": {},
    "target_sample_size": 75
  }'
```

**Layer 5 - AI Pattern Analysis:**
```bash
# Direct pattern analysis
curl -X POST http://localhost:8000/ai/deviation/analyze-patterns \
  -H "Content-Type: application/json" \
  -d '{
    "deviations": [...],
    "cluster_statistics": {}
  }'
```

---

## Performance Benchmarks

Expected performance on standard hardware (4 cores, 16GB RAM):

| Dataset Size | Rows | Deviations | Layer 2 | Layer 3 | Layer 4 | Layer 5 | Total |
|--------------|------|------------|---------|---------|---------|---------|-------|
| Small (100)  | 800  | 45         | 15s     | 2s      | 5s      | 30s     | 52s   |
| Medium (500) | 4000 | 250        | 45s     | 5s      | 15s     | 45s     | 110s  |
| Large (1500) | 12000| 800        | 120s    | 10s     | 30s     | 60s     | 220s  |
| XL (3000)    | 24000| 1600       | 180s    | 15s     | 45s     | 75s     | 315s  |

*Times are approximate and may vary based on:*
- Hardware specifications
- Claude API response times
- Network latency
- Data complexity

---

## Success! What Now?

Once testing is successful:

1. **Document Your Findings**
   - Record performance metrics
   - Note any issues encountered
   - Document configuration changes

2. **Prepare for Production**
   - Set up monitoring
   - Configure backups
   - Plan scaling strategy

3. **Train Your Team**
   - Share ML system explanation
   - Demonstrate pipeline features
   - Create user documentation

4. **Iterate and Improve**
   - Collect user feedback
   - Monitor cost vs. quality
   - Fine-tune parameters based on usage
