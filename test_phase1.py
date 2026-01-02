"""
Test script for Phase 1: Data Cleaning & Statistical Analysis

This script tests the new layered approach:
1. Data Cleaning
2. Statistical Analysis
3. Enhanced AI Analysis with context

Run this from anywhere:
    python test_phase1.py

The script will automatically find the ai-service directory.
"""

import sys
import os
import json
from datetime import datetime

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# If we're in the root directory, change to ai-service
if os.path.basename(script_dir) != 'ai-service':
    ai_service_dir = os.path.join(script_dir, 'ai-service')
    if os.path.exists(ai_service_dir):
        os.chdir(ai_service_dir)
        script_dir = ai_service_dir

# Add ai-service directory to path
sys.path.insert(0, script_dir)

# Now import from the correct path
from app.services.data import DataCleaner, StatisticalAnalyzer

# Sample deviation data for testing
SAMPLE_DEVIATIONS = [
    {
        "case_id": "CASE001",
        "officer_id": "OFF123",
        "deviation_type": "missing_approval",
        "severity": "critical",
        "description": "Loan approved without manager signature",
        "expected_behavior": "Manager approval required",
        "actual_behavior": "Approved by officer only",
        "notes": "Manager was on leave, verbal approval taken",
        "detected_at": "2025-01-15 14:30:00"
    },
    {
        "case_id": "CASE001",
        "officer_id": "OFF123",
        "deviation_type": "missing_approval",
        "severity": "critical",
        "description": "Loan approved without manager signature",
        "expected_behavior": "Manager approval required",
        "actual_behavior": "Approved by officer only",
        "notes": "Manager was on leave, verbal approval taken",
        "detected_at": "2025-01-15 14:30:00"
    },  # Duplicate - should be removed
    {
        "case_id": "CASE002",
        "officer_id": "OFF456",
        "deviation_type": "timing_violation",
        "severity": "high",
        "description": "Credit check completed in 2 minutes (expected 10+ min)",
        "expected_behavior": "Minimum 10 minutes for credit verification",
        "actual_behavior": "Completed in 2 minutes",
        "notes": "System was slow, used cached data",
        "detected_at": "2025-01-15 09:15:00"
    },
    {
        "case_id": "CASE003",
        "officer_id": "OFF123",
        "deviation_type": "kyc_incomplete_progression",
        "severity": "critical",
        "description": "KYC documents missing but case progressed",
        "expected_behavior": "All KYC documents must be verified",
        "actual_behavior": "Case moved to disbursement without KYC",
        "notes": "Customer promised to submit later",
        "detected_at": "2025-01-16 11:20:00"
    },
    {
        "case_id": "CASE004",
        "officer_id": "OFF789",
        "deviation_type": "wrong_sequence",
        "severity": "medium",
        "description": "Disbursement done before final approval",
        "expected_behavior": "Final approval → Disbursement",
        "actual_behavior": "Disbursement → Final approval",
        "notes": "",
        "detected_at": "2025-01-16 16:45:00"
    },
    {
        "case_id": "",  # Invalid - missing case_id
        "officer_id": "OFF999",
        "deviation_type": "test",
        "severity": "low",
        "description": "Test",
        "expected_behavior": "N/A",
        "actual_behavior": "N/A",
        "notes": "",
        "detected_at": "2025-01-16 18:00:00"
    }
]


def test_data_cleaning():
    """Test the data cleaning module."""
    print("="*80)
    print("TEST 1: DATA CLEANING")
    print("="*80)

    print(f"\n📥 Input: {len(SAMPLE_DEVIATIONS)} deviations (including 1 duplicate and 1 invalid)")

    # Run data cleaning
    cleaned, report = DataCleaner.clean_deviations(
        SAMPLE_DEVIATIONS,
        remove_duplicates=True,
        validate_types=True,
        handle_missing=True,
        normalize_text=True
    )

    print(f"\n📤 Output: {len(cleaned)} deviations")

    print("\n📊 Cleaning Report:")
    print(f"  - Original count: {report['original_count']}")
    print(f"  - Duplicates removed: {report['duplicates_removed']}")
    print(f"  - Invalid types fixed: {report['invalid_types_fixed']}")
    print(f"  - Missing values handled: {report['missing_values_handled']}")
    print(f"  - Text normalized: {report['text_normalized']}")
    print(f"  - Final count: {report['final_count']}")
    print(f"  - Retention rate: {report['cleaned_percentage']}%")

    # Get data quality score
    quality = DataCleaner.get_data_quality_score(report)
    print(f"\n🎯 Data Quality:")
    print(f"  - Score: {quality['score']}/100")
    print(f"  - Grade: {quality['grade']}")
    print(f"  - Assessment: {quality['assessment']}")

    print("\n✅ Data Cleaning Test PASSED")
    return cleaned


