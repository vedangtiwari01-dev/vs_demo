import pandas as pd
import random
import datetime
import uuid

# --- CONFIGURATION ---
NUM_LOANS = 250  # This will generate approx 1,200 - 1,500 log rows
START_DATE = datetime.datetime(2025, 1, 1)

# Roles and Limits
ROLES = {
    'Junior Analyst': {'limit': 0, 'id_prefix': 'JR'},
    'Senior Officer': {'limit': 50000, 'id_prefix': 'SR'},
    'Regional Manager': {'limit': 200000, 'id_prefix': 'MGR'}
}

USERS = {
    'Junior Analyst': ['j_doe', 'a_smith', 'b_wayne'],
    'Senior Officer': ['s_connor', 'l_skywalker', 'r_ripley'],
    'Regional Manager': ['m_scott', 'd_vader']
}

# --- HELPER FUNCTIONS ---
def random_date(start, end):
    return start + datetime.timedelta(
        seconds=random.randint(0, int((end - start).total_seconds())))

def generate_loan_id():
    return f"LN-{random.randint(10000, 99999)}"

# --- MAIN GENERATOR ---
data_rows = []

for _ in range(NUM_LOANS):
    # 1. Setup Loan Application
    loan_id = generate_loan_id()
    app_date = random_date(START_DATE, START_DATE + datetime.timedelta(days=30))
    
    # Loan Attributes
    amount = round(random.uniform(5000, 150000), -2) # Round to nearest 100
    credit_score = int(random.triangular(550, 850, 720)) # Skewed towards 720
    collateral_val = amount * random.uniform(0.8, 1.5) # Sometimes under-collateralized
    
    # Deviation Scenarios (Randomly selected)
    scenario = random.choices(
        ['HappyPath', 'SkippedFraud', 'AuthBreach', 'LowScore_Approve', 'UnderCollateral_Approve'], 
        weights=[60, 10, 15, 10, 5]
    )[0]
    
    # --- STEP 1: Application Received ---
    current_time = app_date
    data_rows.append({
        'Loan_ID': loan_id,
        'Loan_Amount': amount,
        'Credit_Score': credit_score,
        'Collateral_Value': round(collateral_val, 2),
        'Timestamp': current_time,
        'Activity': 'Application Received',
        'User': 'System',
        'Role': 'System',
        'Decision': 'Initiated',
        'Notes': 'Application received via portal.'
    })

    # --- STEP 2: KYC Check (Junior Analyst) ---
    current_time += datetime.timedelta(hours=random.randint(1, 4))
    kyc_user = random.choice(USERS['Junior Analyst'])
    data_rows.append({
        'Loan_ID': loan_id,
        'Loan_Amount': amount,
        'Credit_Score': credit_score,
        'Collateral_Value': round(collateral_val, 2),
        'Timestamp': current_time,
        'Activity': 'KYC Verification',
        'User': kyc_user,
        'Role': 'Junior Analyst',
        'Decision': 'Pass',
        'Notes': 'Docs verified.'
    })

    # --- STEP 3: Risk & Fraud Check (Potential Failure Point) ---
    current_time += datetime.timedelta(hours=random.randint(1, 24))
    
    if scenario == 'SkippedFraud':
        # PROCESS FAILURE: User skips fraud check to save time
        notes = random.choice([
            "System slow, skipped check for known client.", 
            "Expedited request from branch manager.",
            "Client waiting in lobby, bypassed check."
        ])
        # Note: In a real log, the activity might be missing, or marked 'Skipped'
        data_rows.append({
            'Loan_ID': loan_id,
            'Loan_Amount': amount,
            'Credit_Score': credit_score,
            'Collateral_Value': round(collateral_val, 2),
            'Timestamp': current_time,
            'Activity': 'Fraud Check',
            'User': random.choice(USERS['Senior Officer']),
            'Role': 'Senior Officer',
            'Decision': 'Skipped', # ! RED FLAG
            'Notes': notes
        })
    else:
        data_rows.append({
            'Loan_ID': loan_id,
            'Loan_Amount': amount,
            'Credit_Score': credit_score,
            'Collateral_Value': round(collateral_val, 2),
            'Timestamp': current_time,
            'Activity': 'Fraud Check',
            'User': 'System',
            'Role': 'System',
            'Decision': 'Clear',
            'Notes': 'No database hits.'
        })

    # --- STEP 4: Final Approval (The Critical Deviation Point) ---
    current_time += datetime.timedelta(hours=random.randint(1, 5))
    
    # Determine who is acting
    if scenario == 'AuthBreach':
        # Junior or Senior approves above their limit
        if amount > 50000:
            actor = random.choice(USERS['Senior Officer']) # Should be Manager
            role = 'Senior Officer'
            note = "Manager out of office, approved per verbal instruction."
        else:
            actor = random.choice(USERS['Junior Analyst']) # Should be Senior
            role = 'Junior Analyst'
            note = "Approved based on previous relationship."
    else:
        # Correct Authority
        if amount > 50000:
            actor = random.choice(USERS['Regional Manager'])
            role = 'Regional Manager'
            note = "High value approval granted."
        else:
            actor = random.choice(USERS['Senior Officer'])
            role = 'Senior Officer'
            note = "Standard approval."

    # Determine Decision based on Scenarios
    decision = 'Approved'
    
    # Logic for bad approvals
    if scenario == 'LowScore_Approve' and credit_score < 650:
        note = f"Score {credit_score} low but client has high deposits. Exception granted."
    elif scenario == 'UnderCollateral_Approve' and collateral_val < (amount * 1.2):
        note = "Collateral slightly short, approved as unsecured portion."
    
    # Final Log Entry
    data_rows.append({
        'Loan_ID': loan_id,
        'Loan_Amount': amount,
        'Credit_Score': credit_score,
        'Collateral_Value': round(collateral_val, 2),
        'Timestamp': current_time,
        'Activity': 'Final Approval',
        'User': actor,
        'Role': role,
        'Decision': decision,
        'Notes': note
    })

# Convert to DataFrame and Save
df = pd.DataFrame(data_rows)
df = df.sort_values(by=['Timestamp']) # Global chronological order
df.to_csv('loan_process_log_with_deviations.csv', index=False)

print(f"Successfully generated {len(df)} rows of data in 'loan_process_log_with_deviations.csv'")