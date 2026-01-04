"""
Synthetic Workflow Log Generator with Hidden Patterns

Generates realistic loan workflow data with subtle compliance issues
designed to test ML clustering, anomaly detection, and pattern recognition.

Hidden patterns included:
1. Temporal bias: Certain officers skip steps during end-of-day rush (4-5 PM)
2. Product-based patterns: Credit checks skipped for "personal loans" but not others
3. Officer clusters: Groups of officers with similar deviation behaviors
4. Gradual drift: Compliance degrades slowly over time (change-point detection)
5. Rare anomalies: Unusual deviations that ML should flag
6. Day-of-week patterns: More deviations on Fridays
7. Hidden correlations: Self-approvals correlated with high loan amounts
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys

# Seed for reproducibility
random.seed(42)

# Configuration
NUM_CASES = 120  # Number of loan applications
DATE_START = datetime(2024, 1, 1)
DATE_END = datetime(2024, 2, 29)  # 60 days
NUM_OFFICERS = 18

# Officers with different behavioral profiles
OFFICER_PROFILES = {
    # Compliant officers (40%)
    'compliant': [f'EMP-{i:03d}' for i in range(1, 8)],

    # Temporal deviators - rush in evening (20%)
    'evening_rushers': [f'EMP-{i:03d}' for i in range(8, 12)],

    # Product-specific deviators - skip credit for personal loans (20%)
    'credit_skippers': [f'EMP-{i:03d}' for i in range(12, 16)],

    # High-risk officers - self-approve, skip multiple steps (15%)
    'high_risk': [f'EMP-{i:03d}' for i in range(16, 19)],

    # Drift officers - start compliant, gradually deviate (5%)
    'drift': ['EMP-019']
}

ALL_OFFICERS = [
    officer
    for profile_officers in OFFICER_PROFILES.values()
    for officer in profile_officers
]

# Loan products
PRODUCTS = ['home_loan', 'personal_loan', 'auto_loan', 'business_loan']

# Standard workflow steps (compliant)
STANDARD_WORKFLOW = [
    ('APPLICATION_RECEIVED', 'receive'),
    ('DOCUMENT_VERIFICATION', 'verify'),
    ('INCOME_VERIFICATION', 'verify'),
    ('CREDIT_ASSESSMENT', 'assess'),
    ('RISK_EVALUATION', 'evaluate'),
    ('APPROVAL_L1', 'approve'),
    ('APPROVAL_L2', 'approve'),
    ('DISBURSEMENT', 'disburse')
]

def get_officer_profile(officer_id: str) -> str:
    """Get the behavioral profile for an officer."""
    for profile, officers in OFFICER_PROFILES.items():
        if officer_id in officers:
            return profile
    return 'compliant'

def generate_case_id(case_num: int) -> str:
    """Generate realistic case ID."""
    return f"LN-2024-{case_num:05d}"

def get_random_timestamp(base_date: datetime, days_offset: int, hour_bias: str = 'normal') -> str:
    """Generate timestamp with optional hour bias."""
    date = base_date + timedelta(days=days_offset)

    if hour_bias == 'evening':
        # Bias towards 4-6 PM
        hour = random.choices(
            range(24),
            weights=[1]*9 + [2]*7 + [8, 10, 8] + [2]*5,  # Peak at 16-18
            k=1
        )[0]
    elif hour_bias == 'morning':
        # Bias towards 9-11 AM
        hour = random.choices(
            range(24),
            weights=[1]*9 + [8, 10, 8] + [2]*12,  # Peak at 9-11
            k=1
        )[0]
    else:
        # Normal distribution
        hour = random.randint(9, 18)

    minute = random.randint(0, 59)
    second = random.randint(0, 59)

    return date.replace(hour=hour, minute=minute, second=second).strftime('%Y-%m-%d %H:%M:%S')

def should_skip_step(officer_id: str, step_name: str, product: str, timestamp: str, days_elapsed: int) -> bool:
    """Determine if officer should skip a step based on hidden patterns."""
    profile = get_officer_profile(officer_id)
    dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    hour = dt.hour
    weekday = dt.weekday()

    # Pattern 1: Evening rushers skip verification steps between 4-6 PM
    if profile == 'evening_rushers' and 16 <= hour <= 18:
        if step_name in ['DOCUMENT_VERIFICATION', 'INCOME_VERIFICATION']:
            return random.random() < 0.7  # 70% chance to skip

    # Pattern 2: Credit skippers skip credit assessment for personal loans
    if profile == 'credit_skippers' and product == 'personal_loan':
        if step_name == 'CREDIT_ASSESSMENT':
            return random.random() < 0.8  # 80% chance to skip

    # Pattern 3: High-risk officers skip multiple steps and self-approve
    if profile == 'high_risk':
        if step_name in ['RISK_EVALUATION', 'INCOME_VERIFICATION']:
            return random.random() < 0.6  # 60% chance to skip

    # Pattern 4: Friday effect - all officers more likely to skip on Fridays
    if weekday == 4:  # Friday
        if step_name in ['DOCUMENT_VERIFICATION', 'INCOME_VERIFICATION']:
            return random.random() < 0.3  # 30% chance to skip

    # Pattern 5: Drift - compliance degrades over time
    if profile == 'drift':
        drift_probability = min(0.7, days_elapsed / 60 * 0.7)  # Increases to 70% by end
        if step_name in ['DOCUMENT_VERIFICATION', 'RISK_EVALUATION']:
            return random.random() < drift_probability

    # Baseline random skips (low probability)
    return random.random() < 0.05  # 5% baseline deviation rate

def should_self_approve(officer_id: str, step_name: str, loan_amount: float) -> bool:
    """Determine if officer performs self-approval (hidden pattern)."""
    profile = get_officer_profile(officer_id)

    # Pattern: High-risk officers self-approve on high-value loans
    if profile == 'high_risk':
        if step_name in ['APPROVAL_L1', 'APPROVAL_L2']:
            # More likely to self-approve on loans > 500k
            if loan_amount > 500000:
                return random.random() < 0.7  # 70% chance
            else:
                return random.random() < 0.4  # 40% chance

    # All officers occasionally self-approve (rare)
    return random.random() < 0.05

def generate_workflow_logs(num_cases: int) -> List[Dict[str, Any]]:
    """Generate synthetic workflow logs with hidden patterns."""
    logs = []

    print(f"Generating {num_cases} loan application workflows...")
    print("Hidden patterns embedded:")
    print("  1. Evening rushers (4-6 PM): Skip verification steps")
    print("  2. Credit skippers (personal loans): Skip credit assessment")
    print("  3. High-risk officers: Self-approve + skip multiple steps")
    print("  4. Friday effect: Increased skipping on Fridays")
    print("  5. Compliance drift: EMP-019 degrades over time")
    print("  6. Rare anomalies: Unusual step sequences")
    print()

    for case_num in range(1, num_cases + 1):
        case_id = generate_case_id(case_num)

        # Random product and loan amount
        product = random.choice(PRODUCTS)
        loan_amount = random.randint(50000, 2000000)

        # Random date within range
        days_range = (DATE_END - DATE_START).days
        case_start_day = random.randint(0, days_range - 5)  # Leave room for workflow
        days_elapsed = case_start_day  # For drift calculation

        # Assign primary officer (with some cases having multiple officers)
        primary_officer = random.choice(ALL_OFFICERS)

        # Generate workflow
        current_time = DATE_START + timedelta(days=case_start_day)
        step_num = 0

        # Track which steps were performed
        performed_steps = []

        for step_name, action in STANDARD_WORKFLOW:
            step_num += 1

            # Decide if step should be skipped
            timestamp = get_random_timestamp(
                current_time,
                0,
                hour_bias='evening' if get_officer_profile(primary_officer) == 'evening_rushers' else 'normal'
            )

            if should_skip_step(primary_officer, step_name, product, timestamp, days_elapsed):
                # Step skipped - creates missing_step deviation
                continue

            # Decide officer for this step
            officer = primary_officer

            # Approval steps might be done by different officer (or self-approved)
            if step_name in ['APPROVAL_L1', 'APPROVAL_L2']:
                if should_self_approve(primary_officer, step_name, loan_amount):
                    # Self-approval (deviation)
                    officer = primary_officer
                else:
                    # Proper approval by different officer
                    other_officers = [o for o in ALL_OFFICERS if o != primary_officer]
                    officer = random.choice(other_officers)

            # Add log entry
            logs.append({
                'case_id': case_id,
                'officer_id': officer,
                'step_name': step_name,
                'action': action.upper(),
                'timestamp': timestamp,
                'duration_seconds': random.randint(30, 3600),
                'status': 'completed',
                'metadata': {
                    'product_type': product,
                    'loan_amount': loan_amount,
                    'step_number': step_num
                }
            })

            performed_steps.append(step_name)

            # Move time forward
            current_time += timedelta(minutes=random.randint(5, 120))

        # Occasionally add wrong sequence (rare anomaly)
        if random.random() < 0.05:  # 5% of cases
            # Add a step out of order
            anomaly_step = random.choice(['CREDIT_ASSESSMENT', 'RISK_EVALUATION'])
            if anomaly_step not in performed_steps:
                logs.append({
                    'case_id': case_id,
                    'officer_id': primary_officer,
                    'step_name': anomaly_step,
                    'action': 'ASSESS',
                    'timestamp': get_random_timestamp(current_time, 0),
                    'duration_seconds': random.randint(30, 1800),
                    'status': 'completed',
                    'metadata': {
                        'product_type': product,
                        'loan_amount': loan_amount,
                        'step_number': 99  # Out of sequence
                    }
                })

        if case_num % 20 == 0:
            print(f"  Generated {case_num}/{num_cases} cases...")

    print(f"\n[OK] Generated {len(logs)} workflow log entries")
    return logs

def generate_sop_rules() -> List[Dict[str, Any]]:
    """Generate SOP rules for validation."""
    rules = [
        {
            'id': 1,
            'rule_type': 'sequence',
            'rule_description': 'APPLICATION_RECEIVED must be the first step',
            'step_number': 1,
            'severity': 'critical',
            'expected_sequence': ['APPLICATION_RECEIVED']
        },
        {
            'id': 2,
            'rule_type': 'sequence',
            'rule_description': 'DOCUMENT_VERIFICATION must occur before CREDIT_ASSESSMENT',
            'step_number': 2,
            'severity': 'high',
            'expected_sequence': ['APPLICATION_RECEIVED', 'DOCUMENT_VERIFICATION']
        },
        {
            'id': 3,
            'rule_type': 'mandatory_step',
            'rule_description': 'INCOME_VERIFICATION is mandatory for all loan applications',
            'step_number': 3,
            'severity': 'critical',
            'required_steps': ['INCOME_VERIFICATION']
        },
        {
            'id': 4,
            'rule_type': 'mandatory_step',
            'rule_description': 'CREDIT_ASSESSMENT is mandatory',
            'step_number': 4,
            'severity': 'critical',
            'required_steps': ['CREDIT_ASSESSMENT']
        },
        {
            'id': 5,
            'rule_type': 'approval',
            'rule_description': 'Two-level approval required - APPROVAL_L1 and APPROVAL_L2',
            'step_number': 6,
            'severity': 'high',
            'approval_levels': 2
        },
        {
            'id': 6,
            'rule_type': 'approval',
            'rule_description': 'Self-approval not permitted - approver must differ from case officer',
            'step_number': 6,
            'severity': 'critical',
            'validation': 'different_officer'
        }
    ]
    return rules

def analyze_hidden_patterns(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the generated data to show what hidden patterns exist."""
    from collections import defaultdict, Counter

    print("\n" + "="*80)
    print("HIDDEN PATTERNS EMBEDDED IN SYNTHETIC DATA")
    print("="*80)

    # Pattern 1: Temporal analysis
    timestamps = [datetime.strptime(log['timestamp'], '%Y-%m-%d %H:%M:%S') for log in logs]
    hour_dist = Counter(dt.hour for dt in timestamps)
    peak_hours = sorted(hour_dist.items(), key=lambda x: x[1], reverse=True)[:3]
    print(f"\n1. TEMPORAL PATTERN:")
    print(f"   Peak activity hours: {', '.join(f'{h}:00 ({c} logs)' for h, c in peak_hours)}")
    print(f"   → Evening rushers (EMP-008 to EMP-011) bias towards 4-6 PM")

    # Pattern 2: Officer clusters
    officer_steps = defaultdict(Counter)
    for log in logs:
        officer_steps[log['officer_id']][log['step_name']] += 1

    print(f"\n2. OFFICER CLUSTERS:")
    print(f"   Total officers: {len(officer_steps)}")
    print(f"   → Compliant: EMP-001 to EMP-007 (normal patterns)")
    print(f"   → Evening rushers: EMP-008 to EMP-011 (skip verification 4-6 PM)")
    print(f"   → Credit skippers: EMP-012 to EMP-015 (skip credit on personal loans)")
    print(f"   → High-risk: EMP-016 to EMP-018 (self-approve + skip multiple)")
    print(f"   → Drift: EMP-019 (compliance degrades over 60 days)")

    # Pattern 3: Product-based patterns
    product_steps = defaultdict(Counter)
    for log in logs:
        product = log.get('metadata', {}).get('product_type')
        if product:
            product_steps[product][log['step_name']] += 1

    print(f"\n3. PRODUCT-BASED PATTERNS:")
    for product, steps in product_steps.items():
        credit_count = steps.get('CREDIT_ASSESSMENT', 0)
        total = sum(steps.values())
        print(f"   {product}: Credit assessment in {credit_count}/{total} logs ({credit_count/total*100:.1f}%)")
    print(f"   → Personal loans have lower credit assessment rate (credit skippers)")

    # Pattern 4: Friday effect
    weekday_dist = Counter(dt.weekday() for dt in timestamps)
    print(f"\n4. DAY-OF-WEEK PATTERN:")
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    for day_num, count in sorted(weekday_dist.items()):
        print(f"   {days[day_num]}: {count} logs")
    print(f"   → Friday has more activity + higher skip rate")

    # Pattern 5: Drift over time
    dates = sorted(set(dt.date() for dt in timestamps))
    first_week = [dt for dt in timestamps if dt.date() <= dates[6]]
    last_week = [dt for dt in timestamps if dt.date() >= dates[-7]]

    print(f"\n5. COMPLIANCE DRIFT:")
    print(f"   First week logs: {len(first_week)}")
    print(f"   Last week logs: {len(last_week)}")
    print(f"   → EMP-019 shows increasing deviation rate over time")

    # Pattern 6: Rare anomalies
    case_steps = defaultdict(list)
    for log in logs:
        case_steps[log['case_id']].append((log.get('metadata', {}).get('step_number', 0), log['step_name']))

    anomalies = 0
    for case_id, steps in case_steps.items():
        steps_sorted = sorted(steps, key=lambda x: x[0])
        if len(steps_sorted) > 1:
            for i in range(len(steps_sorted) - 1):
                if steps_sorted[i][0] > steps_sorted[i+1][0]:
                    anomalies += 1
                    break

    print(f"\n6. RARE ANOMALIES:")
    print(f"   Cases with out-of-sequence steps: ~{anomalies}")
    print(f"   → Should be detected by anomaly detection (Isolation Forest)")

    print("\n" + "="*80)
    print("ML FEATURES THAT SHOULD ACTIVATE:")
    print("="*80)
    print(f"[OK] Clustering: Should identify 4-5 officer behavior groups")
    print(f"[OK] Anomaly Detection: Should flag ~{int(len(set(log['case_id'] for log in logs)) * 0.1)} cases")
    print(f"[OK] Temporal Patterns: Should detect evening peaks and Friday effect")
    print(f"[OK] Correlations: Credit skipping correlated with personal loans")
    print(f"[OK] Change-Point: Should detect drift in EMP-019's behavior")
    print(f"[OK] Intelligent Sampling: Will compress {len(set(log['case_id'] for log in logs))} cases to ~75 representatives")
    print("="*80 + "\n")

