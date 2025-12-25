"""
Complete Pipeline Test Script

Tests the entire 5-layer pipeline:
1. Upload SOP document
2. Upload workflow logs with column mapping
3. Run comprehensive analysis
4. Verify results

Usage:
    python test_complete_pipeline.py
"""

import requests
import json
import time
import os
from pathlib import Path

# Configuration
BACKEND_URL = "http://localhost:5000"
AI_SERVICE_URL = "http://localhost:8000"

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print colored header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def check_services():
    """Check if backend and AI service are running"""
    print_header("STEP 0: Checking Services")

    try:
        # Check backend
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success(f"Backend is running at {BACKEND_URL}")
        else:
            print_error(f"Backend returned status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Backend is not running at {BACKEND_URL}")
        print_error(f"Error: {str(e)}")
        print_info("Start backend: cd backend && npm start")
        return False

    try:
        # Check AI service
        response = requests.get(f"{AI_SERVICE_URL}/ai/health", timeout=5)
        if response.status_code == 200:
            print_success(f"AI Service is running at {AI_SERVICE_URL}")
        else:
            print_error(f"AI Service returned status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"AI Service is not running at {AI_SERVICE_URL}")
        print_error(f"Error: {str(e)}")
        print_info("Start AI service: cd ai-service && python main.py")
        return False

    # Check ML dependencies
    try:
        response = requests.get(f"{AI_SERVICE_URL}/ml/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'healthy':
                print_success("ML dependencies are installed")
                print_info(f"  - numpy: {data['libraries']['numpy']}")
                print_info(f"  - pandas: {data['libraries']['pandas']}")
                print_info(f"  - scikit-learn: {data['libraries']['scikit-learn']}")
            else:
                print_warning(f"ML service is degraded: {data.get('error')}")
                print_info("Install dependencies: cd ai-service && pip install -r requirements.txt")
                return False
        else:
            print_warning("ML health check failed")
            return False
    except Exception as e:
        print_error(f"ML health check failed: {str(e)}")
        return False

    return True

def create_sample_sop():
    """Create a sample SOP file for testing"""
    sop_content = """
LOAN PROCESSING STANDARD OPERATING PROCEDURE

1. KYC VERIFICATION
   Rule: KYC must be completed before loan approval
   Severity: Critical
   Type: kyc_cdd

2. APPROVAL AUTHORITY
   Rule: Loans above $50,000 require manager approval
   Severity: Critical
   Type: approval_authority

3. CREDIT CHECK
   Rule: Credit score must be checked before approval
   Severity: High
   Type: credit_check

4. DOCUMENTATION
   Rule: All required documents must be uploaded before disbursement
   Severity: High
   Type: documentation

5. TIMING
   Rule: Loan processing should not exceed 48 hours
   Severity: Medium
   Type: timing
"""

    sop_path = Path("test_sop.txt")
    with open(sop_path, 'w') as f:
        f.write(sop_content)

    return sop_path

def create_sample_worklog_csv():
    """Create a sample workflow log CSV with deviations"""
    import csv

    csv_path = Path("test_worklog.csv")

    # Create CSV with intentional deviations
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'case_id', 'officer_id', 'step_name', 'action', 'timestamp',
            'duration_seconds', 'status', 'notes'
        ])

        # Generate 100 cases with some deviations
        import datetime
        base_date = datetime.datetime(2025, 1, 1, 9, 0, 0)

        for case_num in range(1, 101):
            case_id = f"CASE-{case_num:03d}"
            officer_id = f"OFF{(case_num % 10) + 1:02d}"

            # Normal workflow
            steps = [
                ('Application Received', 'received', 300, 'completed', ''),
                ('KYC Verification', 'verified', 1800, 'completed', ''),
                ('Credit Check', 'checked', 900, 'completed', ''),
                ('Manager Approval', 'approved', 600, 'completed', ''),
                ('Documentation', 'uploaded', 1200, 'completed', ''),
                ('Loan Disbursement', 'disbursed', 300, 'completed', '')
            ]

            # Add some deviations
            if case_num % 5 == 0:  # Skip KYC for some cases
                steps = [s for s in steps if s[0] != 'KYC Verification']

            if case_num % 7 == 0:  # Skip Manager Approval for some
                steps = [s for s in steps if s[0] != 'Manager Approval']

            if case_num % 3 == 0:  # Add timing issue
                steps[2] = ('Credit Check', 'checked', 7200, 'completed', 'Took too long')

            # Write rows
            current_time = base_date + datetime.timedelta(days=case_num // 10, hours=case_num % 10)
            for step_name, action, duration, status, notes in steps:
                writer.writerow([
                    case_id, officer_id, step_name, action,
                    current_time.strftime('%Y-%m-%d %H:%M:%S'),
                    duration, status, notes
                ])
                current_time += datetime.timedelta(seconds=duration)

    return csv_path

def test_sop_upload(sop_path):
    """Test SOP upload and rule extraction"""
    print_header("STEP 1: Upload SOP Document")

    try:
        with open(sop_path, 'rb') as f:
            files = {'sop': (sop_path.name, f, 'text/plain')}
            data = {'use_llm': 'true'}

            response = requests.post(
                f"{BACKEND_URL}/sop/upload",
                files=files,
                data=data,
                timeout=60
            )

        if response.status_code in [200, 201]:
            result = response.json()
            print_success(f"SOP uploaded successfully")
            print_info(f"  - SOP ID: {result['data']['sop']['id']}")
            print_info(f"  - Rules extracted: {result['data']['rules_extracted']}")
            print_info(f"  - Extraction method: {result['data']['extraction_metadata']['extraction_method']}")
            return result['data']['sop']['id']
        else:
            print_error(f"Failed to upload SOP: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error uploading SOP: {str(e)}")
        return None

def test_worklog_upload(csv_path, sop_id):
    """Test workflow log upload with column mapping"""
    print_header("STEP 2: Analyze CSV Headers")

    try:
        with open(csv_path, 'rb') as f:
            files = {'logs': (csv_path.name, f, 'text/csv')}

            response = requests.post(
                f"{BACKEND_URL}/workflow/analyze-headers",
                files=files,
                timeout=30
            )

        if response.status_code == 200:
            result = response.json()
            print_success("Headers analyzed successfully")

            suggested_mapping = result['data']['suggested_mapping']
            print_info(f"  - Detected {len(suggested_mapping['mappings'])} column mappings")

            # Show a few mappings
            for mapping in suggested_mapping['mappings'][:3]:
                print_info(f"    {mapping['source_field']} → {mapping['target_field']}")
        else:
            print_error(f"Failed to analyze headers: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error analyzing headers: {str(e)}")
        return False

    print_header("STEP 3: Upload Workflow Logs with Mapping")

    try:
        with open(csv_path, 'rb') as f:
            files = {'logs': (csv_path.name, f, 'text/csv')}
            data = {
                'sop_id': str(sop_id),
                'column_mapping': json.dumps(suggested_mapping)
            }

            response = requests.post(
                f"{BACKEND_URL}/workflow/upload-with-mapping",
                files=files,
                data=data,
                timeout=60
            )

        if response.status_code == 201:
            result = response.json()
            print_success("Workflow logs uploaded successfully")
            print_info(f"  - Total rows processed: {result['data']['total_rows_processed']}")
            print_info(f"  - Logs saved: {result['data']['total_logs']}")
            print_info(f"  - Unique cases: {result['data']['unique_cases']}")
            print_info(f"  - Unique officers: {result['data']['unique_officers']}")

            # Show cleaning report
            if 'cleaning_report' in result['data']:
                cleaning = result['data']['cleaning_report']
                print_info(f"  - Data Cleaning:")
                print_info(f"    • Clean rows: {cleaning['clean_output']} ({cleaning['success_rate']})")
                print_info(f"    • Duplicates removed: {cleaning['duplicates_removed']}")
                print_info(f"    • Garbage removed: {cleaning['garbage_removed']}")

            return True
        else:
            print_error(f"Failed to upload workflow logs: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error uploading workflow logs: {str(e)}")
        return False

def test_comprehensive_analysis():
    """Test the comprehensive 5-layer pipeline"""
    print_header("STEP 4: Run Comprehensive Analysis (5-Layer Pipeline)")

    print_info("This will take 2-4 minutes depending on data size...")
    print_info("Pipeline layers:")
    print_info("  1. Data Cleaning (already done during upload)")
    print_info("  2. Batched Deviation Detection")
    print_info("  3. Statistical Analysis (ALL deviations)")
    print_info("  4. ML Intelligent Sampling")
    print_info("  5. AI Pattern Analysis (with cluster context)")

    start_time = time.time()

    try:
        response = requests.post(
            f"{BACKEND_URL}/workflow/analyze-comprehensive",
            json={},
            timeout=600  # 10 minutes max
        )

        elapsed = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            data = result['data']

            print_success(f"Comprehensive analysis completed in {elapsed:.1f}s")
            print("")

            # Summary
            summary = data['summary']
            print_info(f"📊 SUMMARY:")
            print_info(f"  - Total deviations found: {summary['total_deviations']}")
            print_info(f"  - Representatives analyzed by LLM: {summary['representatives_analyzed']}")
            print_info(f"  - Total processing time: {summary['total_time_seconds']:.1f}s")
            print_info(f"  - Pipeline layers completed: {summary['pipeline_layers_completed']}/5")
            print("")

            # Statistical Insights
            if 'statistical_insights' in data:
                stats = data['statistical_insights']
                print_info(f"📈 STATISTICAL INSIGHTS (ALL {summary['total_deviations']} deviations):")

                # Distribution by severity
                if 'distributions' in stats:
                    dist = stats['distributions']
                    if 'by_severity' in dist:
                        print_info("  Severity Distribution:")
                        for item in dist['by_severity'][:4]:
                            severity = item.get('severity', 'unknown')
                            count = item.get('count', 0)
                            pct = (count / summary['total_deviations']) * 100
                            print_info(f"    • {severity}: {count} ({pct:.1f}%)")

                # Top deviation types
                if 'distributions' in stats and 'by_type' in stats['distributions']:
                    print_info("  Top Deviation Types:")
                    for item in stats['distributions']['by_type'][:5]:
                        dev_type = item.get('deviation_type', 'unknown')
                        count = item.get('count', 0)
                        print_info(f"    • {dev_type}: {count}")

                print("")

            # ML Analysis
            if 'ml_analysis' in data:
                ml = data['ml_analysis']
                metadata = ml.get('sampling_metadata', {})

                print_info(f"🤖 ML ANALYSIS:")
                print_info(f"  - Compression ratio: {metadata.get('compression_ratio', 'N/A')}")
                print_info(f"  - Clusters found: {metadata.get('num_clusters', 0)}")
                print_info(f"  - Anomalies detected: {metadata.get('num_anomalies', 0)}")
                print_info(f"  - Feature dimensions: {metadata.get('feature_dimensions', 0)}")

                # Show cluster breakdown
                if 'cluster_statistics' in ml:
                    print_info("  Cluster Breakdown:")
                    for cluster_id, stats in list(ml['cluster_statistics'].items())[:5]:
                        size = stats.get('size', 0)
                        is_noise = stats.get('is_noise', False)
                        if is_noise:
                            print_info(f"    • Cluster {cluster_id} (NOISE): {size} outliers")
                        else:
                            print_info(f"    • Cluster {cluster_id}: {size} deviations")

                print("")

            # Pattern Analysis
            if 'pattern_analysis' in data:
                patterns = data['pattern_analysis']

                print_info(f"🔍 AI PATTERN ANALYSIS:")
                print_info(f"  Summary: {patterns.get('overall_summary', 'N/A')}")

                # Behavioral patterns
                if patterns.get('behavioral_patterns'):
                    print_info(f"  Behavioral Patterns Found: {len(patterns['behavioral_patterns'])}")
                    for i, pattern in enumerate(patterns['behavioral_patterns'][:3], 1):
                        print_info(f"    {i}. {pattern}")

                # Hidden rules
                if patterns.get('hidden_rules'):
                    print_info(f"  Hidden Rules Discovered: {len(patterns['hidden_rules'])}")
                    for i, rule in enumerate(patterns['hidden_rules'][:3], 1):
                        print_info(f"    {i}. {rule}")

                # Recommendations
                if patterns.get('recommendations'):
                    print_info(f"  Recommendations: {len(patterns['recommendations'])}")
                    for i, rec in enumerate(patterns['recommendations'][:3], 1):
                        print_info(f"    {i}. {rec}")

                print("")

            # Cost Savings
            if 'cost_savings' in data:
                cost = data['cost_savings']
                print_info(f"💰 COST SAVINGS:")
                print_info(f"  - Full analysis cost: {cost.get('full_analysis_cost', 'N/A')}")
                print_info(f"  - Actual cost (ML sampling): {cost.get('actual_cost', 'N/A')}")
                print_info(f"  - Savings: {cost.get('savings', 'N/A')}")
                print_info(f"  - Compression: {cost.get('compression_ratio', 'N/A')}")

            return True
        else:
            print_error(f"Failed to run comprehensive analysis: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except requests.Timeout:
        print_error("Request timed out (>10 minutes)")
        print_warning("This might indicate a problem with the AI service or dataset is too large")
        return False
    except Exception as e:
        print_error(f"Error running comprehensive analysis: {str(e)}")
        return False

def cleanup(sop_path, csv_path):
    """Clean up test files"""
    try:
        if sop_path.exists():
            os.remove(sop_path)
        if csv_path.exists():
            os.remove(csv_path)
        print_info("Test files cleaned up")
    except Exception as e:
        print_warning(f"Could not clean up test files: {str(e)}")

def main():
    """Main test function"""
    print_header("5-LAYER PIPELINE COMPREHENSIVE TEST")

    # Check services
    if not check_services():
        print_error("Services are not ready. Please start them and try again.")
        return

    # Create test files
    print_info("Creating sample test files...")
    sop_path = create_sample_sop()
    csv_path = create_sample_worklog_csv()
    print_success(f"Created: {sop_path}")
    print_success(f"Created: {csv_path} (100 cases with intentional deviations)")

    try:
        # Test SOP upload
        sop_id = test_sop_upload(sop_path)
        if not sop_id:
            print_error("SOP upload failed. Stopping test.")
            return

        # Test worklog upload
        if not test_worklog_upload(csv_path, sop_id):
            print_error("Workflow log upload failed. Stopping test.")
            return

        # Test comprehensive analysis
        if not test_comprehensive_analysis():
            print_error("Comprehensive analysis failed.")
            return

        print_header("✅ ALL TESTS PASSED!")
        print_success("The 5-layer pipeline is working correctly!")

    finally:
        # Cleanup
        cleanup(sop_path, csv_path)

if __name__ == "__main__":
    main()
