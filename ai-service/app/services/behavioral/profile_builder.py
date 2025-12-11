from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict

class ProfileBuilder:
    """Builds behavioral profiles for officers"""

    @staticmethod
    def build_profile(officer_id: str, logs: List[Dict[str, Any]], deviations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build comprehensive behavioral profile"""

        # Calculate basic metrics
        total_cases = len(set(log['case_id'] for log in logs))
        deviation_count = len(deviations)
        deviation_rate = (deviation_count / total_cases * 100) if total_cases > 0 else 0

        # Calculate workload metrics
        workload_metrics = ProfileBuilder._calculate_workload(logs)

        # Calculate risk score
        risk_score = ProfileBuilder._calculate_risk_score(deviations, total_cases)

        return {
            'officer_id': officer_id,
            'total_cases': total_cases,
            'deviation_count': deviation_count,
            'deviation_rate': round(deviation_rate, 2),
            'average_workload': workload_metrics['average_daily_cases'],
            'risk_score': risk_score,
            'patterns': {
                'peak_workload_day': workload_metrics['peak_day'],
                'most_common_deviation': ProfileBuilder._get_most_common_deviation(deviations)
            }
        }

    @staticmethod
    def _calculate_workload(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate workload metrics"""
        if not logs:
            return {'average_daily_cases': 0, 'peak_day': 'N/A'}

        # Group by date
        daily_cases = defaultdict(set)
        for log in logs:
            date = datetime.fromisoformat(log['timestamp']).date()
            daily_cases[date].add(log['case_id'])

        # Calculate average
        case_counts = [len(cases) for cases in daily_cases.values()]
        avg_daily = sum(case_counts) / len(case_counts) if case_counts else 0

        # Find peak day
        peak_date = max(daily_cases.items(), key=lambda x: len(x[1]))[0] if daily_cases else None
        peak_day = peak_date.strftime('%Y-%m-%d') if peak_date else 'N/A'

        return {
            'average_daily_cases': round(avg_daily, 2),
            'peak_day': peak_day
        }

    @staticmethod
    def _calculate_risk_score(deviations: List[Dict[str, Any]], total_cases: int) -> float:
        """Calculate risk score based on deviations"""
        if not deviations:
            return 0.0

        # Weight by severity
        severity_weights = {
            'critical': 10,
            'high': 5,
            'medium': 2,
            'low': 1
        }

        total_score = sum(
            severity_weights.get(dev.get('severity', 'medium'), 2)
            for dev in deviations
        )

        # Normalize by total cases
        risk_score = (total_score / max(total_cases, 1)) * 10

        return min(round(risk_score, 2), 100.0)  # Cap at 100

    @staticmethod
    def _get_most_common_deviation(deviations: List[Dict[str, Any]]) -> str:
        """Get most common deviation type"""
        if not deviations:
            return 'None'

        deviation_counts = defaultdict(int)
        for dev in deviations:
            deviation_counts[dev.get('deviation_type', 'unknown')] += 1

        most_common = max(deviation_counts.items(), key=lambda x: x[1])
        return f"{most_common[0]} ({most_common[1]})"