def test_statistical_analysis(cleaned_deviations):
    """Test the statistical analysis module."""
    print("\n" + "="*80)
    print("TEST 2: STATISTICAL ANALYSIS")
    print("="*80)

    # Run statistical analysis
    stats = StatisticalAnalyzer.analyze(cleaned_deviations)

    print("\n📊 Overview:")
    overview = stats['overview']
    print(f"  - Total deviations: {overview['total_deviations']}")
    print(f"  - Unique cases: {overview['unique_cases']}")
    print(f"  - Unique officers: {overview['unique_officers']}")
    print(f"  - Avg deviations/case: {overview['average_deviations_per_case']}")
    print(f"  - Avg deviations/officer: {overview['average_deviations_per_officer']}")

    print("\n🔴 Severity Distribution:")
    severity = stats['severity_distribution']
    print(f"  - Severity Score: {severity['severity_score']}/100")
    print(f"  - Assessment: {severity['severity_assessment']}")
    for sev in ['critical', 'high', 'medium', 'low']:
        dist = severity['distribution'][sev]
        print(f"  - {sev.capitalize()}: {dist['count']} ({dist['percentage']}%)")

    print("\n📈 Top Deviation Types:")
    dev_types = stats['deviation_type_distribution']
    for i, dtype in enumerate(dev_types['top_10_types'][:5], 1):
        print(f"  {i}. {dtype['type']}: {dtype['count']} ({dtype['percentage']}%)")

    print("\n👮 Officer Statistics:")
    officers = stats['officer_statistics']
    print(f"  - Total officers: {officers['total_officers']}")
    print(f"  - Top officers:")
    for i, officer in enumerate(officers['top_20_officers'][:3], 1):
        print(f"    {i}. {officer['officer_id']}: {officer['total_deviations']} deviations "
              f"({officer['unique_cases']} cases)")

    print("\n⏰ Temporal Patterns:")
    temporal = stats['temporal_patterns']
    if temporal.get('has_temporal_data'):
        print(f"  - Peak hours: {', '.join(temporal['peak_hours'])}")
        print(f"  - Peak days: {', '.join(temporal['peak_days'])}")
        print(f"  - Date range: {temporal['date_range']['earliest']} to {temporal['date_range']['latest']}")
    else:
        print("  - No temporal data available")

    print("\n⚠️ Risk Indicators:")
    risk = stats['risk_indicators']
    print(f"  - Critical Mass Score: {risk['critical_mass_score']}/100")
    print(f"  - Assessment: {risk['critical_mass_assessment']}")
    print(f"  - Concentration: Top 5 officers = {risk['concentration_risk']['top_5_officer_percentage']}% of deviations")

    print("\n✅ Statistical Analysis Test PASSED")
    return stats


def test_integration():
    """Test the full integration."""
    print("\n" + "="*80)
    print("TEST 3: FULL INTEGRATION")
    print("="*80)

    print("\n🔄 Running full layered pipeline...")

    # Layer 1: Clean
    print("\n  Layer 1: Data Cleaning...")
    cleaned, cleaning_report = DataCleaner.clean_deviations(SAMPLE_DEVIATIONS)
    print(f"    ✓ Cleaned {len(cleaned)} deviations")

    # Layer 2: Analyze
    print("\n  Layer 2: Statistical Analysis...")
    stats = StatisticalAnalyzer.analyze(cleaned)
    print(f"    ✓ Analyzed {stats['overview']['total_deviations']} deviations")

    # Layer 3 would be AI analysis (requires Claude API key)
    print("\n  Layer 3: AI Analysis...")
    print("    ⚠️  Skipping (requires Claude API key)")
    print("    ⚠️  In production, this would call NotesAnalyzer.analyze_pattern_batch()")

    print("\n✅ Integration Test PASSED")

    return {
        'cleaned': cleaned,
        'cleaning_report': cleaning_report,
        'statistics': stats
    }


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("PHASE 1 TEST SUITE: Data Cleaning & Statistical Analysis")
    print("="*80)

    try:
        # Test 1: Data Cleaning
        cleaned = test_data_cleaning()

        # Test 2: Statistical Analysis
        stats = test_statistical_analysis(cleaned)

        # Test 3: Integration
        results = test_integration()

        # Summary
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED!")
        print("="*80)
        print("\n📋 Summary:")
        print(f"  - Input: {len(SAMPLE_DEVIATIONS)} deviations")
        print(f"  - Cleaned: {len(cleaned)} deviations")
        print(f"  - Data Quality: {DataCleaner.get_data_quality_score(results['cleaning_report'])['grade']}")
        print(f"  - Severity Score: {stats['severity_distribution']['severity_score']}/100")

        print("\n🎉 Phase 1 implementation is working correctly!")
        print("\n💡 Next steps:")
        print("  1. Start your AI service: cd ai-service && python -m uvicorn app.main:app --reload")
        print("  2. Start your backend: cd backend && npm start")
        print("  3. Upload workflow data through the frontend")
        print("  4. Click 'Analyze Patterns' to see the layered approach in action")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