def main():
    """Generate and save synthetic data."""
    print("="*80)
    print("SYNTHETIC WORKFLOW DATA GENERATOR")
    print("="*80)
    print()

    # Generate data
    logs = generate_workflow_logs(NUM_CASES)
    rules = generate_sop_rules()

    # Save to files
    logs_file = 'synthetic_workflow_logs.json'
    rules_file = 'synthetic_sop_rules.json'

    with open(logs_file, 'w') as f:
        json.dump(logs, f, indent=2)
    print(f"📄 Saved workflow logs to: {logs_file}")

    with open(rules_file, 'w') as f:
        json.dump(rules, f, indent=2)
    print(f"📄 Saved SOP rules to: {rules_file}")

    # Analyze patterns
    analyze_hidden_patterns(logs)

    # Statistics
    unique_cases = len(set(log['case_id'] for log in logs))
    unique_officers = len(set(log['officer_id'] for log in logs))
    date_range = (DATE_END - DATE_START).days

    print("[STATS] DATASET STATISTICS:")
    print(f"   Total log entries: {len(logs)}")
    print(f"   Unique cases: {unique_cases}")
    print(f"   Unique officers: {unique_officers}")
    print(f"   Date range: {date_range} days ({DATE_START.date()} to {DATE_END.date()})")
    print(f"   Avg logs per case: {len(logs) / unique_cases:.1f}")
    print()
    print("[OK] Synthetic data generation complete!")
    print("   Run 'python test_intensive.py' to test with this data")

if __name__ == '__main__':
    main()
