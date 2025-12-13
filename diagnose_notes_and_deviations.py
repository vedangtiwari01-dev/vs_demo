"""
Diagnostic Script: Deep Dive into Notes and Deviations
Investigates what happens to data after Step 3 (workflow upload)
"""

import requests
import json
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:3000"
AI_SERVICE_URL = "http://localhost:8000"

def print_section(title):
    """Print section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def check_workflow_logs():
    """Check if workflow logs have notes in metadata"""
    print_section("STEP 1: Checking WorkflowLog Metadata for Notes")

    try:
        response = requests.get(f"{BASE_URL}/api/workflows?limit=10")
        if response.status_code != 200:
            print(f"✗ Failed to fetch workflow logs: {response.status_code}")
            return None

        data = response.json().get('data', {})
        logs = data.get('logs', [])

        print(f"\n✓ Found {len(logs)} workflow logs (showing first 10)")

        logs_with_notes = 0
        sample_logs = []

        for i, log in enumerate(logs[:10], 1):
            metadata = log.get('metadata', {})
            notes = metadata.get('notes') if isinstance(metadata, dict) else None

            print(f"\nLog {i}:")
            print(f"  - ID: {log.get('id')}")
            print(f"  - Case ID: {log.get('case_id')}")
            print(f"  - Officer ID: {log.get('officer_id')}")
            print(f"  - Step: {log.get('step_name')}")
            print(f"  - Metadata Type: {type(metadata)}")
            print(f"  - Metadata: {json.dumps(metadata, indent=4) if isinstance(metadata, dict) else metadata}")
            print(f"  - Notes: {notes if notes else 'NO NOTES'}")

            if notes:
                logs_with_notes += 1
                sample_logs.append({
                    'log_id': log.get('id'),
                    'case_id': log.get('case_id'),
                    'officer_id': log.get('officer_id'),
                    'notes': notes
                })

        print(f"\n📊 SUMMARY:")
        print(f"  - Total logs checked: {len(logs)}")
        print(f"  - Logs with notes: {logs_with_notes}")
        print(f"  - Logs without notes: {len(logs) - logs_with_notes}")

        return sample_logs

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_deviations():
    """Check if deviations have notes field"""
    print_section("STEP 2: Checking Deviation Records for Notes")

    try:
        response = requests.get(f"{BASE_URL}/api/deviations?limit=20")
        if response.status_code != 200:
            print(f"✗ Failed to fetch deviations: {response.status_code}")
            return None

        data = response.json().get('data', {})
        deviations = data.get('deviations', [])

        print(f"\n✓ Found {len(deviations)} deviations (showing first 20)")

        deviations_with_notes = 0
        deviations_with_llm_reasoning = 0
        sample_deviations = []

        for i, deviation in enumerate(deviations[:20], 1):
            notes = deviation.get('notes')
            llm_reasoning = deviation.get('llm_reasoning')

            print(f"\nDeviation {i}:")
            print(f"  - ID: {deviation.get('id')}")
            print(f"  - Case ID: {deviation.get('case_id')}")
            print(f"  - Officer ID: {deviation.get('officer_id')}")
            print(f"  - Type: {deviation.get('deviation_type')}")
            print(f"  - Severity: {deviation.get('severity')}")
            print(f"  - Description: {deviation.get('description', '')[:60]}...")
            print(f"  - Notes: {notes if notes else 'NO NOTES'}")
            print(f"  - LLM Reasoning: {llm_reasoning if llm_reasoning else 'NO LLM REASONING'}")

            if notes:
                deviations_with_notes += 1
            if llm_reasoning:
                deviations_with_llm_reasoning += 1

            if i <= 5:  # Save first 5 for pattern analysis test
                sample_deviations.append(deviation)

        print(f"\n📊 SUMMARY:")
        print(f"  - Total deviations: {len(deviations)}")
        print(f"  - Deviations with notes: {deviations_with_notes}")
        print(f"  - Deviations with LLM reasoning: {deviations_with_llm_reasoning}")
        print(f"  - Deviations without notes: {len(deviations) - deviations_with_notes}")

        return sample_deviations

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_pattern_analysis_endpoint(sample_deviations):
    """Test the AI pattern analysis endpoint with correct URL"""
    print_section("STEP 3: Testing AI Pattern Analysis Endpoint")

    if not sample_deviations:
        print("⚠️ No sample deviations available for testing")
        return False

    # Try both possible endpoint paths
    endpoints = [
        f"{AI_SERVICE_URL}/ai/deviation/analyze-patterns",
        f"{AI_SERVICE_URL}/api/deviation/analyze-patterns",
    ]

    for endpoint in endpoints:
        print(f"\nTrying endpoint: {endpoint}")

        try:
            response = requests.post(
                endpoint,
                json={"deviations": sample_deviations},
                timeout=60
            )

            print(f"  Status Code: {response.status_code}")

            if response.status_code == 200:
                print("  ✓ Endpoint is WORKING!")
                result = response.json()
                print(f"\n  Response Summary:")
                print(f"    - API calls made: {result.get('api_calls_made', 0)}")
                print(f"    - Deviations analyzed: {result.get('deviations_analyzed', 0)}")
                print(f"    - Summary: {result.get('overall_summary', '')[:100]}...")
                return True
            elif response.status_code == 404:
                print("  ✗ Endpoint NOT FOUND (404)")
            else:
                print(f"  ✗ Error: {response.text[:200]}")

        except Exception as e:
            print(f"  ✗ Exception: {e}")

    return False

def check_ai_service_routes():
    """Check what routes are available in AI service"""
    print_section("STEP 4: Checking AI Service Available Routes")

    print("\nAttempting to discover available endpoints...")

    test_endpoints = [
        "/health",
        "/ai/health",
        "/ai/sop/parse",
        "/ai/sop/extract-rules",
        "/ai/mapping/analyze-headers",
        "/ai/deviation/detect",
        "/ai/deviation/analyze-patterns",
        "/ai/pattern/analyze",
        "/api/deviation/analyze-patterns",
        "/api/synthetic/generate-logs",
        "/ai/synthetic/generate-logs",
    ]

    print("\nTesting endpoints:")
    working_endpoints = []

    for endpoint in test_endpoints:
        try:
            # Use GET for health/discovery, HEAD for others
            url = f"{AI_SERVICE_URL}{endpoint}"
            response = requests.get(url, timeout=2)

            if response.status_code == 404:
                print(f"  ✗ {endpoint} - NOT FOUND")
            elif response.status_code == 405:
                print(f"  ~ {endpoint} - EXISTS (Method Not Allowed - needs POST)")
                working_endpoints.append(endpoint)
            elif response.status_code in [200, 422]:  # 422 = validation error (endpoint exists)
                print(f"  ✓ {endpoint} - EXISTS")
                working_endpoints.append(endpoint)
            else:
                print(f"  ? {endpoint} - Status {response.status_code}")
        except Exception as e:
            print(f"  ✗ {endpoint} - Error: {str(e)[:50]}")

    print(f"\n✓ Found {len(working_endpoints)} working endpoints")
    return working_endpoints

def investigate_notes_flow():
    """Investigate how notes flow from CSV to deviations"""
    print_section("STEP 5: Investigating Notes Flow")

    print("\nExpected Flow:")
    print("  1. CSV uploaded with 'Comments' column")
    print("  2. Backend extracts notes from 'Comments' column")
    print("  3. Notes stored in WorkflowLog.metadata as {notes: '...'}")
    print("  4. During deviation detection, backend should:")
    print("     a. Fetch WorkflowLog records for each case")
    print("     b. Extract notes from metadata")
    print("     c. Pass notes to AI service for context")
    print("     d. Store notes in Deviation.notes field")
    print("  5. Deviations should have notes for AI pattern analysis")

    print("\n❓ QUESTIONS TO INVESTIGATE:")
    print("  Q1: Are notes being extracted from CSV during upload?")
    print("  Q2: Are notes being stored in WorkflowLog.metadata?")
    print("  Q3: Is deviation detection fetching WorkflowLog notes?")
    print("  Q4: Are notes being passed to AI service?")
    print("  Q5: Are notes being saved in Deviation.notes field?")

    print("\n🔍 INVESTIGATION RESULTS:")

    # Check Q1 & Q2
    sample_logs = check_workflow_logs()
    if sample_logs and len(sample_logs) > 0:
        print("\n  ✓ Q1 & Q2: YES - Notes are in WorkflowLog.metadata")
    else:
        print("\n  ✗ Q1 & Q2: NO - Notes are NOT in WorkflowLog.metadata")

    # Check Q5
    sample_deviations = check_deviations()
    if sample_deviations and any(d.get('notes') for d in sample_deviations):
        print("\n  ✓ Q5: YES - Notes are in Deviation.notes field")
    else:
        print("\n  ✗ Q5: NO - Notes are NOT in Deviation.notes field")
        print("\n  💡 LIKELY CAUSE:")
        print("     The backend deviation detection is NOT copying notes")
        print("     from WorkflowLog to Deviation records.")

def main():
    print("="*70)
    print("  DIAGNOSTIC SCRIPT: Notes and Deviations Deep Dive")
    print("="*70)
    print("\nThis script investigates:")
    print("  1. Where notes are stored after CSV upload")
    print("  2. Why deviations don't have notes")
    print("  3. Why AI pattern analysis is failing")

    # Step 1: Check workflow logs for notes
    sample_logs = check_workflow_logs()

    # Step 2: Check deviations for notes
    sample_deviations = check_deviations()

    # Step 3: Test pattern analysis endpoint
    if sample_deviations:
        test_pattern_analysis_endpoint(sample_deviations)

    # Step 4: Check AI service routes
    check_ai_service_routes()

    # Step 5: Summarize investigation
    investigate_notes_flow()

    # Final recommendations
    print_section("RECOMMENDATIONS")

    print("\n🔧 FIXES NEEDED:")
    print("\n1. Fix AI Pattern Analysis Endpoint URL:")
    print("   - Change from: /api/deviation/analyze-patterns")
    print("   - Change to:   /ai/deviation/analyze-patterns")

    print("\n2. Fix Notes Flow in Backend:")
    print("   - File: backend/src/controllers/workflow.controller.js")
    print("   - Function: analyzeWorkflow()")
    print("   - Need to:")
    print("     a. Fetch WorkflowLog records for each deviation")
    print("     b. Extract notes from WorkflowLog.metadata")
    print("     c. Attach notes to Deviation record when creating")

    print("\n3. Verify AI Service Endpoints:")
    print("   - Ensure /ai/deviation/analyze-patterns exists")
    print("   - Ensure /ai/synthetic/generate-logs exists")
    print("   - Check app/main.py for router registration")

if __name__ == "__main__":
    main()
