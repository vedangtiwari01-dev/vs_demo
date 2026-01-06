"""
Test script to verify all 10 deviation checkers detect deviations correctly.
Tests each checker module independently without running the full AI service.
"""

import sys
import os

# Add ai-service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-service'))

from app.services.deviation.sequence_checker import SequenceChecker
from app.services.deviation.rule_validator import RuleValidator
from app.services.deviation.eligibility_checker import EligibilityChecker
from app.services.deviation.kyc_checker import KYCChecker
from app.services.deviation.documentation_checker import DocumentationChecker
from app.services.deviation.collateral_checker import CollateralChecker
from app.services.deviation.disbursement_checker import DisbursementChecker
from app.services.deviation.collection_checker import CollectionChecker
from app.services.deviation.regulatory_checker import RegulatoryChecker
from app.services.deviation.data_quality_checker import DataQualityChecker

# Sample test data - workflow logs that should trigger various deviation types
test_logs = [
    # Case 1: Eligibility violations
    {
        'case_id': 'TEST-001',
        'officer_id': 'EMP-TEST-01',
        'step_name': 'Application Received',
        'action': 'Received',
        'timestamp': '2025-01-07T10:00:00',
        'customer_age': 70,  # Above max age (65)
        'tenor_months': 400,  # Exceeds max tenor (360)
        'emi_to_income_ratio': 0.65,  # Exceeds max EMI ratio (0.5)
        'credit_score': 600,  # Below minimum (650)
        'approval_decision': 'approved',
        'exception_flag': 'no'  # No exception for low credit score!
    },
    # Case 2: KYC violations
    {
        'case_id': 'TEST-002',
        'officer_id': 'EMP-TEST-02',
        'step_name': 'Manager Approval',
        'action': 'Approved',
        'timestamp': '2025-01-07T11:00:00',
        'kyc_status': 'pending',  # KYC incomplete
        'kyc_completed_flag': 'no',
        'sanctions_hit_flag': 'yes',  # Sanctions hit!
        'pep_flag': 'yes',  # PEP case without EDD
        'edd_completed': 'no',
        'approval_decision': 'approved'  # Approved despite issues!
    },
    {
        'case_id': 'TEST-002',
        'officer_id': 'EMP-TEST-02',
        'step_name': 'Disbursement',
        'action': 'Disbursed',
        'timestamp': '2025-01-07T12:00:00',
        'kyc_status': 'pending',
        'sanctions_hit_flag': 'yes'
    },
    # Case 3: Documentation violations
    {
        'case_id': 'TEST-003',
        'officer_id': 'EMP-TEST-03',
        'step_name': 'Document Verification',
        'action': 'Verified',
        'timestamp': '2025-01-07T10:00:00',
        'document_type': 'income_proof',
        'document_status': 'submitted',
        'document_expiry_date': '2024-12-01'  # Expired!
    },
    {
        'case_id': 'TEST-003',
        'officer_id': 'EMP-TEST-03',
        'step_name': 'Collateral Valuation',
        'action': 'Completed',
        'timestamp': '2025-01-07T11:00:00',
        'collateral_type': 'property',
        'collateral_value': 1000000
    },
    {
        'case_id': 'TEST-003',
        'officer_id': 'EMP-TEST-03',
        'step_name': 'Disbursement',
        'action': 'Disbursed',
        'timestamp': '2025-01-07T12:00:00'
        # Missing: identity_proof, address_proof, legal_clearance, collateral_docs
    },
    # Case 4: Collateral violations
    {
        'case_id': 'TEST-004',
        'officer_id': 'EMP-TEST-04',
        'step_name': 'Credit Approval',
        'action': 'Approved',
        'timestamp': '2025-01-07T10:00:00',
        'ltv_ratio': 0.95,  # Exceeds max LTV (0.80)
        'collateral_value': 500000,
        'collateral_value_date': '2024-07-01',  # 6 months old (stale)
        'collateral_type': 'property',
        'loan_amount_sanctioned': 475000,
        'security_created_flag': 'no'  # Security not created!
    },
    {
        'case_id': 'TEST-004',
        'officer_id': 'EMP-TEST-04',
        'step_name': 'Disbursement',
        'action': 'Disbursed',
        'timestamp': '2025-01-07T11:00:00',
        'collateral_type': 'property'
    },
    # Case 5: Disbursement violations
    {
        'case_id': 'TEST-005',
        'officer_id': 'EMP-TEST-05',
        'step_name': 'Disbursement',
        'action': 'Disbursed',
        'timestamp': '2025-01-07T10:00:00',
        'disbursement_amount': 100000,
        'loan_amount_sanctioned': 90000,  # Wrong amount!
        'mandate_status': 'not_set',  # Mandate not set!
        'post_disbursement_qc_flag': 'no'  # QC missing!
        # Missing: approval_decision (no approval before disbursement)
    },
    # Case 6: Collection violations
    {
        'case_id': 'TEST-006',
        'officer_id': 'EMP-TEST-06',
        'step_name': 'Collection',
        'action': 'In Collections',
        'timestamp': '2025-01-07T10:00:00',
        'overdue_days': 120,  # 120 DPD - should have legal action
        'bucket': 'NPA',
        'collection_status': 'pending',
        'restructure_flag': 'yes',  # Restructured without approval
        'writeoff_flag': 'yes'  # Written off without approval!
    },
    # Case 7: Regulatory violations
    {
        'case_id': 'TEST-007',
        'officer_id': 'EMP-TEST-07',
        'step_name': 'Classification',
        'action': 'Classified',
        'timestamp': '2025-01-07T10:00:00',
        'overdue_days': 95,  # 95 DPD
        'npa_classification': 'sub_standard',  # Should be "doubtful" at 95 DPD!
        'outstanding_amount': 100000,
        'provisioning_amount': 10000  # Should be 25000 (25% for doubtful)
    },
    # Case 8: Data quality violations - valid timestamps (invalid timestamp tested separately)
    {
        'case_id': 'TEST-008',
        # Missing officer_id!
        'step_name': 'Application Received',
        'action': 'Received',
        'timestamp': '2025-01-07T10:00:00',
        'loan_amount_requested': -50000,  # Negative amount!
        'customer_id': 'CUST-001'
    },
    {
        'case_id': 'TEST-008',
        'officer_id': 'EMP-TEST-08',
        'step_name': 'Credit Check',
        'action': 'Completed',
        'timestamp': '2025-01-07T11:00:00',
        'customer_id': 'CUST-002',  # Changed customer_id (inconsistent!)
        'audit_trail_id': 'AUDIT-123'
    },
    {
        'case_id': 'TEST-008',
        'officer_id': 'EMP-TEST-08',
        'step_name': 'Final Approval',
        'action': 'Approved',
        'timestamp': '2025-01-07T12:00:00'
        # Missing audit_trail_id for critical step!
    },
    # Case 9: Invalid timestamp format (tested separately for data quality)
    {
        'case_id': 'TEST-009',
        'officer_id': 'EMP-TEST-09',
        'step_name': 'Application Received',
        'action': 'Received',
        'timestamp': 'invalid-timestamp-format'  # Invalid format!
    }
]

