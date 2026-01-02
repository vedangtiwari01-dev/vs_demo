"""
Statistical Analysis Module for Deviation Analysis

This module provides comprehensive statistical analysis:
1. Distribution analysis (severity, deviation types)
2. Temporal patterns (time-based trends)
3. Officer-level statistics
4. Correlation analysis
5. Trend detection
"""

import logging
from typing import List, Dict, Any, Tuple
from collections import Counter, defaultdict
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)


class StatisticalAnalyzer:
    """
    Performs comprehensive statistical analysis on deviations.
    """

    @staticmethod
    def analyze(deviations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform comprehensive statistical analysis on cleaned deviations.

        Args:
            deviations: List of cleaned deviation dictionaries

        Returns:
            Dictionary containing all statistical insights
        """
        logger.info(f"Starting statistical analysis for {len(deviations)} deviations")

        if len(deviations) == 0:
            logger.warning("No deviations to analyze")
            return StatisticalAnalyzer._empty_analysis()

        analysis = {
            'overview': StatisticalAnalyzer._calculate_overview(deviations),
            'severity_distribution': StatisticalAnalyzer._analyze_severity(deviations),
            'deviation_type_distribution': StatisticalAnalyzer._analyze_deviation_types(deviations),
            'temporal_patterns': StatisticalAnalyzer._analyze_temporal_patterns(deviations),
            'officer_statistics': StatisticalAnalyzer._analyze_officers(deviations),
            'case_statistics': StatisticalAnalyzer._analyze_cases(deviations),
            'correlations': StatisticalAnalyzer._analyze_correlations(deviations),
            'risk_indicators': StatisticalAnalyzer._calculate_risk_indicators(deviations)
        }

        logger.info("Statistical analysis complete")
        return analysis

    @staticmethod
    def _empty_analysis() -> Dict[str, Any]:
        """Return empty analysis structure."""
        return {
            'overview': {'total_deviations': 0},
            'severity_distribution': {},
            'deviation_type_distribution': {},
            'temporal_patterns': {},
            'officer_statistics': {},
            'case_statistics': {},
            'correlations': {},
            'risk_indicators': {}
        }

    @staticmethod
    def _calculate_overview(deviations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate high-level overview statistics."""
        unique_cases = len(set(d['case_id'] for d in deviations))
        unique_officers = len(set(d['officer_id'] for d in deviations))

        return {
            'total_deviations': len(deviations),
            'unique_cases': unique_cases,
            'unique_officers': unique_officers,
            'average_deviations_per_case': round(len(deviations) / unique_cases, 2) if unique_cases > 0 else 0,
            'average_deviations_per_officer': round(len(deviations) / unique_officers, 2) if unique_officers > 0 else 0
        }

    @staticmethod
    def _analyze_severity(deviations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze severity distribution."""
        severity_counts = Counter(d['severity'] for d in deviations)
        total = len(deviations)

        severity_order = ['critical', 'high', 'medium', 'low']
        distribution = {}

        for severity in severity_order:
            count = severity_counts.get(severity, 0)
            distribution[severity] = {
                'count': count,
                'percentage': round((count / total) * 100, 2) if total > 0 else 0
            }

        # Calculate severity score (weighted average)
        severity_weights = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        total_weight = sum(severity_counts.get(s, 0) * w for s, w in severity_weights.items())
        severity_score = round((total_weight / total) * 25, 2) if total > 0 else 0  # Normalized to 0-100

        return {
            'distribution': distribution,
            'most_common': severity_counts.most_common(1)[0][0] if severity_counts else None,
            'severity_score': severity_score,  # 0-100 scale
            'severity_assessment': StatisticalAnalyzer._assess_severity_score(severity_score)
        }

    @staticmethod
    def _assess_severity_score(score: float) -> str:
        """Assess the overall severity level based on score."""
        if score >= 75:
            return 'Very High Risk - Immediate attention required'
        elif score >= 60:
            return 'High Risk - Urgent remediation needed'
        elif score >= 45:
            return 'Moderate Risk - Action plan required'
        elif score >= 30:
            return 'Low Risk - Monitoring recommended'
        else:
            return 'Minimal Risk - Routine oversight'

    @staticmethod
    def _analyze_deviation_types(deviations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze deviation type distribution."""
        type_counts = Counter(d['deviation_type'] for d in deviations)
        total = len(deviations)

        # Get top 10 deviation types
        top_types = []
        for dev_type, count in type_counts.most_common(10):
            top_types.append({
                'type': dev_type,
                'count': count,
                'percentage': round((count / total) * 100, 2)
            })

        # Group by category (based on naming patterns)
        categories = StatisticalAnalyzer._categorize_deviation_types(type_counts)

        return {
            'total_unique_types': len(type_counts),
            'top_10_types': top_types,
            'categories': categories
        }

    @staticmethod
    def _categorize_deviation_types(type_counts: Counter) -> Dict[str, Any]:
        """Categorize deviation types into logical groups."""
        categories = {
            'approval': ['approval', 'unauthorized_approver', 'self_approval', 'escalation'],
            'timing': ['timing_violation', 'tat_breach', 'cutoff_breach', 'delay'],
            'sequence': ['missing_step', 'wrong_sequence', 'unexpected_step', 'duplicate_step'],
            'documentation': ['document', 'missing_mandatory_document', 'expired_document'],
            'kyc_aml': ['kyc', 'aml', 'sanctions', 'pep', 'cdd'],
            'credit': ['credit', 'score', 'ltv_breach', 'emi_to_income'],
            'disbursement': ['disbursement', 'mandate', 'qc'],
            'collection': ['collection', 'restructure', 'writeoff'],
            'regulatory': ['regulatory', 'classification', 'provisioning'],
            'data_quality': ['missing_core_field', 'invalid_format', 'inconsistent_value']
        }

        category_counts = defaultdict(int)

        for dev_type, count in type_counts.items():
            categorized = False
            for category, keywords in categories.items():
                if any(keyword in dev_type.lower() for keyword in keywords):
                    category_counts[category] += count
                    categorized = True
                    break

            if not categorized:
                category_counts['other'] += count

        total = sum(category_counts.values())

        return {
            cat: {
                'count': count,
                'percentage': round((count / total) * 100, 2)
            }
            for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        }

    @staticmethod
    def _analyze_temporal_patterns(deviations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze time-based patterns in deviations."""
        # Extract timestamps
        timestamps = []
        for d in deviations:
            # Try to get timestamp from different possible fields
            timestamp = d.get('detected_at') or d.get('timestamp') or d.get('created_at')
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        # Try multiple datetime formats
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                            try:
                                dt = datetime.strptime(timestamp.split('.')[0], fmt)
                                timestamps.append(dt)
                                break
                            except ValueError:
                                continue
                    elif isinstance(timestamp, datetime):
                        timestamps.append(timestamp)
                except Exception as e:
                    logger.debug(f"Could not parse timestamp: {timestamp}, {e}")

        if not timestamps:
            logger.warning("No valid timestamps found for temporal analysis")
            return {
                'has_temporal_data': False,
                'message': 'No temporal data available'
            }

        # Hour distribution (0-23)
        hour_counts = Counter(dt.hour for dt in timestamps)
        hour_distribution = {}
        for hour in range(24):
            count = hour_counts.get(hour, 0)
            hour_distribution[f"{hour:02d}:00"] = count

        # Day of week distribution
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_counts = Counter(dt.weekday() for dt in timestamps)
        day_distribution = {day_names[i]: day_counts.get(i, 0) for i in range(7)}

        # Find peak hours
        peak_hours = [f"{h:02d}:00" for h, _ in hour_counts.most_common(3)]

        # Find peak days
        peak_days = [day_names[day] for day, _ in day_counts.most_common(3)]

        # Time period classification
        time_periods = {
            'morning': (6, 12),    # 6am - 12pm
            'afternoon': (12, 18),  # 12pm - 6pm
            'evening': (18, 24),    # 6pm - 12am
            'night': (0, 6)         # 12am - 6am
        }

        period_counts = Counter()
        for dt in timestamps:
            hour = dt.hour
            for period, (start, end) in time_periods.items():
                if start <= hour < end:
                    period_counts[period] += 1
                    break

        total = len(timestamps)
        period_distribution = {
            period: {
                'count': count,
                'percentage': round((count / total) * 100, 2)
            }
            for period, count in period_counts.items()
        }

        return {
            'has_temporal_data': True,
            'total_with_timestamps': len(timestamps),
            'hour_distribution': hour_distribution,
            'day_distribution': day_distribution,
            'period_distribution': period_distribution,
            'peak_hours': peak_hours,
            'peak_days': peak_days,
            'date_range': {
                'earliest': min(timestamps).strftime('%Y-%m-%d'),
                'latest': max(timestamps).strftime('%Y-%m-%d')
            } if timestamps else None
        }

    @staticmethod
    def _analyze_officers(deviations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze officer-level statistics."""
        officer_data = defaultdict(lambda: {
            'total_deviations': 0,
            'severity_counts': Counter(),
            'deviation_types': Counter(),
            'unique_cases': set()
        })

        for d in deviations:
            officer_id = d['officer_id']
            officer_data[officer_id]['total_deviations'] += 1
            officer_data[officer_id]['severity_counts'][d['severity']] += 1
            officer_data[officer_id]['deviation_types'][d['deviation_type']] += 1
            officer_data[officer_id]['unique_cases'].add(d['case_id'])

        # Calculate top officers
        top_officers = []
        for officer_id, data in sorted(officer_data.items(),
                                       key=lambda x: x[1]['total_deviations'],
                                       reverse=True)[:20]:
            top_officers.append({
                'officer_id': officer_id,
                'total_deviations': data['total_deviations'],
                'unique_cases': len(data['unique_cases']),
                'avg_deviations_per_case': round(data['total_deviations'] / len(data['unique_cases']), 2),
                'severity_breakdown': dict(data['severity_counts']),
                'top_deviation_type': data['deviation_types'].most_common(1)[0][0] if data['deviation_types'] else None
            })

        # Calculate distribution
        deviation_counts = [data['total_deviations'] for data in officer_data.values()]

        return {
            'total_officers': len(officer_data),
            'top_20_officers': top_officers,
            'distribution_stats': {
                'mean': round(statistics.mean(deviation_counts), 2) if deviation_counts else 0,
                'median': round(statistics.median(deviation_counts), 2) if deviation_counts else 0,
                'std_dev': round(statistics.stdev(deviation_counts), 2) if len(deviation_counts) > 1 else 0,
                'min': min(deviation_counts) if deviation_counts else 0,
                'max': max(deviation_counts) if deviation_counts else 0
            }
        }

    @staticmethod
    def _analyze_cases(deviations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze case-level statistics."""
        case_data = defaultdict(lambda: {
            'total_deviations': 0,
            'severity_counts': Counter(),
            'officers': set()
        })

        for d in deviations:
            case_id = d['case_id']
            case_data[case_id]['total_deviations'] += 1
            case_data[case_id]['severity_counts'][d['severity']] += 1
            case_data[case_id]['officers'].add(d['officer_id'])

        # Calculate top cases
        top_cases = []
        for case_id, data in sorted(case_data.items(),
                                    key=lambda x: x[1]['total_deviations'],
                                    reverse=True)[:10]:
            top_cases.append({
                'case_id': case_id,
                'total_deviations': data['total_deviations'],
                'unique_officers': len(data['officers']),
                'severity_breakdown': dict(data['severity_counts'])
            })

        # Calculate distribution
        deviation_counts = [data['total_deviations'] for data in case_data.values()]

        return {
            'total_cases': len(case_data),
            'top_10_cases': top_cases,
            'distribution_stats': {
                'mean': round(statistics.mean(deviation_counts), 2) if deviation_counts else 0,
                'median': round(statistics.median(deviation_counts), 2) if deviation_counts else 0,
                'std_dev': round(statistics.stdev(deviation_counts), 2) if len(deviation_counts) > 1 else 0,
                'min': min(deviation_counts) if deviation_counts else 0,
                'max': max(deviation_counts) if deviation_counts else 0
            }
        }

    @staticmethod
    def _analyze_correlations(deviations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze correlations between different attributes."""
        correlations = {}

        # Severity vs Deviation Type
        severity_type_matrix = defaultdict(lambda: defaultdict(int))
        for d in deviations:
            severity_type_matrix[d['severity']][d['deviation_type']] += 1

        # Convert to readable format
        severity_type_correlations = {}
        for severity in ['critical', 'high', 'medium', 'low']:
            if severity in severity_type_matrix:
                types = severity_type_matrix[severity]
                top_types = sorted(types.items(), key=lambda x: x[1], reverse=True)[:3]
                severity_type_correlations[severity] = [
                    {'type': t, 'count': c} for t, c in top_types
                ]

        correlations['severity_to_deviation_type'] = severity_type_correlations

        # Officer vs Severity (high-risk officers)
        officer_severity = defaultdict(lambda: Counter())
        for d in deviations:
            officer_severity[d['officer_id']][d['severity']] += 1

        high_risk_officers = []
        for officer_id, severities in officer_severity.items():
            critical_count = severities['critical']
            high_count = severities['high']
            total = sum(severities.values())

            risk_score = ((critical_count * 4 + high_count * 3) / (total * 4)) * 100 if total > 0 else 0

            if risk_score > 50:  # Officers with >50% critical/high severity
                high_risk_officers.append({
                    'officer_id': officer_id,
                    'risk_score': round(risk_score, 2),
                    'critical_count': critical_count,
                    'high_count': high_count,
                    'total_deviations': total
                })

        correlations['high_risk_officers'] = sorted(high_risk_officers,
                                                    key=lambda x: x['risk_score'],
                                                    reverse=True)[:10]

        return correlations

    @staticmethod
    def _calculate_risk_indicators(deviations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall risk indicators."""
        total = len(deviations)
        severity_counts = Counter(d['severity'] for d in deviations)

        # Critical mass indicator
        critical_percentage = (severity_counts['critical'] / total * 100) if total > 0 else 0
        high_percentage = (severity_counts['high'] / total * 100) if total > 0 else 0

        critical_mass_score = critical_percentage + (high_percentage * 0.75)

        # Concentration risk (are deviations concentrated in few officers?)
        officer_counts = Counter(d['officer_id'] for d in deviations)
        unique_officers = len(officer_counts)
        top_5_officer_percentage = sum(c for _, c in officer_counts.most_common(5)) / total * 100 if total > 0 else 0

        # Diversity of issues
        type_counts = Counter(d['deviation_type'] for d in deviations)
        diversity_score = len(type_counts) / total * 100 if total > 0 else 0

        return {
            'critical_mass_score': round(critical_mass_score, 2),
            'critical_mass_assessment': StatisticalAnalyzer._assess_critical_mass(critical_mass_score),
            'concentration_risk': {
                'top_5_officer_percentage': round(top_5_officer_percentage, 2),
                'is_concentrated': top_5_officer_percentage > 50,
                'unique_officers': unique_officers
            },
            'issue_diversity': {
                'unique_types': len(type_counts),
                'diversity_score': round(diversity_score, 2),
                'assessment': 'High diversity' if len(type_counts) > 15 else 'Low diversity'
            }
        }

    @staticmethod
    def _assess_critical_mass(score: float) -> str:
        """Assess the critical mass of high-severity deviations."""
        if score >= 75:
            return 'Critical - Systemic compliance failure'
        elif score >= 50:
            return 'Severe - Immediate executive attention required'
        elif score >= 30:
            return 'Elevated - Management intervention needed'
        elif score >= 15:
            return 'Moderate - Enhanced monitoring required'
        else:
            return 'Normal - Routine oversight sufficient'
