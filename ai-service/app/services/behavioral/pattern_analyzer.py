from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict

class PatternAnalyzer:
    """Detects behavioral patterns in officer activity"""

    @staticmethod
    def detect_patterns(officer_id: str, logs: List[Dict[str, Any]], deviations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect behavioral patterns"""
        patterns = []

        if not logs or not deviations:
            return patterns

        # Detect workload-based patterns
        workload_patterns = PatternAnalyzer._detect_workload_patterns(logs, deviations)
        patterns.extend(workload_patterns)

        # Detect time-based patterns
        time_patterns = PatternAnalyzer._detect_time_patterns(logs, deviations)
        patterns.extend(time_patterns)

        # Detect step-specific patterns
        step_patterns = PatternAnalyzer._detect_step_patterns(deviations)
        patterns.extend(step_patterns)

        return patterns

    @staticmethod
    def _detect_workload_patterns(logs: List[Dict[str, Any]], deviations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect patterns related to workload"""
        patterns = []

        # Group by date
        daily_data = defaultdict(lambda: {'cases': set(), 'deviations': 0})

        for log in logs:
            date = datetime.fromisoformat(log['timestamp']).date()
            daily_data[date]['cases'].add(log['case_id'])

        for dev in deviations:
            date = datetime.fromisoformat(dev['detected_at']).date()
            daily_data[date]['deviations'] += 1

        # Analyze workload vs deviation correlation
        high_workload_days = []
        low_workload_days = []

        for date, data in daily_data.items():
            case_count = len(data['cases'])
            dev_count = data['deviations']

            if case_count > 15:  # High workload threshold
                high_workload_days.append({'cases': case_count, 'deviations': dev_count})
            elif case_count < 8:  # Low workload
                low_workload_days.append({'cases': case_count, 'deviations': dev_count})

        # Calculate deviation rates
        if high_workload_days:
            high_dev_rate = sum(d['deviations'] for d in high_workload_days) / len(high_workload_days)
            avg_high_workload = sum(d['cases'] for d in high_workload_days) / len(high_workload_days)

            if high_dev_rate > 2:  # More than 2 deviations per day on average
                patterns.append({
                    'pattern_type': 'workload_threshold',
                    'description': f'Deviation rate increases when workload exceeds {avg_high_workload:.0f} cases/day',
                    'trigger_condition': {
                        'workload_threshold': round(avg_high_workload),
                        'deviation_increase': round(high_dev_rate, 2)
                    },
                    'frequency': len(high_workload_days),
                    'confidence_score': 0.85
                })

        return patterns

    @staticmethod
    def _detect_time_patterns(logs: List[Dict[str, Any]], deviations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect time-based patterns"""
        patterns = []

        # Group deviations by day of week
        weekday_deviations = defaultdict(int)

        for dev in deviations:
            date = datetime.fromisoformat(dev['detected_at'])
            weekday = date.strftime('%A')
            weekday_deviations[weekday] += 1

        if weekday_deviations:
            max_day = max(weekday_deviations.items(), key=lambda x: x[1])
            total_deviations = sum(weekday_deviations.values())
            day_percentage = (max_day[1] / total_deviations) * 100

            if day_percentage > 30:  # If more than 30% on one day
                patterns.append({
                    'pattern_type': 'time_based',
                    'description': f'Higher deviation rate on {max_day[0]}s ({max_day[1]} deviations, {day_percentage:.0f}%)',
                    'trigger_condition': {
                        'day_of_week': max_day[0],
                        'deviation_count': max_day[1]
                    },
                    'frequency': max_day[1],
                    'confidence_score': 0.75
                })

        return patterns

    @staticmethod
    def _detect_step_patterns(deviations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect step-specific patterns"""
        patterns = []

        # Group deviations by type
        deviation_types = defaultdict(int)

        for dev in deviations:
            dev_type = dev.get('deviation_type', 'unknown')
            deviation_types[dev_type] += 1

        # Find most frequent deviation
        if deviation_types:
            most_common = max(deviation_types.items(), key=lambda x: x[1])

            if most_common[1] >= 3:  # At least 3 occurrences
                # Extract specific step if available
                specific_deviations = [d for d in deviations if d.get('deviation_type') == most_common[0]]
                context = specific_deviations[0].get('context', {}) if specific_deviations else {}

                description = f'Frequently commits {most_common[0].replace("_", " ")} ({most_common[1]} times)'

                if 'missing_step' in context:
                    description += f': often skips {context["missing_step"]}'

                patterns.append({
                    'pattern_type': 'step_specific',
                    'description': description,
                    'trigger_condition': {
                        'deviation_type': most_common[0],
                        'frequency': most_common[1]
                    },
                    'frequency': most_common[1],
                    'confidence_score': 0.90
                })

        return patterns