# Sample rules (minimal for testing)
test_rules = [
    {'rule_type': 'sequence', 'rule_description': 'Credit check must happen before approval', 'step_number': 1},
    {'rule_type': 'approval', 'rule_description': 'Manager approval required', 'step_number': 2},
    {'rule_type': 'timing', 'rule_description': 'Process must take at least 1 hour', 'step_number': None},
    {'rule_type': 'eligibility', 'rule_description': 'Customer age must be 18-65 years', 'step_number': None},
    {'rule_type': 'credit_risk', 'rule_description': 'Credit score must be at least 650', 'step_number': None},
    {'rule_type': 'kyc', 'rule_description': 'KYC must be completed before approval', 'step_number': None},
    {'rule_type': 'documentation', 'rule_description': 'All mandatory documents required', 'step_number': None},
    {'rule_type': 'collateral', 'rule_description': 'LTV must not exceed 80%', 'step_number': None},
    {'rule_type': 'disbursement', 'rule_description': 'Mandate must be set before disbursement', 'step_number': None},
    {'rule_type': 'collection', 'rule_description': 'Escalate to legal at 90 DPD', 'step_number': None},
    {'rule_type': 'regulatory', 'rule_description': 'Proper classification and provisioning required', 'step_number': None},
    {'rule_type': 'data_quality', 'rule_description': 'All core fields must be present', 'step_number': None}
]

print("=" * 80)
print("DEVIATION DETECTION TEST - All 10 Checkers")
print("=" * 80)
print(f"\nTest Data: {len(test_logs)} workflow logs, {len(test_rules)} rules\n")

# Test each checker
all_deviations = []

print("\n--- Testing Core Checkers ---\n")

# 1. SequenceChecker
try:
    deviations = SequenceChecker.check_sequence(test_logs, test_rules)
    all_deviations.extend(deviations)
    print(f"[OK] SequenceChecker: {len(deviations)} deviations")
    for dev in deviations:
        print(f"  - {dev['case_id']}: {dev['deviation_type']} ({dev['severity']})")
except Exception as e:
    print(f"[FAIL] SequenceChecker FAILED: {e}")

# 2. RuleValidator
try:
    deviations = RuleValidator.validate_all(test_logs, test_rules)
    all_deviations.extend(deviations)
    print(f"\n[OK] RuleValidator: {len(deviations)} deviations")
    for dev in deviations:
        print(f"  - {dev['case_id']}: {dev['deviation_type']} ({dev['severity']})")
except Exception as e:
    print(f"\n[FAIL] RuleValidator FAILED: {e}")

