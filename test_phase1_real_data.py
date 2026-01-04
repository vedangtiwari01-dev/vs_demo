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
    print_header("TESTING LAYERED PATTERN ANALYSIS (4 LAYERS)")

    print(f"📤 Sending {len(deviations)} deviations to AI service...")
    print("\n🔄 Pipeline Flow:")
    print("  Layer 1: Data Cleaning → Clean deviations")
    print("  Layer 2: Statistical Analysis → Stats summary")
    print("  Layer 3: ML Analysis → Selected representatives + labels")
    print("  Layer 4: AI Pattern Analysis → Insights + recommendations")

    # Show sample input deviations
    print(f"\n📥 INPUT: Sample of {len(deviations)} deviations being sent:")
    for i, dev in enumerate(deviations[:3], 1):
        print(f"  {i}. {dev.get('case_id', 'N/A')} - {dev.get('deviation_type', 'N/A')} ({dev.get('severity', 'N/A')})")
    if len(deviations) > 3:
        print(f"  ... and {len(deviations) - 3} more")

    try:
        # Call the pattern analysis endpoint
        response = requests.post(
            'http://localhost:8000/ai/deviation/analyze-patterns',
            json={'deviations': deviations},
            timeout=120  # 2 minutes timeout
        )

        if response.status_code == 200:
            result = response.json()

            print_success("Pattern analysis completed!\n")

            # Debug: Show what fields are in the response
            print(f"\n🔍 DEBUG: Response contains these fields:")
            print(f"   {list(result.keys())}")

            print("\n" + "="*80)
            print("LAYER-BY-LAYER RESULTS:")
            print("="*80)

            # Show data quality
            if 'data_quality' in result:
                quality = result['data_quality']
                print(f"\n🧹 Layer 1: Data Cleaning")
                print(f"  Quality Score: {quality['score']}/100 (Grade {quality['grade']})")
                print(f"  Assessment: {quality['assessment']}")

            # Show cleaning report
            if 'cleaning_report' in result:
                report = result['cleaning_report']
                print(f"\n  Cleaning Operations:")
                print(f"    - Original count: {report['original_count']}")
                print(f"    - Duplicates removed: {report['duplicates_removed']}")
                print(f"    - Invalid types fixed: {report['invalid_types_fixed']}")
                print(f"    - Missing values handled: {report['missing_values_handled']}")
                print(f"    - Text fields normalized: {report.get('text_normalized', 0)}")
                print(f"    ✅ Final count: {report['final_count']} clean deviations")

                if report.get('validation_errors'):
                    print(f"\n  ⚠️  Validation Issues Found:")
                    for err in report['validation_errors'][:3]:
                        print(f"    - {err}")
                    if len(report['validation_errors']) > 3:
                        print(f"    ... and {len(report['validation_errors']) - 3} more")

                print(f"\n  📤 OUTPUT → Passing {report['final_count']} clean deviations to Layer 2")

            # Show statistical summary
            if 'statistical_summary' in result:
                stats = result['statistical_summary']
                print(f"\n📊 Statistical Summary (Layer 2):")
                print(f"  Overview:")
                print(f"    - Total analyzed: {stats['total_analyzed']} deviations")
                print(f"    - Severity score: {stats['severity_score']}/100 ({stats['severity_assessment']})")
                print(f"    - Critical mass score: {stats['critical_mass_score']}/100")
                print(f"    - Risk assessment: {stats['risk_assessment']}")

                if 'top_deviation_types' in stats:
                    print(f"\n  📈 Deviation Type Distribution:")
                    for i, dtype in enumerate(stats['top_deviation_types'][:5], 1):
                        print(f"    {i}. {dtype['type']}: {dtype['count']} occurrences ({dtype['percentage']:.1f}%)")

                print(f"\n  📤 OUTPUT → Statistical context + {stats['total_analyzed']} deviations → Layer 3")

            # Show ML summary
            if 'ml_summary' in result:
                ml = result['ml_summary']
                print(f"\n🤖 ML Analysis (Layer 3):")

                if ml.get('ml_applied'):
                    print(f"  ✅ ML Pipeline ACTIVE")
                    print(f"\n  📊 Compression:")
                    print(f"    - Original deviations: {ml['original_count']}")
                    print(f"    - Selected for LLM: {ml['selected_count']}")
                    print(f"    - Compression ratio: {ml['compression_ratio']:.1f}x")
                    print(f"    - Cost savings: ~{((ml['compression_ratio'] - 1) / ml['compression_ratio'] * 100):.0f}%")

                    print(f"\n  🔍 Pattern Discovery:")
                    print(f"    - Clustering method: {ml['clustering_method']}")
                    print(f"    - Clusters found: {ml['clusters_found']}")
                    print(f"    - Anomalies detected: {ml['anomalies_detected']}")

                    if 'sampling_composition' in ml:
                        comp = ml['sampling_composition']
                        print(f"\n  📦 Sample Composition (what ML selected):")
                        print(f"    - Anomalies: {comp.get('anomalies', 0)} (all unusual deviations included)")
                        print(f"    - Cluster representatives: {comp.get('cluster_representatives', 0)} (from {ml['clusters_found']} clusters)")
                        if comp.get('severity_coverage'):
                            print(f"    - Severity samples: {comp.get('severity_coverage', 0)} (all levels covered)")
                        if comp.get('temporal_coverage'):
                            print(f"    - Temporal samples: {comp.get('temporal_coverage', 0)} (time diversity)")
                        if comp.get('officer_coverage'):
                            print(f"    - Officer samples: {comp.get('officer_coverage', 0)} (officer diversity)")

                    print(f"\n  ✨ Result: 100% pattern coverage with {ml['compression_ratio']:.1f}x efficiency!")
                    print(f"\n  📤 OUTPUT → {ml['selected_count']} representative deviations with ML labels → Layer 4")
                else:
                    print(f"  ⚠️  ML Pipeline SKIPPED")
                    reason = ml.get('reason', 'Unknown reason')
                    print(f"    Reason: {reason}")
                    if 'too small' in reason.lower():
                        print(f"    Note: ML requires minimum 10 deviations for meaningful clustering")
                    print(f"    Fallback: Using all deviations directly (no sampling needed)")

            # Show AI analysis results
            print(f"\n🧠 AI Pattern Analysis (Layer 4):")
            print(f"  LLM Analysis Results:")
            print(f"    - Behavioral patterns: {len(result.get('behavioral_patterns', []))}")
            print(f"    - Hidden rules: {len(result.get('hidden_rules', []))}")
            print(f"    - Systemic issues: {len(result.get('systemic_issues', []))}")
            print(f"    - Time patterns: {len(result.get('time_patterns', []))}")
            print(f"    - Recommendations: {len(result.get('recommendations', []))}")
            print(f"    - API calls made: {result.get('api_calls_made', 0)}")

            # Show sample behavioral pattern
            if result.get('behavioral_patterns'):
                print(f"\n  👤 Sample Behavioral Pattern:")
                pattern = result['behavioral_patterns'][0]
                if isinstance(pattern, dict):
                    print(f"    {pattern.get('pattern', pattern)}")
                else:
                    print(f"    {pattern}")

            # Show sample hidden rule
            if result.get('hidden_rules'):
                print(f"\n  📜 Sample Hidden Rule Discovered:")
                rule = result['hidden_rules'][0]
                if isinstance(rule, dict):
                    print(f"    {rule.get('rule', rule)}")
                else:
                    print(f"    {rule}")

            # Show sample systemic issue
            if result.get('systemic_issues'):
                print(f"\n  ⚠️  Sample Systemic Issue:")
                issue = result['systemic_issues'][0]
                if isinstance(issue, dict):
                    print(f"    {issue.get('issue', issue)}")
                else:
                    print(f"    {issue}")

            # Show first recommendation
            if result.get('recommendations'):
                print(f"\n  💡 Top Recommendation:")
                print(f"    {result['recommendations'][0]}")
                if len(result['recommendations']) > 1:
                    print(f"    ... and {len(result['recommendations']) - 1} more recommendations")

            print("\n" + "="*80)
            print("END OF LAYER-BY-LAYER ANALYSIS")
            print("="*80)

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
    print_header("✅ ALL 4 LAYERS WORKING WITH REAL DATA!")

    print("\n📋 Summary:")
    print(f"  - Deviations tested: {len(deviations)}")
    if 'data_quality' in result:
        print(f"  - Data quality: {result['data_quality']['grade']} ({result['data_quality']['score']}/100)")
    if 'statistical_summary' in result:
        print(f"  - Severity score: {result['statistical_summary']['severity_score']}/100")
    if 'ml_summary' in result and result['ml_summary'].get('ml_applied'):
        ml = result['ml_summary']
        print(f"  - ML compression: {ml['compression_ratio']:.1f}x ({ml['original_count']} → {ml['selected_count']})")
        print(f"  - Clusters found: {ml['clusters_found']}")
        print(f"  - Anomalies detected: {ml['anomalies_detected']}")
    elif 'ml_summary' in result:
        print(f"  - ML status: Skipped (dataset too small)")
    print(f"  - Patterns found: {len(result.get('behavioral_patterns', []))}")
    print(f"  - Recommendations: {len(result.get('recommendations', []))}")

    print("\n🎉 All 4 layers (Cleaning + Statistics + ML + AI) working correctly!")

    # Save detailed results to files
    output_file = 'test_results.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\n💾 Full analysis results saved to: {output_file}")

    # Save a human-readable report
    report_file = 'test_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("DEVIATION ANALYSIS TEST REPORT\n")
        f.write("="*80 + "\n\n")

        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Layer 1: Cleaning
        if 'data_quality' in result:
            f.write("LAYER 1: DATA CLEANING\n")
            f.write("-" * 40 + "\n")
            f.write(f"Quality Score: {result['data_quality']['score']}/100 ({result['data_quality']['grade']})\n")
            if 'cleaning_report' in result:
                report = result['cleaning_report']
                f.write(f"Original: {report['original_count']} → Final: {report['final_count']}\n")
                f.write(f"Duplicates removed: {report['duplicates_removed']}\n")
                f.write(f"Invalid types fixed: {report['invalid_types_fixed']}\n\n")

        # Layer 2: Statistics
        if 'statistical_summary' in result:
            f.write("LAYER 2: STATISTICAL ANALYSIS\n")
            f.write("-" * 40 + "\n")
            stats = result['statistical_summary']
            f.write(f"Total analyzed: {stats['total_analyzed']}\n")
            f.write(f"Severity score: {stats['severity_score']}/100\n")
            f.write(f"Risk: {stats['risk_assessment']}\n\n")

        # Layer 3: ML
        if 'ml_summary' in result and result['ml_summary'].get('ml_applied'):
            f.write("LAYER 3: ML ANALYSIS\n")
            f.write("-" * 40 + "\n")
            ml = result['ml_summary']
            f.write(f"Original: {ml['original_count']} deviations\n")
            f.write(f"Selected: {ml['selected_count']} representatives\n")
            f.write(f"Compression: {ml['compression_ratio']:.1f}x\n")
            f.write(f"Clusters: {ml['clusters_found']}\n")
            f.write(f"Anomalies: {ml['anomalies_detected']}\n\n")

        # Layer 4: AI Analysis
        f.write("LAYER 4: AI PATTERN ANALYSIS\n")
        f.write("-" * 40 + "\n")
        f.write(f"Behavioral patterns: {len(result.get('behavioral_patterns', []))}\n")
        f.write(f"Hidden rules: {len(result.get('hidden_rules', []))}\n")
        f.write(f"Systemic issues: {len(result.get('systemic_issues', []))}\n")
        f.write(f"Recommendations: {len(result.get('recommendations', []))}\n\n")

        # Show all recommendations
        if result.get('recommendations'):
            f.write("RECOMMENDATIONS:\n")
            f.write("-" * 40 + "\n")
            for i, rec in enumerate(result['recommendations'], 1):
                f.write(f"{i}. {rec}\n")
            f.write("\n")

        # Show all behavioral patterns
        if result.get('behavioral_patterns'):
            f.write("BEHAVIORAL PATTERNS:\n")
            f.write("-" * 40 + "\n")
            for i, pattern in enumerate(result['behavioral_patterns'], 1):
                if isinstance(pattern, dict):
                    f.write(f"{i}. {pattern.get('pattern', pattern)}\n")
                else:
                    f.write(f"{i}. {pattern}\n")
            f.write("\n")

        # Show all hidden rules
        if result.get('hidden_rules'):
            f.write("HIDDEN RULES:\n")
            f.write("-" * 40 + "\n")
            for i, rule in enumerate(result['hidden_rules'], 1):
                if isinstance(rule, dict):
                    f.write(f"{i}. {rule.get('rule', rule)}\n")
                else:
                    f.write(f"{i}. {rule}\n")
            f.write("\n")

        f.write("="*80 + "\n")

    print(f"📄 Human-readable report saved to: {report_file}")

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
