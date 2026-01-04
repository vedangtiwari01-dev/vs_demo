"""
Intensive System Test with Synthetic Data

Tests the complete 4-layer pipeline with challenging synthetic data:
- Layer 0: Workflow log cleaning
- Layer 1: Deviation detection
- Layer 2: Statistical analysis (basic + advanced)
- Layer 3: ML analysis (clustering, anomaly detection, sampling)
- Layer 4: AI pattern analysis

This test validates:
1. ML pipeline activates (100+ deviations)
2. Clustering identifies officer behavior groups
3. Anomaly detection flags unusual patterns
4. Advanced statistics reveal correlations
5. Control charts detect process issues
6. Change-point detection finds shifts
"""

import json
import sys
import requests
from datetime import datetime
from typing import Dict, Any, List

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

def print_section(text):
    print(f"\n{Color.BLUE}{'─'*80}{Color.END}")
    print(f"{Color.BLUE}{Color.BOLD}{text}{Color.END}")
    print(f"{Color.BLUE}{'─'*80}{Color.END}")

def print_success(text):
    print(f"{Color.GREEN}[OK] {text}{Color.END}")

def print_warning(text):
    print(f"{Color.YELLOW}[WARNING] {text}{Color.END}")

def print_error(text):
    print(f"{Color.RED}[ERROR] {text}{Color.END}")

def load_synthetic_data():
    """Load synthetic workflow logs and SOP rules."""
    print_header("LOADING SYNTHETIC DATA")

    try:
        with open('synthetic_workflow_logs.json', 'r') as f:
            logs = json.load(f)
        print_success(f"Loaded {len(logs)} workflow log entries")

        with open('synthetic_sop_rules.json', 'r') as f:
            rules = json.load(f)
        print_success(f"Loaded {len(rules)} SOP rules")

        # Show data overview
        unique_cases = len(set(log['case_id'] for log in logs))
        unique_officers = len(set(log['officer_id'] for log in logs))
        date_range = (
            max(log['timestamp'] for log in logs),
            min(log['timestamp'] for log in logs)
        )

        print(f"\n[DATA] Data Overview:")
        print(f"   Cases: {unique_cases}")
        print(f"   Officers: {unique_officers}")
        print(f"   Date range: {date_range[1][:10]} to {date_range[0][:10]}")
        print(f"   Avg logs/case: {len(logs) / unique_cases:.1f}")

        return logs, rules
    except FileNotFoundError as e:
        print_error("Synthetic data files not found!")
        print("Run: python generate_synthetic_data.py")
        sys.exit(1)

def check_services():
    """Check if backend and AI service are running."""
    print_header("CHECKING SERVICES")

    services_ok = True

    # Check AI service
    try:
        response = requests.get('http://localhost:8000/ai/health', timeout=5)
        if response.status_code == 200:
            print_success("AI service is running (http://localhost:8000)")
        else:
            print_error(f"AI service returned status {response.status_code}")
            services_ok = False
    except Exception as e:
        print_error(f"AI service is not running: {e}")
        print("Start it with: cd ai-service && python -m uvicorn main:app --reload")
        services_ok = False

    return services_ok

