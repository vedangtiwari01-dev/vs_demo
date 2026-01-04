# Prompt Fix for JSON Parsing Issues

## Problem
Claude API was returning malformed JSON with nested objects in the `recommendations` array:
```json
"recommendations": [
  {
    "recommendation": "Configure system...",
    "timeline": "Within 2 months"
  }
]
```

This caused JSON parsing errors: `Expecting ',' delimiter: line 193 column 6 (char 16553)`

---

## Root Cause
The prompt didn't explicitly prevent Claude from adding extra fields to recommendations. Claude was being "helpful" by adding structure (timeline, priority, impact) that broke the JSON format.

---

## Solution Applied

### Fix 1: Enhanced Prompt Instructions
**File:** `ai-service/app/services/claude/prompts.py` (lines 519-529)

Added CRITICAL JSON FORMATTING RULES to the prompt:

```
CRITICAL JSON FORMATTING RULES - READ CAREFULLY:
1. "recommendations" MUST be an array of simple strings ONLY - NO objects with fields
2. Each recommendation is just a plain string - do NOT add "priority", "timeline", "impact" fields
3. Keep recommendations concise (1-2 sentences each)
4. Do NOT add trailing commas before closing brackets ] or braces }
5. If you want to show priority, include it IN the string: "[HIGH] Do this immediately"
6. Do NOT create objects inside the recommendations array
7. WRONG: {"recommendation": "text", "timeline": "2 months"}
8. CORRECT: "Do this within 2 months"
```

**Why this works:**
- Explicitly shows Claude what NOT to do (with examples)
- Shows the CORRECT format vs WRONG format
- Tells Claude how to include priority/timeline info (inside the string, not as separate fields)

### Fix 2: Save Failed JSON for Debugging
**File:** `ai-service/app/services/deviation/notes_analyzer.py` (lines 167-171)

Added automatic JSON dump to temp file when parsing fails:

```python
# Log the full JSON to a temp file for debugging
import tempfile
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    f.write(json_text)
    logger.error(f"Full JSON saved to: {f.name}")
```

**Why this helps:**
- If parsing still fails, we get the complete JSON for manual inspection
- Temp file path shown in error logs
- Can examine exact malformation and add more repair logic if needed

---

## Expected Result

### Before Fix:
```json
"recommendations": [
  {
    "recommendation": "Configure system to require officer comment",
    "timeline": "Within 2 months"
  },
  {
    "recommendation": "Implement real-time monitoring",
    "priority": "high"
  }
]
```
❌ **Result:** JSON parsing error at position 16553

### After Fix:
```json
"recommendations": [
  "Configure system to require officer comment within 2 months",
  "Implement real-time monitoring (HIGH priority)",
  "Add automated alerts for critical deviations"
]
```
✅ **Result:** Valid JSON, parses successfully

---

## Testing Instructions

1. **Restart AI service:**
   ```bash
   cd ai-service
   .venv\Scripts\python -m uvicorn main:app --reload
   ```

2. **Run test:**
   ```bash
   cd ..
   python test_intensive.py
   ```

3. **Expected improvements:**
   - ✅ JSON parsing should succeed
   - ✅ Recommendations displayed as simple strings
   - ✅ If still fails, temp file path shown in logs for inspection

4. **If JSON parsing still fails:**
   - Check AI service logs for: `Full JSON saved to: C:\Users\...\tmp...\....json`
   - Open that file and inspect what Claude returned
   - Share the file path and I'll add more specific repair logic

---

## Alternative Solutions (If This Doesn't Work)

### Option A: Install json-repair Library (Most Robust)
```bash
cd ai-service
.venv\Scripts\pip install json-repair
```

Then modify `notes_analyzer.py`:
```python
from json_repair import repair_json

# Before json.loads():
json_text = repair_json(json_text)
pattern_analysis = json.loads(json_text)
```

**Pros:** Professional-grade JSON repair, handles 99% of malformations
**Cons:** Additional dependency

### Option B: Use json5 Parser (Lenient)
```bash
cd ai-service
.venv\Scripts\pip install json5
```

Then modify:
```python
import json5
pattern_analysis = json5.loads(json_text)  # Allows trailing commas, comments
```

**Pros:** Natively handles trailing commas and other relaxed JSON
**Cons:** Additional dependency, doesn't fix all malformations

### Option C: Regex Fallback Parser
If JSON is completely broken, extract key fields using regex:

```python
except json.JSONDecodeError:
    # Fallback: extract patterns manually
    patterns = re.findall(r'"pattern":\s*"([^"]+)"', response_text)
    rules = re.findall(r'"rule":\s*"([^"]+)"', response_text)
    recommendations = re.findall(r'"recommendations":\s*\[(.*?)\]', response_text, re.DOTALL)
```

**Pros:** Always works (doesn't depend on valid JSON)
**Cons:** Less reliable, might miss nested data

---

## Summary

**Changes Made:**
1. ✅ Added 8 explicit JSON formatting rules to prompt
2. ✅ Showed Claude WRONG vs CORRECT examples
3. ✅ Auto-save failed JSON to temp file for debugging

**What This Fixes:**
- ✅ Prevents Claude from adding nested objects in recommendations
- ✅ Tells Claude how to include priority/timeline (in string, not as field)
- ✅ Provides debugging output if parsing still fails

**Next Steps:**
1. Restart AI service
2. Run test
3. If still fails, check temp file path in logs and share with me
4. If needed, I'll implement Option A (json-repair library) for 99% reliability

The explicit instructions should guide Claude to return properly formatted JSON. If it still fails, we'll use the temp file to see exactly what's wrong and implement Option A as a permanent fix.
