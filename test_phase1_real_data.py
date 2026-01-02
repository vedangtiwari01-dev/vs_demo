"""
Test Phase 1 with REAL database data

This script connects to your database and tests the layered approach
with your actual SOP and workflow data.

Requirements:
1. Backend database must be accessible
2. You must have uploaded SOP and workflow data
3. Deviations must have been detected

Run this:
    python test_phase1_real_data.py
"""

import sys
import os
import json
import requests
from datetime import datetime

# Colors for output
class Color:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Color.BOLD}{'='*80}{Color.END}")
    print(f"{Color.BOLD}{text}{Color.END}")
    print(f"{Color.BOLD}{'='*80}{Color.END}\n")

def print_success(text):
    print(f"{Color.GREEN}✅ {text}{Color.END}")

def print_warning(text):
    print(f"{Color.YELLOW}⚠️  {text}{Color.END}")

def print_error(text):
    print(f"{Color.RED}❌ {text}{Color.END}")

def check_services():
    """Check if backend and AI service are running."""
    print_header("CHECKING SERVICES")

    # Check backend
    try:
        response = requests.get('http://localhost:3000/api/health', timeout=5)
        if response.status_code == 200:
            print_success("Backend is running (http://localhost:3000)")
            backend_ok = True
        else:
            print_error(f"Backend returned status {response.status_code}")
            backend_ok = False
    except Exception as e:
        print_error(f"Backend is not running: {e}")
        print("Start it with: cd backend && npm start")
        backend_ok = False

    # Check AI service
    try:
        response = requests.get('http://localhost:8000/ai/health', timeout=5)
        if response.status_code == 200:
            print_success("AI service is running (http://localhost:8000)")
            ai_ok = True
        else:
            print_error(f"AI service returned status {response.status_code}")
            ai_ok = False
    except Exception as e:
        print_error(f"AI service is not running: {e}")
        print("Start it with: cd ai-service && python -m uvicorn main:app --reload")
        ai_ok = False

    return backend_ok and ai_ok

