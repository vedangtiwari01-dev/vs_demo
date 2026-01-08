"""
Integration Test Script for ZenWolf Backend + AI Services
Tests the complete flow: SOP upload -> Rule extraction -> Workflow upload -> Deviation detection -> Pattern analysis
"""

import requests
import json
import time
import os
from pathlib import Path
from typing import Dict, Any

# Configuration
BACKEND_URL = "http://localhost:3000/api"
AI_SERVICE_URL = "http://localhost:8000"

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(message: str):
    """Print a formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def print_info(message: str):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

def check_services() -> bool:
    """Check if backend and AI services are running"""
    print_header("STEP 0: Checking Services")

    try:
        # Check backend
        print_info("Checking backend service...")
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success(f"Backend service is running at {BACKEND_URL}")
        else:
            print_error(f"Backend returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Backend service is not reachable at {BACKEND_URL}")
        print_error(f"Error: {str(e)}")
        return False

    try:
        # Check AI service
        print_info("Checking AI service...")
        response = requests.get(f"{AI_SERVICE_URL}/ai/health", timeout=5)
        if response.status_code == 200:
            print_success(f"AI service is running at {AI_SERVICE_URL}")
        else:
            print_error(f"AI service returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"AI service is not reachable at {AI_SERVICE_URL}")
        print_error(f"Error: {str(e)}")
        return False

    return True

def upload_sop(file_path: str) -> Dict[str, Any]:
    """Upload SOP document"""
    print_header("STEP 1: Uploading SOP Document")

    if not os.path.exists(file_path):
        print_error(f"SOP file not found: {file_path}")
        return None

    print_info(f"Uploading SOP from: {file_path}")

    with open(file_path, 'rb') as f:
        files = {'sop': (os.path.basename(file_path), f, 'text/plain')}
        data = {
            'title': 'Test SOP - Loan Processing',
            'version': '1.0'
        }

        response = requests.post(
            f"{BACKEND_URL}/sops/upload",
            files=files,
            data=data,
            timeout=30
        )

    if response.status_code == 200 or response.status_code == 201:
        result = response.json()
        sop_id = result['data']['id']
        print_success(f"SOP uploaded successfully! ID: {sop_id}")
        print_info(f"Title: {result['data']['title']}")
        print_info(f"Status: {result['data']['status']}")
        return result['data']
    else:
        print_error(f"Failed to upload SOP. Status: {response.status_code}")
        print_error(f"Response: {response.text}")
        return None

def process_sop(sop_id: int) -> Dict[str, Any]:
    """Process SOP to extract rules"""
    print_header("STEP 2: Processing SOP (Extracting Rules)")

    print_info(f"Processing SOP ID: {sop_id}")
    print_info("This may take 30-60 seconds as Claude AI extracts rules...")

    response = requests.post(
        f"{BACKEND_URL}/sops/{sop_id}/process",
        timeout=120
    )

    if response.status_code == 200:
        result = response.json()
        rules = result['data']['rules']
        print_success(f"SOP processed successfully! Extracted {len(rules)} rules")

        print_info("\nExtracted Rules:")
        for i, rule in enumerate(rules, 1):
            print(f"  {i}. [{rule['rule_type']}] {rule['rule_description'][:80]}...")
            print(f"     Severity: {rule['severity']}")

        return result['data']
    else:
        print_error(f"Failed to process SOP. Status: {response.status_code}")
        print_error(f"Response: {response.text}")
        return None

def upload_workflow_logs(file_path: str) -> Dict[str, Any]:
    """Upload workflow logs CSV"""
    print_header("STEP 3: Uploading Workflow Logs")

    if not os.path.exists(file_path):
        print_error(f"Workflow logs file not found: {file_path}")
        return None

    print_info(f"Uploading workflow logs from: {file_path}")

    # First, analyze headers for column mapping
    print_info("Step 3a: Analyzing CSV headers...")
    with open(file_path, 'rb') as f:
        files = {'logs': (os.path.basename(file_path), f, 'text/csv')}
        response = requests.post(
            f"{BACKEND_URL}/workflows/analyze-headers",
            files=files,
            timeout=30
        )

    if response.status_code != 200:
        print_error(f"Failed to analyze headers. Status: {response.status_code}")
        return None

    mapping_result = response.json()
    print_success("Headers analyzed successfully!")
    print_info(f"Detected mappings: {len(mapping_result['data']['mapping_suggestions'])} fields")
    print_info(f"Notes column: {mapping_result['data'].get('notes_column', 'None')}")

    # Upload with mapping
    print_info("Step 3b: Uploading logs with mapping...")
    with open(file_path, 'rb') as f:
        files = {'logs': (os.path.basename(file_path), f, 'text/csv')}
        data = {
            'mapping': json.dumps(mapping_result['data']['mapping_suggestions'])
        }

        response = requests.post(
            f"{BACKEND_URL}/workflows/upload-with-mapping",
            files=files,
            data=data,
            timeout=60
        )

    if response.status_code == 200 or response.status_code == 201:
        result = response.json()
        print_success(f"Workflow logs uploaded successfully!")
        print_info(f"Total logs imported: {result['data']['total_logs']}")
        print_info(f"Unique cases: {result['data']['unique_cases']}")
        print_info(f"Unique officers: {result['data']['unique_officers']}")
        print_info(f"Notes imported: {result['data'].get('notes_imported', 0)}")
        return result['data']
    else:
        print_error(f"Failed to upload workflow logs. Status: {response.status_code}")
        print_error(f"Response: {response.text}")
        return None

def analyze_workflow() -> Dict[str, Any]:
    """Analyze workflow logs for deviations"""
    print_header("STEP 4: Analyzing Workflow (Detecting Deviations)")

    print_info("Running deviation detection...")
    print_info("This may take 10-20 seconds...")

    response = requests.post(
        f"{BACKEND_URL}/workflows/analyze",
        timeout=120
    )

    if response.status_code == 200:
        result = response.json()
        print_success(f"Workflow analysis complete!")
        print_info(f"Total deviations detected: {result['data']['total_deviations']}")
        print_info(f"Cases analyzed: {result['data']['summary']['total_cases']}")
        print_info(f"Logs processed: {result['data']['summary']['total_logs']}")

        # Breakdown by severity
        severity_dist = result['data']['summary'].get('severity_distribution', {})
        if severity_dist:
            print_info("\nDeviations by Severity:")
            for severity, count in severity_dist.items():
                print(f"  - {severity.capitalize()}: {count}")

        # Breakdown by type (top 5)
        type_dist = result['data']['summary'].get('deviation_type_distribution', {})
        if type_dist:
            print_info("\nTop 5 Deviation Types:")
            sorted_types = sorted(type_dist.items(), key=lambda x: x[1], reverse=True)[:5]
            for dev_type, count in sorted_types:
                print(f"  - {dev_type}: {count}")

        return result['data']
    else:
        print_error(f"Failed to analyze workflow. Status: {response.status_code}")
        print_error(f"Response: {response.text}")
        return None

def analyze_patterns() -> Dict[str, Any]:
    """Analyze patterns across all deviations using AI"""
    print_header("STEP 5: Analyzing Patterns (AI Pattern Discovery)")

    print_info("Running AI pattern analysis...")
    print_info("This may take 60-90 seconds as Claude AI analyzes patterns...")

    response = requests.post(
        f"{BACKEND_URL}/workflows/analyze-patterns",
        timeout=600  # 10 minutes timeout
    )

    if response.status_code == 200:
        result = response.json()
        print_success("Pattern analysis complete!")

        # Overall summary
        print_info("\n📊 Overall Summary:")
        print(f"  {result['data'].get('overall_summary', 'No summary available')}")

        # Behavioral patterns
        patterns = result['data'].get('behavioral_patterns', [])
        if patterns:
            print_info(f"\n🔍 Behavioral Patterns Found: {len(patterns)}")
            for i, pattern in enumerate(patterns[:3], 1):  # Show first 3
                print(f"  {i}. {pattern.get('pattern', 'N/A')}")
                print(f"     Frequency: {pattern.get('frequency', 'N/A')}")
                print(f"     Risk Level: {pattern.get('risk_level', 'N/A')}")
                officers = pattern.get('officers_involved', [])
                if officers:
                    print(f"     Officers: {', '.join(officers)}")

        # Hidden rules
        hidden_rules = result['data'].get('hidden_rules', [])
        if hidden_rules:
            print_info(f"\n📜 Hidden Rules Discovered: {len(hidden_rules)}")
            for i, rule in enumerate(hidden_rules[:3], 1):
                print(f"  {i}. {rule.get('rule', 'N/A')}")
                print(f"     Confidence: {rule.get('confidence', 'N/A')}")
                print(f"     Impact: {rule.get('compliance_impact', 'N/A')[:100]}...")

        # Systemic issues
        systemic = result['data'].get('systemic_issues', [])
        if systemic:
            print_info(f"\n⚠️  Systemic Issues: {len(systemic)}")
            for i, issue in enumerate(systemic[:3], 1):
                print(f"  {i}. {issue.get('issue', 'N/A')}")
                print(f"     Frequency: {issue.get('frequency', 'N/A')}")
                print(f"     Fix: {issue.get('recommended_fix', 'N/A')[:100]}...")

        # Recommendations
        recommendations = result['data'].get('recommendations', [])
        if recommendations:
            print_info(f"\n💡 Recommendations: {len(recommendations)}")
            for i, rec in enumerate(recommendations[:5], 1):
                # Remove leading comma and whitespace if present
                rec_clean = rec.lstrip(', ') if isinstance(rec, str) else str(rec)
                print(f"  {i}. {rec_clean}")

        # Statistical Summary
        stat_summary = result['data'].get('statistical_summary', {})
        if stat_summary:
            print_info(f"\n📊 Statistical Summary:")
            if 'severity_distribution' in stat_summary:
                print("  Severity Distribution:")
                for severity, count in stat_summary['severity_distribution'].items():
                    print(f"    - {severity.capitalize()}: {count}")
            if 'severity_score' in stat_summary:
                print(f"  Severity Score: {stat_summary.get('severity_score', 'N/A')}/100")
            if 'critical_mass_percentage' in stat_summary:
                print(f"  Critical Mass: {stat_summary.get('critical_mass_percentage', 'N/A')}%")

        # ML Summary
        ml_summary = result['data'].get('ml_summary', {})
        if ml_summary:
            print_info(f"\n🤖 ML Summary:")
            print(f"  Clustering method: {ml_summary.get('clustering_method', 'N/A')}")
            print(f"  Clusters detected: {ml_summary.get('clusters_found', 'N/A')}")
            print(f"  Anomalies flagged: {ml_summary.get('anomalies_detected', 'N/A')}")
            print(f"  Samples selected: {ml_summary.get('selected_count', 'N/A')} of {ml_summary.get('original_count', 'N/A')}")
            print(f"  Compression ratio: {ml_summary.get('compression_ratio', 'N/A')}x")

        # API Stats
        print_info(f"\n📈 API Stats:")
        print(f"  API calls made: {result['data'].get('api_calls_made', 'N/A')}")
        print(f"  Deviations analyzed: {result['data'].get('deviations_analyzed', 'N/A')}")

        return result['data']
    else:
        print_error(f"Failed to analyze patterns. Status: {response.status_code}")
        print_error(f"Response: {response.text}")
        return None

def main():
    """Main test execution"""
    print_header("ZenWolf Integration Test - Backend + AI Services")
    print_info("Testing complete flow: SOP upload → Rule extraction → Workflow upload → Deviation detection → Pattern analysis")

    # Paths to test data
    base_dir = Path(__file__).parent / "test_data"
    sop_file = base_dir / "test_sop_rules.txt"
    workflow_file = base_dir / "test_workflow_logs.csv"

    # Track results
    results = {}

    # Step 0: Check services
    if not check_services():
        print_error("\n❌ Services are not running. Please start backend and AI services first.")
        print_info("\nTo start services:")
        print_info("  1. Backend: cd backend && npm start")
        print_info("  2. AI Service: cd ai-service && python main.py")
        return

    # Step 1: Upload SOP
    sop_data = upload_sop(str(sop_file))
    if not sop_data:
        print_error("\n❌ Test failed at SOP upload")
        return
    results['sop_upload'] = sop_data
    time.sleep(1)

    # Step 2: Process SOP
    sop_processed = process_sop(sop_data['id'])
    if not sop_processed:
        print_error("\n❌ Test failed at SOP processing")
        return
    results['sop_processing'] = sop_processed
    time.sleep(1)

    # Step 3: Upload workflow logs
    workflow_data = upload_workflow_logs(str(workflow_file))
    if not workflow_data:
        print_error("\n❌ Test failed at workflow upload")
        return
    results['workflow_upload'] = workflow_data
    time.sleep(1)

    # Step 4: Analyze workflow
    analysis_data = analyze_workflow()
    if not analysis_data:
        print_error("\n❌ Test failed at workflow analysis")
        return
    results['workflow_analysis'] = analysis_data
    time.sleep(2)

    # Step 5: Analyze patterns
    pattern_data = analyze_patterns()
    if not pattern_data:
        print_error("\n❌ Test failed at pattern analysis")
        return
    results['pattern_analysis'] = pattern_data

    # Final summary
    print_header("TEST SUMMARY")
    print_success("✅ All tests passed successfully!")
    print_info(f"\n📊 Key Metrics:")
    print(f"  - SOP Rules Extracted: {len(sop_processed['rules'])}")
    print(f"  - Workflow Logs Imported: {workflow_data['total_logs']}")
    print(f"  - Unique Cases: {workflow_data['unique_cases']}")
    print(f"  - Deviations Detected: {analysis_data['total_deviations']}")
    print(f"  - Behavioral Patterns Found: {len(pattern_data.get('behavioral_patterns', []))}")
    print(f"  - Hidden Rules Discovered: {len(pattern_data.get('hidden_rules', []))}")
    print(f"  - Systemic Issues: {len(pattern_data.get('systemic_issues', []))}")

    print_info("\n💾 Saving results to test_results.json...")
    with open('test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print_success("Results saved!")

    print_info("\n🎉 Integration test completed successfully!")
    print_info("You can now review the results in the backend database or test_results.json")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_error("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print_error(f"\n\n❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
