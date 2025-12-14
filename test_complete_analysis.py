"""
Complete Analysis Testing - Test the full workflow with database uploads
"""
import requests
import json
from datetime import datetime

BACKEND_URL = "http://localhost:3000/api"

def print_section(title):
    print("\n" + "="*80)
    print(title)
    print("="*80)

def print_subsection(title):
    print("\n" + "-"*80)
    print(title)
    print("-"*80)

def main():
    print_section("COMPLETE ANALYSIS WORKFLOW TEST")

    try:
        # Step 1: Check database
        print_subsection("[1/3] Checking uploaded data in database...")

        # Check SOPs
        sops_response = requests.get(f"{BACKEND_URL}/sops")
        if sops_response.status_code == 200:
            sops_data = sops_response.json()
            sops = sops_data.get('data', sops_data)
            print(f"✓ Found {len(sops)} SOPs in database")
            if len(sops) > 0:
                print(f"   - Using: {sops[0]['title']} (ID: {sops[0]['id']})")
                if sops[0].get('rules'):
                    print(f"   - Rules extracted: {len(sops[0]['rules'])}")
        else:
            print(f"✗ Failed to fetch SOPs: {sops_response.status_code}")
            return

        # Check workflows
        workflows_response = requests.get(f"{BACKEND_URL}/workflows/list-files")
        if workflows_response.status_code == 200:
            workflows_data = workflows_response.json()
            # Handle nested data structure
            files = workflows_data.get('data', {}).get('files') or workflows_data.get('files', [])
            print(f"✓ Found {len(files)} workflow files in database")
            if len(files) > 0:
                print(f"   - Using: {files[0]['filename']}")
                print(f"   - Total logs: {files[0]['total_logs']}")
                print(f"   - Unique cases: {files[0]['unique_cases']}")
        else:
            print(f"✗ Failed to fetch workflows: {workflows_response.status_code}")
            return

        if len(sops) == 0 or len(files) == 0:
            print("\n❌ ERROR: Need at least 1 SOP and 1 workflow file uploaded")
            print("Please upload files first before running analysis")
            return

        # Step 2: Run deviation detection
        print_subsection("[2/3] Running deviation detection...")

        deviation_response = requests.post(f"{BACKEND_URL}/workflows/analyze")

        if deviation_response.status_code == 200:
            deviation_data = deviation_response.json()

            print("✓ Deviation detection complete!")
            print("\n--- RESPONSE STRUCTURE ---")
            print(f"Keys: {list(deviation_data.keys())}")

            # Extract data (handle nested structure)
            data = deviation_data.get('data', deviation_data)

            print(f"\nData keys: {list(data.keys())}")

            if 'deviations' in data:
                print(f"\n✓ Deviations found: {len(data['deviations'])}")
                if len(data['deviations']) > 0:
                    print("\nFirst deviation:")
                    print(json.dumps(data['deviations'][0], indent=2, default=str))

            if 'summary' in data:
                print("\n--- SUMMARY STRUCTURE ---")
                print(json.dumps(data['summary'], indent=2, default=str))

            # Save for pattern analysis
            deviations_count = len(data.get('deviations', []))

        else:
            print(f"✗ Deviation detection failed: {deviation_response.status_code}")
            print(f"Response: {deviation_response.text}")
            return

        # Step 3: Run pattern analysis
        print_subsection("[3/3] Running pattern analysis (this may take a few minutes)...")
        print("Note: This analyzes up to 50 most recent deviations")

        pattern_response = requests.post(f"{BACKEND_URL}/workflows/analyze-patterns")

        if pattern_response.status_code == 200:
            pattern_data = pattern_response.json()

            print("✓ Pattern analysis complete!")
            print("\n--- RESPONSE STRUCTURE ---")
            print(f"Keys: {list(pattern_data.keys())}")

            # Extract data
            data = pattern_data.get('data', pattern_data)
            print(f"\nData keys: {list(data.keys())}")

            if 'patterns' in data:
                patterns = data['patterns']
                print("\n--- PATTERNS STRUCTURE ---")
                print(f"Pattern keys: {list(patterns.keys())}")

                # Show pattern details
                if 'overall_summary' in patterns:
                    print(f"\nOverall Summary:")
                    print(f"  {patterns['overall_summary'][:200]}...")

                if 'behavioral_patterns' in patterns:
                    print(f"\nBehavioral Patterns: {len(patterns['behavioral_patterns'])} found")
                    if len(patterns['behavioral_patterns']) > 0:
                        print(f"  First pattern: {patterns['behavioral_patterns'][0].get('pattern', 'N/A')[:100]}...")

                if 'hidden_rules' in patterns:
                    print(f"\nHidden Rules: {len(patterns['hidden_rules'])} found")

                if 'systemic_issues' in patterns:
                    print(f"\nSystemic Issues: {len(patterns['systemic_issues'])} found")

            print(f"\nDeviations analyzed: {data.get('deviations_analyzed', 'N/A')}")
            print(f"API calls made: {data.get('api_calls_made', 'N/A')}")

        else:
            print(f"✗ Pattern analysis failed: {pattern_response.status_code}")
            print(f"Response: {pattern_response.text}")
            if pattern_response.status_code == 500:
                print("\nPossible issues:")
                print("- AI service timeout (reduce limit in workflow.controller.js)")
                print("- AI service not running")
                print("- Claude API rate limit")
            return

        # Summary
        print_section("TEST COMPLETE")
        print("\n✅ All tests passed!")
        print(f"\nDeviation Detection: SUCCESS ({deviations_count} deviations found)")
        print(f"Pattern Analysis: SUCCESS")
        print("\n📝 Next steps:")
        print("1. Check if summary structure matches frontend expectations")
        print("2. Test frontend with this data")
        print("3. Fix any data structure mismatches")

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend")
        print("Make sure backend is running on http://localhost:3000")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
