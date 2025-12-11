from typing import List, Dict, Any
from datetime import datetime, timedelta
import random

class LogGenerator:
    """Generates synthetic workflow logs for stress testing"""

    STANDARD_STEPS = [
        'Application Received',
        'Document Verification',
        'Income Verification',
        'Credit Check',
        'Risk Assessment',
        'Manager Approval',
        'Final Approval'
    ]

    @staticmethod
    def generate(scenario_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate synthetic logs based on scenario"""

        if scenario_type == 'officer_shortage':
            logs = LogGenerator._generate_officer_shortage(parameters)
        elif scenario_type == 'peak_load':
            logs = LogGenerator._generate_peak_load(parameters)
        elif scenario_type == 'system_downtime':
            logs = LogGenerator._generate_system_downtime(parameters)
        elif scenario_type == 'regulatory_change':
            logs = LogGenerator._generate_regulatory_change(parameters)
        else:
            raise ValueError(f'Unknown scenario type: {scenario_type}')

        return {
            'logs': logs,
            'metadata': {
                'scenario_type': scenario_type,
                'parameters': parameters,
                'generated_at': datetime.now().isoformat(),
                'total_logs': len(logs)
            }
        }

    @staticmethod
    def _generate_officer_shortage(params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate logs simulating officer shortage scenario"""
        logs = []

        normal_officers = params.get('normal_officers', 10)
        reduced_officers = params.get('reduced_officers', 6)
        total_cases = params.get('total_cases', 100)
        days = params.get('days', 30)

        start_date = datetime.now() - timedelta(days=days)

        # Higher workload per officer = higher deviation probability
        cases_per_officer = total_cases / reduced_officers
        skip_probability = min(0.35, cases_per_officer / 25)

        for case_num in range(total_cases):
            case_id = f'CASE-{case_num + 1:04d}'
            officer_id = f'OFF-{random.randint(1, reduced_officers):03d}'

            # Random start day
            day_offset = random.randint(0, days - 1)
            case_start = start_date + timedelta(days=day_offset)

            # Random start hour (8 AM to 5 PM)
            case_start = case_start.replace(
                hour=random.randint(8, 17),
                minute=random.randint(0, 59)
            )

            current_time = case_start

            for step in LogGenerator.STANDARD_STEPS:
                # Skip steps based on workload pressure
                if random.random() < skip_probability:
                    continue

                logs.append({
                    'case_id': case_id,
                    'officer_id': officer_id,
                    'step_name': step,
                    'action': 'completed',
                    'timestamp': current_time.isoformat(),
                    'duration_seconds': random.randint(180, 900),  # 3-15 mins (rushed)
                    'status': 'completed'
                })

                # Shorter time between steps (rushed process)
                current_time += timedelta(minutes=random.randint(5, 30))

        return logs

    @staticmethod
    def _generate_peak_load(params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate logs simulating peak load scenario"""
        logs = []

        total_cases = params.get('total_cases', 150)
        officers = params.get('officers', 10)
        peak_hours = params.get('peak_hours', 4)  # Compressed into 4 hours

        start_time = datetime.now().replace(hour=9, minute=0, second=0)
        end_time = start_time + timedelta(hours=peak_hours)

        for case_num in range(total_cases):
            case_id = f'PEAK-{case_num + 1:04d}'
            officer_id = f'OFF-{random.randint(1, officers):03d}'

            # Random time within peak period
            total_seconds = int((end_time - start_time).total_seconds())
            random_seconds = random.randint(0, total_seconds)
            case_start = start_time + timedelta(seconds=random_seconds)

            current_time = case_start

            # Higher skip probability due to time pressure
            skip_prob = 0.25

            for step in LogGenerator.STANDARD_STEPS:
                if random.random() < skip_prob:
                    continue

                logs.append({
                    'case_id': case_id,
                    'officer_id': officer_id,
                    'step_name': step,
                    'action': 'completed',
                    'timestamp': current_time.isoformat(),
                    'duration_seconds': random.randint(120, 300),  # Very rushed (2-5 mins)
                    'status': 'completed'
                })

                current_time += timedelta(minutes=random.randint(2, 10))

        return logs

    @staticmethod
    def _generate_system_downtime(params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate logs simulating system downtime scenario"""
        logs = []

        total_cases = params.get('total_cases', 80)
        officers = params.get('officers', 10)
        downtime_hours = params.get('downtime_hours', 6)

        start_date = datetime.now() - timedelta(days=2)
        downtime_start = start_date + timedelta(hours=10)
        downtime_end = downtime_start + timedelta(hours=downtime_hours)

        for case_num in range(total_cases):
            case_id = f'CASE-{case_num + 1:04d}'
            officer_id = f'OFF-{random.randint(1, officers):03d}'

            case_start = start_date + timedelta(hours=random.randint(0, 48))
            current_time = case_start

            for step in LogGenerator.STANDARD_STEPS:
                # Skip if during downtime
                if downtime_start <= current_time <= downtime_end:
                    current_time = downtime_end + timedelta(minutes=random.randint(10, 60))

                logs.append({
                    'case_id': case_id,
                    'officer_id': officer_id,
                    'step_name': step,
                    'action': 'completed',
                    'timestamp': current_time.isoformat(),
                    'duration_seconds': random.randint(300, 1200),
                    'status': 'completed'
                })

                current_time += timedelta(minutes=random.randint(15, 60))

        return logs

    @staticmethod
    def _generate_regulatory_change(params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate logs simulating regulatory change scenario"""
        logs = []

        total_cases = params.get('total_cases', 100)
        officers = params.get('officers', 10)
        change_after_cases = params.get('change_after_cases', 50)

        # New required step after regulatory change
        new_step = params.get('new_step', 'Compliance Check')

        start_date = datetime.now() - timedelta(days=30)

        for case_num in range(total_cases):
            case_id = f'CASE-{case_num + 1:04d}'
            officer_id = f'OFF-{random.randint(1, officers):03d}'

            case_start = start_date + timedelta(hours=case_num * 5)
            current_time = case_start

            # Determine if this case is after regulatory change
            after_change = case_num >= change_after_cases

            steps = LogGenerator.STANDARD_STEPS.copy()
            if after_change:
                # Insert new step after Risk Assessment
                steps.insert(5, new_step)

            # Some officers miss the new step (confusion)
            skip_new_step = after_change and random.random() < 0.30

            for step in steps:
                if skip_new_step and step == new_step:
                    continue

                logs.append({
                    'case_id': case_id,
                    'officer_id': officer_id,
                    'step_name': step,
                    'action': 'completed',
                    'timestamp': current_time.isoformat(),
                    'duration_seconds': random.randint(300, 1800),
                    'status': 'completed'
                })

                current_time += timedelta(minutes=random.randint(20, 90))

        return logs