def get_deviations():
    """Fetch deviations from backend."""
    print_header("FETCHING DEVIATIONS FROM DATABASE")

    try:
        # Get deviations from backend API
        response = requests.get('http://localhost:3000/api/deviations', timeout=10)

        if response.status_code == 200:
            data = response.json()

            # Debug: Print response structure
            print(f"📦 Response structure: {list(data.keys())}")

            # Try different response formats
            deviations = None

            # Format 1: { success, data: { deviations: [...] } }
            if 'data' in data and isinstance(data['data'], dict):
                data_obj = data['data']
                print(f"📦 Data object keys: {list(data_obj.keys())}")
                if 'deviations' in data_obj:
                    deviations = data_obj['deviations']
                elif 'rows' in data_obj:
                    deviations = data_obj['rows']
                elif 'items' in data_obj:
                    deviations = data_obj['items']

            # Format 2: { data: [...] } - direct list
            elif 'data' in data and isinstance(data['data'], list):
                deviations = data['data']

            # Format 3: { deviations: [...] }
            elif 'deviations' in data:
                deviations = data['deviations']

            # Format 4: [...] - direct array
            elif isinstance(data, list):
                deviations = data

            if deviations is None:
                print_error(f"Could not find deviations in response")
                print(f"Response structure: {str(data)[:300]}")
                return None

            # Ensure deviations is a list
            if not isinstance(deviations, list):
                print_error(f"Deviations is not a list: {type(deviations)}")
                print(f"Deviations value: {str(deviations)[:200]}")
                return None

            if len(deviations) == 0:
                print_warning("No deviations found in database")
                print("\n💡 To get deviations:")
                print("  1. Upload SOP document")
                print("  2. Upload workflow logs CSV")
                print("  3. Click 'Analyze Workflow' to detect deviations")
                return None

            print_success(f"Found {len(deviations)} deviations in database")

            # Show sample - with better error handling
            try:
                print(f"\n📋 Sample deviation:")
                sample = deviations[0]
                print(f"  - Case ID: {sample.get('case_id', 'N/A')}")
                print(f"  - Officer ID: {sample.get('officer_id', 'N/A')}")
                print(f"  - Type: {sample.get('deviation_type', 'N/A')}")
                print(f"  - Severity: {sample.get('severity', 'N/A')}")
                desc = sample.get('description', '')
                if desc:
                    print(f"  - Description: {desc[:60]}...")
                else:
                    print(f"  - Description: (empty)")
            except Exception as sample_error:
                print_warning(f"Could not display sample: {sample_error}")
                print(f"Sample data type: {type(deviations[0])}")
                print(f"Sample data: {str(deviations[0])[:200]}")

            return deviations

        else:
            print_error(f"Failed to fetch deviations: Status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return None

    except Exception as e:
        print_error(f"Error fetching deviations: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_pattern_analysis(deviations):
    """Test the full layered pattern analysis."""
    print_header("TESTING LAYERED PATTERN ANALYSIS")

    print(f"📤 Sending {len(deviations)} deviations to AI service...")
    print("This will test:")
    print("  Layer 1: Data Cleaning")
    print("  Layer 2: Statistical Analysis")
    print("  Layer 3: AI Pattern Analysis (if Claude API key configured)")

    try:
        # Call the pattern analysis endpoint
        response = requests.post(
            'http://localhost:8000/ai/deviation/analyze-patterns',
            json={'deviations': deviations},
            timeout=120  # 2 minutes timeout
        )

        if response.status_code == 200:
            result = response.json()

            print_success("Pattern analysis completed!")

            # Show data quality
            if 'data_quality' in result:
                quality = result['data_quality']
                print(f"\n🎯 Data Quality:")
                print(f"  - Score: {quality['score']}/100")
                print(f"  - Grade: {quality['grade']}")
                print(f"  - Assessment: {quality['assessment']}")

            # Show cleaning report
            if 'cleaning_report' in result:
                report = result['cleaning_report']
                print(f"\n🧹 Cleaning Report:")
                print(f"  - Original count: {report['original_count']}")
                print(f"  - Duplicates removed: {report['duplicates_removed']}")
                print(f"  - Invalid types fixed: {report['invalid_types_fixed']}")
                print(f"  - Missing values handled: {report['missing_values_handled']}")
                print(f"  - Final count: {report['final_count']}")

            # Show statistical summary
            if 'statistical_summary' in result:
                stats = result['statistical_summary']
                print(f"\n📊 Statistical Summary:")
                print(f"  - Total analyzed: {stats['total_analyzed']}")
                print(f"  - Severity score: {stats['severity_score']}/100")
                print(f"  - Assessment: {stats['severity_assessment']}")
                print(f"  - Critical mass score: {stats['critical_mass_score']}/100")
                print(f"  - Risk: {stats['risk_assessment']}")

                if 'top_deviation_types' in stats:
                    print(f"\n  📈 Top Deviation Types:")
                    for i, dtype in enumerate(stats['top_deviation_types'][:3], 1):
                        print(f"    {i}. {dtype['type']}: {dtype['count']} ({dtype['percentage']}%)")

            # Show AI analysis results
            print(f"\n🤖 AI Pattern Analysis:")
            print(f"  - Behavioral patterns found: {len(result.get('behavioral_patterns', []))}")
            print(f"  - Hidden rules found: {len(result.get('hidden_rules', []))}")
            print(f"  - Systemic issues found: {len(result.get('systemic_issues', []))}")
            print(f"  - Recommendations: {len(result.get('recommendations', []))}")
            print(f"  - API calls made: {result.get('api_calls_made', 0)}")

            # Show first recommendation
            if result.get('recommendations'):
                print(f"\n💡 First Recommendation:")
                print(f"  {result['recommendations'][0]}")

            return result

        else:
            print_error(f"Pattern analysis failed: Status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return None

    except requests.exceptions.Timeout:
        print_error("Request timed out (took more than 2 minutes)")
        print("This might happen if you have many deviations or Claude API is slow")
        return None
    except Exception as e:
        print_error(f"Error during pattern analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Run the full test suite with real data."""
    print_header("PHASE 1 TEST WITH REAL DATABASE DATA")

    # Step 1: Check services
    if not check_services():
        print_error("\n❌ Services are not running. Please start them first.")
        return 1

    # Step 2: Fetch deviations
    deviations = get_deviations()
    if not deviations:
        print_error("\n❌ No deviations available for testing")
        return 1

    # Step 3: Test pattern analysis
    result = test_pattern_analysis(deviations)
    if not result:
        print_error("\n❌ Pattern analysis failed")
        return 1

    # Success!
    print_header("✅ ALL TESTS PASSED WITH REAL DATA!")

    print("\n📋 Summary:")
    print(f"  - Deviations tested: {len(deviations)}")
    if 'data_quality' in result:
        print(f"  - Data quality: {result['data_quality']['grade']}")
    if 'statistical_summary' in result:
        print(f"  - Severity score: {result['statistical_summary']['severity_score']}/100")
    print(f"  - Patterns found: {len(result.get('behavioral_patterns', []))}")
    print(f"  - Recommendations: {len(result.get('recommendations', []))}")

    print("\n🎉 Phase 1 is working correctly with your real data!")

    # Save results to file
    output_file = 'test_results.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\n💾 Full results saved to: {output_file}")

    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