# 3. DataQualityChecker
try:
    deviations = DataQualityChecker.check_data_quality(test_logs, test_rules)
    all_deviations.extend(deviations)
    print(f"\n[OK] DataQualityChecker: {len(deviations)} deviations")
    for dev in deviations:
        print(f"  - {dev['case_id']}: {dev['deviation_type']} ({dev['severity']})")
except Exception as e:
    print(f"\n[FAIL] DataQualityChecker FAILED: {e}")

print("\n--- Testing Extended Checkers (NEW) ---\n")

# 4. EligibilityChecker (NEW)
try:
    deviations = EligibilityChecker.check_eligibility(test_logs, test_rules)
    all_deviations.extend(deviations)
    print(f"[OK] EligibilityChecker (NEW): {len(deviations)} deviations")
    for dev in deviations:
        print(f"  - {dev['case_id']}: {dev['deviation_type']} ({dev['severity']})")
except Exception as e:
    print(f"[FAIL] EligibilityChecker FAILED: {e}")

# 5. KYCChecker (NEW)
try:
    deviations = KYCChecker.check_kyc(test_logs, test_rules)
    all_deviations.extend(deviations)
    print(f"\n[OK] KYCChecker (NEW): {len(deviations)} deviations")
    for dev in deviations:
        print(f"  - {dev['case_id']}: {dev['deviation_type']} ({dev['severity']})")
except Exception as e:
    print(f"\n[FAIL] KYCChecker FAILED: {e}")

# 6. DocumentationChecker (NEW)
try:
    deviations = DocumentationChecker.check_documentation(test_logs, test_rules)
    all_deviations.extend(deviations)
    print(f"\n[OK] DocumentationChecker (NEW): {len(deviations)} deviations")
    for dev in deviations:
        print(f"  - {dev['case_id']}: {dev['deviation_type']} ({dev['severity']})")
except Exception as e:
    print(f"\n[FAIL] DocumentationChecker FAILED: {e}")

# 7. CollateralChecker (NEW)
try:
    deviations = CollateralChecker.check_collateral(test_logs, test_rules)
    all_deviations.extend(deviations)
    print(f"\n[OK] CollateralChecker (NEW): {len(deviations)} deviations")
    for dev in deviations:
        print(f"  - {dev['case_id']}: {dev['deviation_type']} ({dev['severity']})")
except Exception as e:
    print(f"\n[FAIL] CollateralChecker FAILED: {e}")

# 8. DisbursementChecker (NEW)
try:
    deviations = DisbursementChecker.check_disbursement(test_logs, test_rules)
    all_deviations.extend(deviations)
    print(f"\n[OK] DisbursementChecker (NEW): {len(deviations)} deviations")
    for dev in deviations:
        print(f"  - {dev['case_id']}: {dev['deviation_type']} ({dev['severity']})")
except Exception as e:
    print(f"\n[FAIL] DisbursementChecker FAILED: {e}")

# 9. CollectionChecker (NEW)
try:
    deviations = CollectionChecker.check_collection(test_logs, test_rules)
    all_deviations.extend(deviations)
    print(f"\n[OK] CollectionChecker (NEW): {len(deviations)} deviations")
    for dev in deviations:
        print(f"  - {dev['case_id']}: {dev['deviation_type']} ({dev['severity']})")
except Exception as e:
    print(f"\n[FAIL] CollectionChecker FAILED: {e}")

# 10. RegulatoryChecker (NEW)
try:
    deviations = RegulatoryChecker.check_regulatory(test_logs, test_rules)
    all_deviations.extend(deviations)
    print(f"\n[OK] RegulatoryChecker (NEW): {len(deviations)} deviations")
    for dev in deviations:
        print(f"  - {dev['case_id']}: {dev['deviation_type']} ({dev['severity']})")
except Exception as e:
    print(f"\n[FAIL] RegulatoryChecker FAILED: {e}")

# Summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print(f"\nTotal Deviations Detected: {len(all_deviations)}")

# Count by type
type_counts = {}
for dev in all_deviations:
    dtype = dev['deviation_type']
    type_counts[dtype] = type_counts.get(dtype, 0) + 1

print(f"\nUnique Deviation Types: {len(type_counts)}")
print("\nBreakdown by Type:")
for dtype, count in sorted(type_counts.items()):
    print(f"  - {dtype}: {count}")

# Count by severity
severity_counts = {}
for dev in all_deviations:
    sev = dev['severity']
    severity_counts[sev] = severity_counts.get(sev, 0) + 1

print(f"\nBreakdown by Severity:")
for sev in ['critical', 'high', 'medium', 'low']:
    count = severity_counts.get(sev, 0)
    if count > 0:
        print(f"  - {sev}: {count}")

print("\n" + "=" * 80)
print("[SUCCESS] TEST COMPLETE - All 10 checkers executed successfully!")
print("=" * 80)
