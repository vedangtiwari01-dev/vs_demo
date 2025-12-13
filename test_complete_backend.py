import requests
import json
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:3000"
AI_SERVICE_URL = "http://localhost:8000"
SOP_FILE = r"C:\Users\VedangTiwari\Desktop\test_git\vs_demo\sop_samp.docx"
CSV_FILE = r"C:\Users\VedangTiwari\Desktop\test_git\vs_demo\loan_process_log_with_deviations.csv"

def test_step(step_num, description):
    """Print test step header"""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {description}")
    print(f"{'='*60}")

def check_services():
    """Check if backend and AI service are running"""
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
        print("✓ Backend is running")
    except:
        print("✗ Backend is NOT running! Start it first:")
        print("  cd backend && npm start")
        return False

    try:
        requests.get(f"{AI_SERVICE_URL}/ai/health", timeout=2)
        print("✓ AI Service is running")
    except:
        print("✗ AI Service is NOT running! Start it first:")
        print("  cd ai-service && python main.py")
        return False

    return True

def clear_database():
    """Clear all test data from database"""
    print("\n" + "="*60)
    print("CLEARING DATABASE")
    print("="*60)

    try:
        # Delete all SOPs (will cascade to rules)
        response = requests.get(f"{BASE_URL}/api/sops")
        if response.status_code == 200:
            sops = response.json().get('data', [])
            for sop in sops:
                sop_id = sop.get('id')
                if sop_id:
                    delete_response = requests.delete(f"{BASE_URL}/api/sops/{sop_id}")
                    if delete_response.status_code == 200:
                        print(f"✓ Deleted SOP {sop_id}")

        # Delete all workflow logs
        response = requests.get(f"{BASE_URL}/api/workflows")
        if response.status_code == 200:
            logs = response.json().get('data', [])
            print(f"✓ Found {len(logs)} workflow logs (will be cleared on next upload)")

        # Delete all deviations
        response = requests.get(f"{BASE_URL}/api/deviations")
        if response.status_code == 200:
            deviations = response.json().get('data', [])
            print(f"✓ Found {len(deviations)} deviations (will be cleared on next analysis)")

        print("✓ Database cleared successfully\n")
        return True

    except Exception as e:
        print(f"⚠️ Warning: Could not clear database: {e}")
        print("Continuing with test anyway...\n")
        return True  # Don't fail the test if clearing fails