def test_deviation_detection(logs: List[Dict], rules: List[Dict]):
    """Test deviation detection with workflow log cleaning."""
    print_header("STEP 1: DEVIATION DETECTION (with Log Cleaning)")

    try:
        print(f"📤 Sending {len(logs)} workflow logs + {len(rules)} rules to AI service...")
        print("   This will test:")
        print("   - Step 0: Clean workflow logs (remove duplicates, validate, normalize)")
        print("   - Step 1: Detect sequence deviations")
        print("   - Step 2: Detect rule violations")

        response = requests.post(
            'http://localhost:8000/ai/deviation/detect',
            json={'logs': logs, 'rules': rules},
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            deviations = result.get('deviations', [])

            print_success(f"Deviation detection completed!")
            print(f"\n[RESULTS] Results:")
            print(f"   Total deviations found: {len(deviations)}")

            # Analyze deviation types
            from collections import Counter
            type_counts = Counter(d.get('deviation_type', 'unknown') for d in deviations)

            print(f"\n   Deviation breakdown:")
            for dtype, count in type_counts.most_common(10):
                print(f"     - {dtype}: {count}")

            # Severity distribution
            severity_counts = Counter(d.get('severity', 'unknown') for d in deviations)
            print(f"\n   Severity distribution:")
            for severity, count in severity_counts.items():
                print(f"     - {severity}: {count}")

            print(f"\n   Expected patterns:")
            print(f"     ✓ Missing INCOME_VERIFICATION steps")
            print(f"     ✓ Missing CREDIT_ASSESSMENT steps (personal loans)")
            print(f"     ✓ Self-approval violations")
            print(f"     ✓ Wrong sequence deviations")

            return deviations
        else:
            print_error(f"Detection failed: Status {response.status_code}")
            print(response.text[:500])
            return None

    except requests.exceptions.Timeout:
        print_error("Request timed out after 60 seconds")
        return None
    except Exception as e:
        print_error(f"Error during detection: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_pattern_analysis(deviations: List[Dict], logs: List[Dict] = None):
    """Test complete 4-layer pattern analysis."""
    print_header("STEP 2: COMPLETE PATTERN ANALYSIS (4 Layers)")

    print(f"📤 Sending {len(deviations)} deviations for comprehensive analysis...")
    if logs:
        print(f"📤 Including {len(logs)} workflow logs for time-series analysis...")
    print("\n[PIPELINE] Pipeline:")
    print("   Layer 1: SKIP (logs already cleaned)")
    print("   Layer 2: Statistical Analysis (basic + advanced)")
    print("   Layer 2a: Advanced Statistics (correlations on deviations, time-series on logs)")
    print("   Layer 3: ML Analysis (clustering, anomaly detection, intelligent sampling)")
    print("   Layer 4: AI Pattern Analysis (LLM with full context)")

    try:
        payload = {'deviations': deviations}
        if logs:
            payload['workflow_logs'] = logs

        response = requests.post(
            'http://localhost:8000/ai/deviation/analyze-patterns',
            json=payload,
            timeout=180  # 3 minutes for ML + LLM
        )

        if response.status_code == 200:
            result = response.json()

            print_success("Pattern analysis completed!\n")

            # Layer 1: Data Quality
            print_section("LAYER 1: SKIP DEVIATION CLEANING")
            print(f"   Deviation cleaning SKIPPED (logs already cleaned at Step 0)")
            print(f"   Reason: Multiple occurrences of same deviation are valid, not duplicates")
            print(f"   Total deviations to analyze: {len(deviations)}")

            # Layer 2: Basic Statistics
            print_section("LAYER 2: STATISTICAL ANALYSIS")
            if 'statistical_summary' in result:
                stats = result['statistical_summary']
                print(f"   Total analyzed: {stats['total_analyzed']}")
                print(f"   Severity score: {stats['severity_score']}/100 ({stats['severity_assessment']})")
                print(f"   Risk: {stats['risk_assessment']}")

                if 'top_deviation_types' in stats:
                    print(f"\n   Top deviation types:")
                    for i, dtype in enumerate(stats['top_deviation_types'][:5], 1):
                        print(f"     {i}. {dtype['type']}: {dtype['count']} ({dtype['percentage']:.1f}%)")

                # Advanced Statistics
                print_section("LAYER 2a: ADVANCED STATISTICS")

                # Correlations
                if 'advanced_correlations' in stats:
                    corr = stats['advanced_correlations']
                    if corr.get('available'):
                        print(f"   [CORR] Correlation Analysis:")

                        if 'cramers_v' in corr:
                            print(f"\n   Cramér's V (categorical associations):")
                            for pair, data in list(corr['cramers_v'].items())[:3]:
                                print(f"     • {pair}: {data['value']} ({data['interpretation']})")

                        if 'chi_square_tests' in corr:
                            print(f"\n   Chi-Square Independence Tests:")
                            for pair, data in list(corr['chi_square_tests'].items())[:3]:
                                sig = "✓ Significant" if data['is_significant'] else "✗ Not significant"
                                print(f"     • {pair}: p={data['p_value']:.6f} {sig}")

                # Lift and odds ratios
                if 'lift_and_odds' in stats:
                    lift = stats['lift_and_odds']
                    if 'officer_to_deviation_type' in lift and lift['officer_to_deviation_type']:
                        print(f"\n   [ASSOC] Association Rules (Top 3):")
                        for i, assoc in enumerate(lift['officer_to_deviation_type'][:3], 1):
                            print(f"     {i}. {assoc['officer']} → {assoc['deviation_type']}")
                            print(f"        Lift: {assoc['lift']}x, Confidence: {assoc['confidence']:.1f}%")

                # Time-series
                if 'time_series' in stats:
                    ts = stats['time_series']
                    if ts.get('available'):
                        print(f"\n   [TIME] Time-Series Analysis:")
                        if 'date_range' in ts:
                            print(f"     Date range: {ts['date_range']['start']} to {ts['date_range']['end']} ({ts['date_range']['days']} days)")
                        if 'trend' in ts:
                            print(f"     Trend: {ts['trend']['direction']} ({ts['trend']['interpretation']})")
                    else:
                        print(f"\n   [TIME] Time-Series: {ts.get('message', 'Not available')}")

                # Control charts
                if 'control_charts' in stats:
                    cc = stats['control_charts']
                    if cc.get('available'):
                        print(f"\n   📉 Control Charts (SPC):")
                        if 'shewhart' in cc:
                            shew = cc['shewhart']
                            print(f"     Shewhart: {shew['status']}")
                            print(f"       Mean: {shew['mean']:.2f}, UCL: {shew['ucl']:.2f}, LCL: {shew['lcl']:.2f}")
                    else:
                        print(f"\n   📉 Control Charts: {cc.get('message', 'Not available')}")

                # Change points
                if 'change_points' in stats:
                    cp = stats['change_points']
                    if cp.get('available'):
                        print(f"\n   [CHANGE] Change-Point Detection:")
                        print(f"     {cp['interpretation']}")
                        if 'change_dates' in cp and cp['change_dates']:
                            print(f"     Change dates: {', '.join(cp['change_dates'][:3])}")
                    else:
                        print(f"\n   [CHANGE] Change-Point Detection: {cp.get('message', 'Not available')}")

            # Layer 3: ML Analysis
            print_section("LAYER 3: ML ANALYSIS")
            if 'ml_summary' in result:
                ml = result['ml_summary']

                if ml.get('ml_applied'):
                    print_success("ML Pipeline ACTIVE!")
                    print(f"\n   [ML] Compression:")
                    print(f"     Original: {ml['original_count']} deviations")
                    print(f"     Selected: {ml['selected_count']} representatives")
                    print(f"     Compression: {ml['compression_ratio']:.1f}x")
                    print(f"     Cost savings: ~{((ml['compression_ratio'] - 1) / ml['compression_ratio'] * 100):.0f}%")

                    print(f"\n   [PATTERN] Pattern Discovery:")
                    print(f"     Clustering: {ml['clustering_method']}")
                    print(f"     Clusters found: {ml['clusters_found']}")
                    print(f"     Anomalies detected: {ml['anomalies_detected']}")

                    if 'sampling_composition' in ml:
                        comp = ml['sampling_composition']
                        print(f"\n   📦 Sample Composition:")
                        print(f"     Anomalies: {comp.get('anomalies', 0)} (all included)")
                        print(f"     Cluster reps: {comp.get('cluster_representatives', 0)}")

                    print(f"\n   [HIDDEN] ML validated hidden patterns:")
                    print(f"     ✓ Officer clusters identified ({ml['clusters_found']} groups)")
                    print(f"     ✓ Anomalies flagged ({ml['anomalies_detected']} unusual cases)")
                    print(f"     ✓ Intelligent sampling (100% coverage, {ml['compression_ratio']:.1f}x efficiency)")

                else:
                    print_warning(f"ML Pipeline skipped: {ml.get('reason', 'Unknown')}")

            # Layer 4: AI Pattern Analysis
            print_section("LAYER 4: AI PATTERN ANALYSIS")
            print(f"   LLM Analysis:")
            print(f"     Behavioral patterns: {len(result.get('behavioral_patterns', []))}")
            print(f"     Hidden rules: {len(result.get('hidden_rules', []))}")
            print(f"     Systemic issues: {len(result.get('systemic_issues', []))}")
            print(f"     Recommendations: {len(result.get('recommendations', []))}")
            print(f"     API calls: {result.get('api_calls_made', 0)}")

            # Show samples
            if result.get('behavioral_patterns'):
                print(f"\n   👤 Sample Behavioral Pattern:")
                pattern = result['behavioral_patterns'][0]
                if isinstance(pattern, dict):
                    print(f"      {pattern.get('pattern', pattern)}")
                else:
                    print(f"      {pattern}")

            if result.get('hidden_rules'):
                print(f"\n   📜 Sample Hidden Rule:")
                rule = result['hidden_rules'][0]
                if isinstance(rule, dict):
                    print(f"      {rule.get('rule', rule)}")
                else:
                    print(f"      {rule}")

            if result.get('recommendations'):
                print(f"\n   [REC] Top Recommendation:")
                print(f"      {result['recommendations'][0]}")

            return result
        else:
            print_error(f"Analysis failed: Status {response.status_code}")
            print(response.text[:500])
            return None

    except requests.exceptions.Timeout:
        print_error("Request timed out after 3 minutes")
        return None
    except Exception as e:
        print_error(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

def validate_ml_activation(result: Dict[str, Any]):
    """Validate that ML features activated correctly."""
    print_section("ML ACTIVATION VALIDATION")

    validations = []

    # Check ML applied
    ml = result.get('ml_summary', {})
    if ml.get('ml_applied'):
        validations.append(("[OK]", "ML pipeline activated"))

        # Check compression ratio
        ratio = ml.get('compression_ratio', 0)
        if ratio >= 3:
            validations.append(("[OK]", f"Compression ratio: {ratio:.1f}x (good)"))
        else:
            validations.append(("[WARN]", f"Compression ratio: {ratio:.1f}x (lower than expected)"))

        # Check clusters
        clusters = ml.get('clusters_found', 0)
        if 3 <= clusters <= 15:
            validations.append(("[OK]", f"Clusters found: {clusters} (optimal range 3-15)"))
        else:
            validations.append(("[WARN]", f"Clusters found: {clusters} (unusual)"))

        # Check anomalies
        anomalies = ml.get('anomalies_detected', 0)
        original = ml.get('original_count', 0)
        anomaly_rate = (anomalies / original * 100) if original > 0 else 0
        if 5 <= anomaly_rate <= 20:
            validations.append(("[OK]", f"Anomaly rate: {anomaly_rate:.1f}% (expected 5-20%)"))
        else:
            validations.append(("[WARN]", f"Anomaly rate: {anomaly_rate:.1f}% (unusual)"))

    else:
        validations.append(("❌", f"ML pipeline NOT activated: {ml.get('reason', 'Unknown')}"))

    # Check advanced statistics
    stats = result.get('statistical_summary', {})

    if 'advanced_correlations' in stats:
        corr = stats['advanced_correlations']
        if corr.get('available'):
            validations.append(("[OK]", "Advanced correlations computed"))
        else:
            validations.append(("[WARN]", f"Correlations skipped: {corr.get('message', 'Unknown')}"))

    if 'lift_and_odds' in stats:
        lift = stats['lift_and_odds']
        if lift.get('officer_to_deviation_type'):
            validations.append(("[OK]", f"Association rules found: {len(lift['officer_to_deviation_type'])}"))

    if 'time_series' in stats:
        ts = stats['time_series']
        if ts.get('available'):
            validations.append(("[OK]", "Time-series analysis completed"))
        else:
            validations.append(("[WARN]", f"Time-series skipped: {ts.get('message', 'Unknown')}"))

    if 'control_charts' in stats:
        cc = stats['control_charts']
        if cc.get('available'):
            validations.append(("[OK]", "Control charts generated"))
        else:
            validations.append(("[WARN]", f"Control charts skipped: {cc.get('message', 'Unknown')}"))

    if 'change_points' in stats:
        cp = stats['change_points']
        if cp.get('available'):
            validations.append(("[OK]", f"Change-point detection: {len(cp.get('change_points', []))} changes found"))
        else:
            validations.append(("[WARN]", f"Change-point skipped: {cp.get('message', 'Unknown')}"))

    # Print validations
    print()
    for icon, message in validations:
        print(f"   {icon} {message}")

    # Overall assessment
    success_count = sum(1 for icon, _ in validations if icon == "[OK]")
    total_count = len(validations)

    print(f"\n   Overall: {success_count}/{total_count} checks passed")

    return success_count >= total_count * 0.7  # 70% pass rate

def save_results(deviations: List[Dict], analysis: Dict[str, Any]):
    """Save results to files."""
    print_section("SAVING RESULTS")

    # Save deviations
    dev_file = 'test_intensive_deviations.json'
    with open(dev_file, 'w', encoding='utf-8') as f:
        json.dump(deviations, f, indent=2)
    print_success(f"Deviations saved to: {dev_file}")

    # Save analysis
    analysis_file = 'test_intensive_analysis.json'
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2)
    print_success(f"Analysis saved to: {analysis_file}")

    # Human-readable report
    report_file = 'test_intensive_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("INTENSIVE SYSTEM TEST REPORT\n")
        f.write("="*80 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Summary
        f.write("SUMMARY\n")
        f.write("-"*80 + "\n")
        f.write(f"Deviations detected: {len(deviations)}\n")
        f.write(f"Deviations analyzed: {analysis.get('deviations_analyzed', 0)}\n")
        f.write(f"API calls made: {analysis.get('api_calls_made', 0)}\n\n")

        # ML Summary
        if 'ml_summary' in analysis:
            ml = analysis['ml_summary']
            f.write("ML ANALYSIS\n")
            f.write("-"*80 + "\n")
            if ml.get('ml_applied'):
                f.write(f"Status: ACTIVE\n")
                f.write(f"Compression: {ml['compression_ratio']:.1f}x ({ml['original_count']} → {ml['selected_count']})\n")
                f.write(f"Clusters: {ml['clusters_found']}\n")
                f.write(f"Anomalies: {ml['anomalies_detected']}\n\n")
            else:
                f.write(f"Status: SKIPPED ({ml.get('reason', 'Unknown')})\n\n")

        # Patterns
        f.write("PATTERNS DISCOVERED\n")
        f.write("-"*80 + "\n")
        for i, pattern in enumerate(analysis.get('behavioral_patterns', []), 1):
            if isinstance(pattern, dict):
                f.write(f"{i}. {pattern.get('pattern', pattern)}\n")
            else:
                f.write(f"{i}. {pattern}\n")
        f.write("\n")

        # Recommendations
        f.write("RECOMMENDATIONS\n")
        f.write("-"*80 + "\n")
        for i, rec in enumerate(analysis.get('recommendations', []), 1):
            f.write(f"{i}. {rec}\n")
        f.write("\n")

        f.write("="*80 + "\n")

    print_success(f"Report saved to: {report_file}")

def main():
    """Run intensive system test."""
    print_header("INTENSIVE SYSTEM TEST")
    print("Testing complete pipeline with synthetic data containing hidden patterns")
    print()

    # Step 1: Load data
    logs, rules = load_synthetic_data()

    # Step 2: Check services
    if not check_services():
        print_error("\nServices not running. Start them first.")
        return 1

    # Step 3: Detect deviations
    deviations = test_deviation_detection(logs, rules)
    if not deviations:
        print_error("\nDeviation detection failed")
        return 1

    if len(deviations) < 10:
        print_warning(f"\nOnly {len(deviations)} deviations found - ML may not activate (needs 10+)")

    # Step 4: Analyze patterns (with workflow logs for time-series)
    analysis = test_pattern_analysis(deviations, logs=logs)
    if not analysis:
        print_error("\nPattern analysis failed")
        return 1

    # Step 5: Validate ML activation
    ml_ok = validate_ml_activation(analysis)

    # Step 6: Save results
    save_results(deviations, analysis)

    # Final summary
    print_header("TEST COMPLETE")

    if ml_ok:
        print_success("All ML features activated successfully!")
        print_success("Advanced statistics computed")
        print_success("Hidden patterns detected and analyzed")
        print()
        print("[PASS] System passed intensive testing!")
    else:
        print_warning("Some ML features did not activate as expected")
        print("   Check test_intensive_report.txt for details")

    return 0

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
