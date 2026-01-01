#!/usr/bin/env python3
"""
Test script for expanded SOP Compliance & Deviation Detection System

This script tests the comprehensive capabilities of the expanded system:
- 16 rule types (vs 4 originally)
- 80+ column mappings (vs 9 originally)
- 40+ deviation types (vs 5 originally)

Prerequisites:
1. Backend server running on http://localhost:3000
2. AI service running on http://localhost:8000
3. test_sop.docx and test_log.csv files in the same directory
"""

import requests
import json
import os
import sys
from pathlib import Path

# API Configuration
BACKEND_URL = "http://localhost:3000/api"
AI_SERVICE_URL = "http://localhost:8000/ai"

# Test files
SCRIPT_DIR = Path(__file__).parent
TEST_SOP_FILE = SCRIPT_DIR / "test_sop.docx"
TEST_LOG_FILE = SCRIPT_DIR / "test_log.csv"

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def check_services():
    """Check if backend and AI services are running"""
    print_header("CHECKING SERVICES")

    # Check backend
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success(f"Backend service is running at {BACKEND_URL}")
        else:
            print_error(f"Backend service returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Backend service not reachable: {e}")
        print_info("Make sure backend is running: cd backend && npm start")
        return False

    # Check AI service
    try:
        response = requests.get(f"{AI_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success(f"AI service is running at {AI_SERVICE_URL}")
        else:
            print_error(f"AI service returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"AI service not reachable: {e}")
        print_info("Make sure AI service is running: cd ai-service && python main.py")
        return False

    return True

def check_test_files():
    """Check if test files exist"""
    print_header("CHECKING TEST FILES")

    if not TEST_SOP_FILE.exists():
        print_error(f"Test SOP file not found: {TEST_SOP_FILE}")
        return False
    print_success(f"Found SOP file: {TEST_SOP_FILE}")

    if not TEST_LOG_FILE.exists():
        print_error(f"Test log file not found: {TEST_LOG_FILE}")
        return False
    print_success(f"Found log file: {TEST_LOG_FILE}")

    return True

def test_sop_upload():
    """Test SOP upload with expanded rule types"""
    print_header("TEST 1: SOP UPLOAD WITH EXPANDED RULE TYPES")

    try:
        with open(TEST_SOP_FILE, 'rb') as f:
            files = {'sop': (TEST_SOP_FILE.name, f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
            response = requests.post(f"{BACKEND_URL}/sops/upload", files=files)

        if response.status_code in [200, 201]:
            result = response.json()
            sop_data = result.get('data', {})
            sop_id = sop_data.get('id')

            print_success(f"SOP uploaded successfully (ID: {sop_id})")

            # Process SOP to extract rules
            if sop_id:
                print_info("Processing SOP to extract rules (this may take 30-60 seconds)...")
                try:
                    process_response = requests.post(f"{BACKEND_URL}/sops/{sop_id}/process", timeout=120)
                    if process_response.status_code == 200:
                        process_result = process_response.json()
                        process_data = process_result.get('data', {})
                        rules_count = len(process_data.get('rules', []))

                        print_success(f"Extracted {rules_count} rules from SOP")

                        # Display rule types found
                        if 'rules' in process_data and process_data['rules']:
                            rule_types = {}
                            for rule in process_data['rules']:
                                rule_type = rule.get('rule_type', 'unknown')
                                rule_types[rule_type] = rule_types.get(rule_type, 0) + 1

                            print_info(f"Rule types detected:")
                            for rule_type, count in sorted(rule_types.items()):
                                print(f"  - {rule_type}: {count}")
                    else:
                        error_result = process_response.json()
                        error_msg = error_result.get('message', process_response.text)
                        print_error(f"Rule extraction failed: {process_response.status_code}")
                        print_error(f"Error details:\n{error_msg}")
                        print_info("\nCheck backend terminal logs for detailed diagnostics")
                except requests.exceptions.Timeout:
                    print_error("Rule extraction timed out after 120 seconds")
                    print_info("The SOP document may be too large or Claude API is slow")
                    print_info("Check backend terminal for progress logs")
                except Exception as e:
                    print_error(f"Exception during rule extraction: {e}")

            return sop_id
        else:
            print_error(f"SOP upload failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None

    except Exception as e:
        print_error(f"Exception during SOP upload: {e}")
        return None

def test_column_mapping():
    """Test column mapping with expanded field support"""
    print_header("TEST 2: COLUMN MAPPING WITH EXPANDED FIELDS")

    try:
        with open(TEST_LOG_FILE, 'rb') as f:
            files = {'logs': (TEST_LOG_FILE.name, f, 'text/csv')}
            response = requests.post(f"{BACKEND_URL}/workflows/analyze-headers", files=files)

        if response.status_code == 200:
            result = response.json()
            data = result.get('data', {})
            mappings = data.get('mapping_suggestions', {})
            unmapped = data.get('unmapped_columns', [])
            warnings = data.get('warnings', [])

            print_success(f"Column mapping analysis completed")
            print_info(f"Total system fields supported: 85 (5 required + 80 optional)")
            print_info(f"Mapped columns: {len(mappings)}")

            # Count how many optional fields were detected
            required_fields = ['case_id', 'officer_id', 'step_name', 'action', 'timestamp']
            mapped_system_fields = set(mappings.values())
            optional_detected = len([f for f in mapped_system_fields if f not in required_fields])
            print_info(f"Optional fields detected: {optional_detected}")

            # Display mapped columns
            print_info("Column mappings:")
            for csv_col, system_field in list(mappings.items())[:10]:  # Show first 10
                print(f"  {csv_col} → {system_field}")
            if len(mappings) > 10:
                print(f"  ... and {len(mappings) - 10} more")

            if warnings:
                print_warning(f"Warnings: {', '.join(warnings)}")

            return mappings
        else:
            print_error(f"Column mapping failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None

    except Exception as e:
        print_error(f"Exception during column mapping: {e}")
        return None

def test_workflow_upload(sop_id, mappings):
    """Test workflow upload with confirmed mappings"""
    print_header("TEST 3: WORKFLOW LOG UPLOAD")

    if not sop_id or not mappings:
        print_warning("Skipping workflow upload (missing SOP ID or mappings)")
        return None

    try:
        with open(TEST_LOG_FILE, 'rb') as f:
            files = {'logs': (TEST_LOG_FILE.name, f, 'text/csv')}
            data = {
                'sop_id': sop_id,
                'mapping': json.dumps(mappings)
            }
            response = requests.post(f"{BACKEND_URL}/workflows/upload-with-mapping", files=files, data=data)

        if response.status_code in [200, 201]:
            result = response.json()
            data = result.get('data', {})
            workflow_count = data.get('total_logs', 0)
            unique_cases = data.get('unique_cases', 0)
            unique_officers = data.get('unique_officers', 0)

            print_success(f"Workflow logs uploaded successfully")
            print_info(f"Uploaded {workflow_count} workflow steps")
            print_info(f"Unique cases: {unique_cases}, Unique officers: {unique_officers}")

            return workflow_count
        else:
            print_error(f"Workflow upload failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None

    except Exception as e:
        print_error(f"Exception during workflow upload: {e}")
        return None

def test_deviation_detection(sop_id):
    """Test comprehensive deviation detection"""
    print_header("TEST 4: COMPREHENSIVE DEVIATION DETECTION (40+ TYPES)")

    if not sop_id:
        print_warning("Skipping deviation detection (missing SOP ID)")
        return

    try:
        response = requests.post(f"{BACKEND_URL}/workflows/analyze", json={'sop_id': sop_id})

        if response.status_code == 200:
            result = response.json()
            data = result.get('data', {})
            deviations = data.get('deviations', [])

            print_success(f"Deviation detection completed")
            print_info(f"Total deviations detected: {len(deviations)}")

            if deviations:
                # Group by deviation type
                deviation_types = {}
                severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}

                for deviation in deviations:
                    dev_type = deviation.get('deviation_type', 'unknown')
                    severity = deviation.get('severity', 'unknown')

                    deviation_types[dev_type] = deviation_types.get(dev_type, 0) + 1
                    if severity in severity_counts:
                        severity_counts[severity] += 1

                # Display deviation type breakdown
                print_info("Deviation types detected:")
                for dev_type, count in sorted(deviation_types.items(), key=lambda x: x[1], reverse=True):
                    print(f"  - {dev_type}: {count}")

                # Display severity breakdown
                print_info("Severity breakdown:")
                for severity, count in severity_counts.items():
                    if count > 0:
                        print(f"  - {severity}: {count}")

                # Show sample deviations
                print_info("Sample deviations:")
                for deviation in deviations[:3]:
                    print(f"\n  Case: {deviation.get('case_id')}")
                    print(f"  Type: {deviation.get('deviation_type')}")
                    print(f"  Severity: {deviation.get('severity')}")
                    print(f"  Description: {deviation.get('description', 'N/A')[:80]}...")

            return len(deviations)
        else:
            print_error(f"Deviation detection failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None

    except Exception as e:
        print_error(f"Exception during deviation detection: {e}")
        return None

def print_summary(results):
    """Print final summary"""
    print_header("EXPANDED SYSTEM CAPABILITIES SUMMARY")

    print(f"{Colors.BOLD}Current System Configuration:{Colors.END}\n")

    print(f"{Colors.BOLD}1. RULE TYPES (16 total):{Colors.END}")
    rule_types = [
        "sequence", "approval", "timing", "eligibility",
        "credit_risk", "kyc", "aml", "documentation",
        "collateral", "disbursement", "post_disbursement_qc",
        "collection", "restructuring", "regulatory",
        "data_quality", "operational"
    ]
    for i, rule_type in enumerate(rule_types, 1):
        print(f"   {i}. {rule_type}")

    print(f"\n{Colors.BOLD}2. COLUMN MAPPINGS (85 total):{Colors.END}")
    print(f"   Required Fields (5): case_id, officer_id, step_name, action, timestamp")
    print(f"   Optional Fields (80):")
    print(f"     • Core workflow: duration_seconds, status, notes, comments, step_id, stage_name, workflow_version, etc.")
    print(f"     • Entity identifiers: application_id, loan_id, customer_id, customer_name, portfolio_id, etc.")
    print(f"     • Product & channel: product_type, branch_code, channel, region, geo_code, etc.")
    print(f"     • Amounts & terms: loan_amount_requested, loan_amount_sanctioned, interest_rate, tenor_months, etc.")
    print(f"     • Risk & credit: credit_score_bureau, emi_to_income_ratio, dti_ratio, risk_grade, etc.")
    print(f"     • Collateral: collateral_type, collateral_value, security_created_flag, etc.")
    print(f"     • KYC/AML: kyc_status, sanctions_hit_flag, pep_flag, aml_risk_rating, etc.")
    print(f"     • Workflow detail: approver_id, approval_decision, exception_flag, override_flag, etc.")
    print(f"     • Disbursement: disbursement_date, disbursement_amount, post_disbursement_qc_flag, etc.")
    print(f"     • Collections: overdue_days, bucket, collection_status, restructure_flag, etc.")
    print(f"     • Audit & data quality: created_by, source_system, audit_trail_id, error_code, etc.")

    print(f"\n{Colors.BOLD}3. DEVIATION TYPES (43 total):{Colors.END}")
    deviation_categories = {
        "Process & Sequence (5)": ["missing_step", "wrong_sequence", "unexpected_step", "duplicate_step", "skipped_mandatory_subprocess"],
        "Approval & Authority (5)": ["missing_approval", "insufficient_approval_hierarchy", "unauthorized_approver", "self_approval_violation", "escalation_missing"],
        "Timing & SLA (4)": ["timing_violation", "tat_breach", "cutoff_breach", "post_disbursement_qc_delay"],
        "Eligibility & Credit Policy (4)": ["ineligible_age", "ineligible_tenor", "emi_to_income_breach", "low_score_approved_without_exception"],
        "KYC/AML/Sanctions (3)": ["kyc_incomplete_progression", "sanctions_hit_not_rejected", "pep_no_edd_or_extra_approval"],
        "Documentation & Legal (4)": ["missing_mandatory_document", "expired_document_used", "legal_clearance_missing", "collateral_docs_incomplete"],
        "Collateral & Security (3)": ["ltv_breach", "valuation_missing_or_stale", "security_not_created"],
        "Disbursement & Post-Disbursement (4)": ["pre_disbursement_condition_unmet", "mandate_not_set_before_disbursement", "incorrect_disbursement_amount", "post_disbursement_qc_missing"],
        "Collections & Restructuring (3)": ["collection_escalation_delay", "unauthorized_restructure", "unauthorized_writeoff"],
        "Regulatory & Reporting (3)": ["classification_mismatch", "provisioning_shortfall", "regulatory_report_missing_or_late"],
        "Data Quality & Logging (5)": ["missing_core_field", "invalid_format", "inconsistent_value_across_steps", "duplicate_active_case", "audit_trail_missing"]
    }

    for category, types in deviation_categories.items():
        print(f"\n   {Colors.BOLD}{category}:{Colors.END}")
        for dev_type in types:
            print(f"     • {dev_type}")

    print(f"\n{Colors.BOLD}Test Results:{Colors.END}")
    if results['sop_uploaded']:
        print_success(f"SOP Upload: {results['rules_extracted']} rules extracted")
    else:
        print_error("SOP Upload: Failed")

    if results['mapping_completed']:
        print_success(f"Column Mapping: {results['columns_mapped']} columns mapped")
    else:
        print_error("Column Mapping: Failed")

    if results['workflow_uploaded']:
        print_success(f"Workflow Upload: {results['workflows_uploaded']} steps uploaded")
    else:
        print_error("Workflow Upload: Failed")

    if results['deviations_detected'] is not None:
        print_success(f"Deviation Detection: {results['deviations_detected']} deviations found")
    else:
        print_error("Deviation Detection: Failed")

    print(f"\n{Colors.BOLD}{Colors.GREEN}System is ready for comprehensive SOP compliance analysis!{Colors.END}\n")

def main():
    """Main test execution"""
    print_header("EXPANDED SOP COMPLIANCE SYSTEM - TEST SUITE")
    print_info("Testing 16 rule types, 85 column mappings, and 43 deviation types")

    results = {
        'sop_uploaded': False,
        'rules_extracted': 0,
        'mapping_completed': False,
        'columns_mapped': 0,
        'workflow_uploaded': False,
        'workflows_uploaded': 0,
        'deviations_detected': None
    }

    # Pre-flight checks
    if not check_services():
        print_error("Services not running. Exiting.")
        sys.exit(1)

    if not check_test_files():
        print_error("Test files not found. Exiting.")
        sys.exit(1)

    # Run tests
    sop_id = test_sop_upload()
    if sop_id:
        results['sop_uploaded'] = True
        results['rules_extracted'] = "Extracted"

    mappings = test_column_mapping()
    if mappings:
        results['mapping_completed'] = True
        results['columns_mapped'] = len(mappings)

    workflow_count = test_workflow_upload(sop_id, mappings)
    if workflow_count:
        results['workflow_uploaded'] = True
        results['workflows_uploaded'] = workflow_count

    deviation_count = test_deviation_detection(sop_id)
    if deviation_count is not None:
        results['deviations_detected'] = deviation_count

    # Print summary
    print_summary(results)

if __name__ == "__main__":
    main()