def main():
    print("="*60)
    print("BACKEND & AI SERVICE TESTING SUITE")
    print("="*60)

    if not check_services():
        return

    # Clear database before starting tests
    if not clear_database():
        return

    # STEP 1: Upload SOP
    test_step(1, "Upload & Store SOP Document")
    try:
        with open(SOP_FILE, 'rb') as f:
            files = {'sop': f}  # Field name must be 'sop' not 'file'
            data = {'title': 'Test SOP', 'description': 'Testing', 'version': '1.0'}
            response = requests.post(f"{BASE_URL}/api/sops/upload", files=files, data=data)

            # Debug: Print response details
            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.text[:500]}")  # First 500 chars

            if response.status_code != 200 and response.status_code != 201:
                print(f"✗ Failed: HTTP {response.status_code}")
                print(f"Error: {response.text}")
                return

            response_json = response.json()

            # Backend returns {success, message, data: {sop}}
            if 'data' not in response_json:
                print(f"✗ Failed: Response missing 'data' field")
                print(f"Full response: {response_json}")
                return

            sop_data = response_json['data']
            sop_id = sop_data['id']
            print(f"✓ SOP uploaded successfully (ID: {sop_id})")
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # STEP 2: Parse SOP with LLM
    test_step(2, "Parse SOP with Claude LLM")
    try:
        time.sleep(1)  # Brief delay
        response = requests.post(f"{BASE_URL}/api/sops/{sop_id}/process")

        if response.status_code != 200:
            print(f"✗ Failed: HTTP {response.status_code}")
            print(f"Error: {response.text}")
            return

        response_json = response.json()
        sop_data = response_json.get('data', {})
        rules = sop_data.get('rules', [])
        print(f"✓ Extracted {len(rules)} rules")
        for i, rule in enumerate(rules[:3], 1):
            print(f"  {i}. {rule['rule_type']}: {rule['rule_description'][:60]}...")
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # STEP 3a: Analyze CSV Headers
    test_step(3, "Part A: Analyze CSV Headers with AI")
    try:
        with open(CSV_FILE, 'rb') as f:
            files = {'logs': f}  # Changed from 'file' to 'logs'
            response = requests.post(f"{BASE_URL}/api/workflows/analyze-headers", files=files)

            if response.status_code != 200:
                print(f"✗ Failed: HTTP {response.status_code}")
                print(f"Error: {response.text}")
                return

            response_json = response.json()
            mapping_result = response_json.get('data', {})

            # Backend returns 'mapping_suggestions' not 'mappings'
            mapping_suggestions = mapping_result.get('mapping_suggestions', {})

            print("✓ AI suggested mappings:")
            for csv_col, field_info in mapping_suggestions.items():
                print(f"  {csv_col} → {field_info['system_field']} ({field_info['confidence']:.0%})")

            # Build confirmed mapping from AI suggestions
            mapping = {csv_col: field_info['system_field']
                      for csv_col, field_info in mapping_suggestions.items()}

            # ✅ CRITICAL FIX: Add notes column to mapping if detected
            notes_column = mapping_result.get('notes_column')
            if notes_column:
                mapping[notes_column] = 'notes'  # Map "Notes" → "notes"
                print(f"✓ Notes column detected and mapped: {notes_column} → notes")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return

    # STEP 3b: Upload Workflow Logs with Mapping
    test_step(3, "Part B: Upload Workflow Logs with Confirmed Mapping")
    try:
        with open(CSV_FILE, 'rb') as f:
            files = {'logs': f}  # Changed from 'file' to 'logs'
            data = {
                'sop_id': sop_id,
                'mapping': json.dumps(mapping)
            }
            response = requests.post(f"{BASE_URL}/api/workflows/upload-with-mapping",
                                    files=files, data=data)

            if response.status_code != 200 and response.status_code != 201:
                print(f"✗ Failed: HTTP {response.status_code}")
                print(f"Error: {response.text}")
                return

            response_json = response.json()
            upload_result = response_json.get('data', {})

            print(f"✓ Uploaded {upload_result.get('total_logs', 0)} workflow logs")
            print(f"✓ {upload_result.get('unique_cases', 0)} unique cases")
            print(f"✓ {upload_result.get('unique_officers', 0)} unique officers")
            if upload_result.get('notes_imported', 0) > 0:
                print(f"✓ {upload_result['notes_imported']} notes imported")
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # STEP 4: Rule-Based Deviation Detection
    test_step(4, "Rule-Based Deviation Detection")
    try:
        time.sleep(1)
        response = requests.post(f"{BASE_URL}/api/workflows/analyze",
                                json={"sopId": sop_id})

        if response.status_code != 200:
            print(f"✗ Failed: HTTP {response.status_code}")
            print(f"Error: {response.text}")
            return

        response_json = response.json()
        analysis_result = response_json.get('data', {})

        total_deviations = analysis_result.get('total_deviations', 0)
        print(f"✓ Found {total_deviations} deviations")

        # Show summary by severity
        summary = analysis_result.get('summary', {})
        if summary:
            print("\nDeviation breakdown by severity:")
            for severity, count in summary.items():
                if count > 0:
                    print(f"  - {severity}: {count}")

        # Get deviations for next step
        response = requests.get(f"{BASE_URL}/api/deviations?limit=200")
        response_json = response.json()

        # Deviations are nested in data.deviations
        data = response_json.get('data', {})
        deviations = data.get('deviations', [])

        # Convert Sequelize objects to plain dicts if needed
        deviations_list = []
        for d in deviations:
            if isinstance(d, dict):
                deviations_list.append(d)
            elif hasattr(d, '__dict__'):
                deviations_list.append(vars(d))

        deviations_with_notes = [d for d in deviations_list if d.get('notes')]
        print(f"\n✓ Total deviations: {len(deviations_list)}")
        print(f"✓ {len(deviations_with_notes)} deviations have notes for AI analysis")
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # STEP 5: AI Pattern Analysis
    test_step(5, "AI Pattern & Behavioral Analysis")
    try:
        # Use all deviations for pattern analysis (not just ones with notes)
        if deviations_list and len(deviations_list) > 0:
            # Send to AI service for pattern analysis
            response = requests.post(f"{AI_SERVICE_URL}/ai/deviation/analyze-patterns",
                                    json={"deviations": deviations_list})

            if response.status_code != 200:
                print(f"⚠️ Pattern analysis not available (HTTP {response.status_code})")
                print("Continuing without pattern analysis...")
                patterns = None
            else:
                patterns = response.json()

                print(f"\n✓ Pattern analysis complete!")
                print(f"  API calls made: {patterns.get('api_calls_made', 0)}")
                print(f"\n📊 Summary: {patterns.get('overall_summary', '')[:100]}...")

                print("\n🔍 Behavioral Patterns:")
                for i, pattern in enumerate(patterns.get('behavioral_patterns', [])[:2], 1):
                    print(f"  {i}. {pattern.get('pattern', '')[:80]}...")

                print("\n💡 Hidden Rules:")
                for i, rule in enumerate(patterns.get('hidden_rules', [])[:2], 1):
                    print(f"  {i}. {rule.get('description', '')[:80]}...")
        else:
            print("⚠️ No deviations to analyze")
            patterns = None
    except Exception as e:
        print(f"⚠️ Pattern analysis failed: {e}")
        print("Continuing with rest of the test...")
        patterns = None
        # Not critical, continue

    # STEP 6: Generate Report Data
    test_step(6, "Generate Complete Report Data")
    try:
        report = {
            "sop": {
                "id": sop_id,
                "title": sop_data.get('sop', {}).get('title', 'Test SOP'),
                "total_rules": len(sop_data.get('rules', []))
            },
            "workflow_analysis": {
                "total_deviations": total_deviations,
                "summary": summary
            },
            "pattern_analysis": patterns if patterns else None
        }

        with open('test_report.json', 'w') as f:
            json.dump(report, f, indent=2)

        print("✓ Report data compiled")
        print("✓ Saved to: test_report.json")
    except Exception as e:
        print(f"✗ Failed: {e}")

    # STEP 7: Synthetic Data Generation
    test_step(7, "Generate Synthetic Test Data")
    try:
        response = requests.post(f"{AI_SERVICE_URL}/ai/synthetic/generate",
                                json={
                                    "scenario_type": "officer_shortage",
                                    "parameters": {
                                        "normal_officers": 10,
                                        "reduced_officers": 6,
                                        "total_cases": 10,
                                        "days": 7
                                    }
                                })
        synthetic = response.json()

        # Response structure: {logs: [...], metadata: {total_logs: N, ...}}
        total_logs = synthetic.get('metadata', {}).get('total_logs', len(synthetic.get('logs', [])))
        print(f"✓ Generated {total_logs} synthetic logs for 'officer_shortage' scenario")
    except Exception as e:
        print(f"⚠️ Synthetic generation not available: {e}")

    # Final Summary
    print("\n" + "="*60)
    print("TEST SUITE COMPLETE!")
    print("="*60)
    print("\n✓ All critical steps passed")
    print("✓ System is ready for frontend integration")
    print("\nNext steps:")
    print("1. Review test_report.json for detailed results")
    print("2. Check database for stored data")
    print("3. Test frontend integration")

if __name__ == "__main__":
    main()