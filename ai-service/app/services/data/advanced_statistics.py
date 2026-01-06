"""
Advanced Statistical Analysis Module

Provides advanced statistical methods including:
1. Correlation analysis (Pearson, Spearman, Cramér's V, Chi-square)
2. Association rules (Lift, Odds ratios)
3. Time-series analysis (Moving averages, exponential smoothing, rolling std)
4. Control charts (Shewhart, CUSUM, EWMA)
5. Change-point detection

Dependencies: scipy, pandas, ruptures
"""

import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter, defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    from scipy import stats
    from scipy.stats import chi2_contingency, contingency
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("scipy not available - correlation analysis will be limited")

try:
    import ruptures as rpt
    RUPTURES_AVAILABLE = True
except ImportError:
    RUPTURES_AVAILABLE = False
    logger.warning("ruptures not available - change-point detection disabled")


class AdvancedStatistics:
    """
    Advanced statistical analysis methods for deviation analysis.
    """

    @staticmethod
    def analyze_correlations(deviations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Comprehensive correlation analysis including:
        - Pearson correlation (continuous variables)
        - Spearman correlation (ordinal variables)
        - Cramér's V (categorical variables)
        - Chi-square tests for independence
        """
        if not SCIPY_AVAILABLE:
            logger.warning("scipy not available - skipping correlation analysis")
            return {'available': False, 'message': 'scipy not installed'}

        logger.info("Starting advanced correlation analysis")

        results = {
            'available': True,
            'pearson_correlations': {},
            'spearman_correlations': {},
            'cramers_v': {},
            'chi_square_tests': {}
        }

        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(deviations)

        # Pearson correlation for numeric variables
        numeric_cols = ['duration_seconds'] if 'duration_seconds' in df.columns else []
        if len(numeric_cols) > 0:
            # Add severity as numeric (critical=4, high=3, medium=2, low=1)
            df['severity_numeric'] = df['severity'].map({
                'critical': 4, 'high': 3, 'medium': 2, 'low': 1
            })
            numeric_cols.append('severity_numeric')

            if len(numeric_cols) >= 2:
                pearson_corr = df[numeric_cols].corr(method='pearson')
                results['pearson_correlations'] = pearson_corr.to_dict()

        # Spearman correlation (rank-based, good for ordinal data)
        if len(numeric_cols) >= 2:
            spearman_corr = df[numeric_cols].corr(method='spearman')
            results['spearman_correlations'] = spearman_corr.to_dict()

        # Cramér's V for categorical associations
        categorical_pairs = [
            ('severity', 'deviation_type'),
            ('officer_id', 'deviation_type'),
            ('deviation_type', 'case_id')
        ]

        for col1, col2 in categorical_pairs:
            if col1 in df.columns and col2 in df.columns:
                cramers_v = AdvancedStatistics._calculate_cramers_v(
                    df[col1].values, df[col2].values
                )
                results['cramers_v'][f"{col1}_vs_{col2}"] = {
                    'value': cramers_v,
                    'interpretation': AdvancedStatistics._interpret_cramers_v(cramers_v)
                }

        # Chi-square tests for independence
        for col1, col2 in categorical_pairs:
            if col1 in df.columns and col2 in df.columns:
                chi_square_result = AdvancedStatistics._chi_square_test(
                    df[col1].values, df[col2].values
                )
                results['chi_square_tests'][f"{col1}_vs_{col2}"] = chi_square_result

        logger.info("Correlation analysis complete")
        return results

    @staticmethod
    def _calculate_cramers_v(x: np.ndarray, y: np.ndarray) -> float:
        """
        Calculate Cramér's V statistic for categorical association.

        V ranges from 0 (no association) to 1 (complete association).
        """
        # Create contingency table
        contingency_table = pd.crosstab(x, y)

        # Chi-square test
        chi2, p, dof, expected = chi2_contingency(contingency_table)

        # Total sample size
        n = contingency_table.sum().sum()

        # Minimum dimension
        min_dim = min(contingency_table.shape[0] - 1, contingency_table.shape[1] - 1)

        # Cramér's V formula
        cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0

        return round(cramers_v, 4)

    @staticmethod
    def _interpret_cramers_v(v: float) -> str:
        """Interpret Cramér's V value."""
        if v < 0.1:
            return "Negligible association"
        elif v < 0.3:
            return "Weak association"
        elif v < 0.5:
            return "Moderate association"
        else:
            return "Strong association"

    @staticmethod
    def _chi_square_test(x: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """
        Perform chi-square test for independence.
        """
        contingency_table = pd.crosstab(x, y)
        chi2, p_value, dof, expected = chi2_contingency(contingency_table)

        return {
            'chi_square_statistic': round(chi2, 4),
            'p_value': round(p_value, 6),
            'degrees_of_freedom': int(dof),
            'is_significant': bool(p_value < 0.05),  # Convert numpy.bool_ to Python bool
            'interpretation': 'Variables are dependent (related)' if p_value < 0.05 else 'Variables are independent (not related)'
        }

    @staticmethod
    def calculate_lift_and_odds(deviations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate lift and odds ratios for association rules.

        Example: What's the lift of "critical severity" given "officer X"?
        """
        logger.info("Calculating lift and odds ratios")

        results = {
            'officer_to_deviation_type': [],
            'officer_to_severity': [],
            'deviation_type_to_severity': []
        }

        df = pd.DataFrame(deviations)
        total = len(df)

        # Officer → Deviation Type lift
        for officer in df['officer_id'].unique()[:20]:  # Top 20 officers
            officer_count = len(df[df['officer_id'] == officer])

            for dev_type in df['deviation_type'].unique()[:10]:  # Top 10 types
                type_count = len(df[df['deviation_type'] == dev_type])
                both_count = len(df[(df['officer_id'] == officer) & (df['deviation_type'] == dev_type)])

                if both_count > 0:
                    # P(type | officer)
                    confidence = both_count / officer_count

                    # P(type)
                    support = type_count / total

                    # Lift = P(type | officer) / P(type)
                    lift = confidence / support if support > 0 else 0

                    if lift > 1.5:  # Only show significant lifts
                        results['officer_to_deviation_type'].append({
                            'officer': officer,
                            'deviation_type': dev_type,
                            'lift': round(lift, 2),
                            'confidence': round(confidence * 100, 2),
                            'support': round(support * 100, 2),
                            'count': both_count
                        })

        # Officer → Severity lift
        for officer in df['officer_id'].unique()[:20]:
            officer_count = len(df[df['officer_id'] == officer])

            for severity in ['critical', 'high']:
                severity_count = len(df[df['severity'] == severity])
                both_count = len(df[(df['officer_id'] == officer) & (df['severity'] == severity)])

                if both_count > 0:
                    confidence = both_count / officer_count
                    support = severity_count / total
                    lift = confidence / support if support > 0 else 0

                    # Odds ratio
                    odds_officer = both_count / (officer_count - both_count) if (officer_count - both_count) > 0 else 0
                    odds_overall = severity_count / (total - severity_count) if (total - severity_count) > 0 else 0
                    odds_ratio = odds_officer / odds_overall if odds_overall > 0 else 0

                    if lift > 1.3:
                        results['officer_to_severity'].append({
                            'officer': officer,
                            'severity': severity,
                            'lift': round(lift, 2),
                            'odds_ratio': round(odds_ratio, 2),
                            'confidence': round(confidence * 100, 2),
                            'count': both_count
                        })

        # Sort by lift
        results['officer_to_deviation_type'] = sorted(
            results['officer_to_deviation_type'],
            key=lambda x: x['lift'],
            reverse=True
        )[:20]

        results['officer_to_severity'] = sorted(
            results['officer_to_severity'],
            key=lambda x: x['lift'],
            reverse=True
        )[:20]

        logger.info(f"Found {len(results['officer_to_deviation_type'])} significant officer→type associations")
        logger.info(f"Found {len(results['officer_to_severity'])} significant officer→severity associations")

        return results

    @staticmethod
    def time_series_analysis(deviations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Time-series analysis including:
        - Moving averages
        - Exponential smoothing
        - Rolling standard deviation
        """
        logger.info("Starting time-series analysis")

        # Extract timestamps
        timestamps = []
        for d in deviations:
            timestamp = d.get('detected_at') or d.get('timestamp') or d.get('created_at')
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                            try:
                                dt = datetime.strptime(timestamp.split('.')[0], fmt)
                                timestamps.append((dt, d))
                                break
                            except ValueError:
                                continue
                except Exception:
                    continue

        if len(timestamps) < 7:  # Need at least a week of data
            return {
                'available': False,
                'message': 'Insufficient temporal data for time-series analysis (need at least 7 data points)'
            }

        # Sort by timestamp
        timestamps.sort(key=lambda x: x[0])

        # Create daily counts
        daily_counts = defaultdict(int)
        daily_severity_scores = defaultdict(list)

        severity_weights = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}

        for dt, dev in timestamps:
            date = dt.date()
            daily_counts[date] += 1
            daily_severity_scores[date].append(severity_weights.get(dev['severity'], 1))

        # Convert to sorted lists
        dates = sorted(daily_counts.keys())
        counts = [daily_counts[d] for d in dates]

        # Calculate moving averages
        ma_7 = AdvancedStatistics._moving_average(counts, window=7)
        ma_14 = AdvancedStatistics._moving_average(counts, window=14)

        # Exponential smoothing
        ema = AdvancedStatistics._exponential_smoothing(counts, alpha=0.3)

        # Rolling standard deviation
        rolling_std = AdvancedStatistics._rolling_std(counts, window=7)

        # Detect trend
        trend = AdvancedStatistics._detect_trend(counts)

        return {
            'available': True,
            'date_range': {
                'start': str(dates[0]),
                'end': str(dates[-1]),
                'days': len(dates)
            },
            'daily_counts': {
                'dates': [str(d) for d in dates],
                'counts': counts,
                'mean': round(np.mean(counts), 2),
                'std': round(np.std(counts), 2)
            },
            'moving_averages': {
                '7_day': [round(x, 2) for x in ma_7],
                '14_day': [round(x, 2) for x in ma_14]
            },
            'exponential_smoothing': {
                'values': [round(x, 2) for x in ema],
                'alpha': 0.3
            },
            'rolling_std': {
                '7_day': [round(x, 2) if x is not None else None for x in rolling_std]
            },
            'trend': trend
        }

    @staticmethod
    def _moving_average(data: List[float], window: int) -> List[float]:
        """Calculate moving average."""
        if len(data) < window:
            return data

        ma = []
        for i in range(len(data)):
            if i < window - 1:
                ma.append(np.mean(data[:i+1]))
            else:
                ma.append(np.mean(data[i-window+1:i+1]))
        return ma

    @staticmethod
    def _exponential_smoothing(data: List[float], alpha: float = 0.3) -> List[float]:
        """Calculate exponential moving average."""
        ema = [data[0]]
        for i in range(1, len(data)):
            ema.append(alpha * data[i] + (1 - alpha) * ema[i-1])
        return ema

    @staticmethod
    def _rolling_std(data: List[float], window: int) -> List[Optional[float]]:
        """Calculate rolling standard deviation."""
        rolling = []
        for i in range(len(data)):
            if i < window - 1:
                rolling.append(None)
            else:
                rolling.append(np.std(data[i-window+1:i+1]))
        return rolling

    @staticmethod
    def _detect_trend(data: List[float]) -> Dict[str, Any]:
        """Detect trend using linear regression."""
        if len(data) < 3:
            return {'direction': 'insufficient_data'}

        x = np.arange(len(data))
        y = np.array(data)

        # Linear regression
        slope, intercept = np.polyfit(x, y, 1)

        # Determine trend
        if abs(slope) < 0.1:
            direction = 'stable'
        elif slope > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'

        return {
            'direction': direction,
            'slope': round(slope, 4),
            'interpretation': f"Deviation count {'increasing' if slope > 0.1 else 'decreasing' if slope < -0.1 else 'stable'} by {abs(slope):.2f} per day"
        }

    @staticmethod
    def control_charts(deviations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Statistical Process Control (SPC) charts:
        - Shewhart chart (X-bar and R)
        - CUSUM (Cumulative Sum)
        - EWMA (Exponentially Weighted Moving Average)
        """
        logger.info("Generating control charts")

        # Extract daily counts (similar to time-series)
        timestamps = []
        for d in deviations:
            timestamp = d.get('detected_at') or d.get('timestamp')
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        dt = datetime.strptime(timestamp.split('.')[0], '%Y-%m-%d %H:%M:%S')
                        timestamps.append(dt)
                except Exception:
                    continue

        if len(timestamps) < 10:
            return {
                'available': False,
                'message': 'Insufficient data for control charts (need at least 10 time points)'
            }

        daily_counts = Counter(dt.date() for dt in timestamps)
        dates = sorted(daily_counts.keys())
        counts = [daily_counts[d] for d in dates]

        # Shewhart chart
        mean = np.mean(counts)
        std = np.std(counts)
        ucl = mean + 3 * std  # Upper Control Limit
        lcl = max(0, mean - 3 * std)  # Lower Control Limit

        out_of_control = [i for i, c in enumerate(counts) if c > ucl or c < lcl]

        # CUSUM
        cusum_pos, cusum_neg = AdvancedStatistics._calculate_cusum(counts, mean)

        # EWMA
        ewma_values = AdvancedStatistics._calculate_ewma(counts, lambda_param=0.2)
        ewma_std = np.std(counts) * np.sqrt(0.2 / (2 - 0.2))
        ewma_ucl = mean + 3 * ewma_std
        ewma_lcl = max(0, mean - 3 * ewma_std)

        return {
            'available': True,
            'shewhart': {
                'mean': round(mean, 2),
                'std': round(std, 2),
                'ucl': round(ucl, 2),
                'lcl': round(lcl, 2),
                'out_of_control_points': len(out_of_control),
                'out_of_control_indices': out_of_control,
                'status': 'In Control' if len(out_of_control) == 0 else f'Out of Control ({len(out_of_control)} points)'
            },
            'cusum': {
                'positive': [round(x, 2) for x in cusum_pos],
                'negative': [round(x, 2) for x in cusum_neg],
                'interpretation': 'CUSUM tracks cumulative deviations from mean'
            },
            'ewma': {
                'values': [round(x, 2) for x in ewma_values],
                'ucl': round(ewma_ucl, 2),
                'lcl': round(ewma_lcl, 2),
                'lambda': 0.2,
                'interpretation': 'EWMA smooths data and detects small shifts'
            }
        }

    @staticmethod
    def _calculate_cusum(data: List[float], target: float, k: float = 0.5) -> Tuple[List[float], List[float]]:
        """Calculate CUSUM (Cumulative Sum) control chart values."""
        cusum_pos = [0]
        cusum_neg = [0]

        for value in data:
            cusum_pos.append(max(0, cusum_pos[-1] + value - target - k))
            cusum_neg.append(max(0, cusum_neg[-1] - value + target - k))

        return cusum_pos[1:], cusum_neg[1:]

    @staticmethod
    def _calculate_ewma(data: List[float], lambda_param: float = 0.2) -> List[float]:
        """Calculate EWMA (Exponentially Weighted Moving Average) values."""
        ewma = [data[0]]
        for value in data[1:]:
            ewma.append(lambda_param * value + (1 - lambda_param) * ewma[-1])
        return ewma

    @staticmethod
    def change_point_detection(deviations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect change points (sudden shifts) in deviation rates using ruptures library.
        """
        if not RUPTURES_AVAILABLE:
            return {
                'available': False,
                'message': 'ruptures library not installed'
            }

        logger.info("Detecting change points")

        # Extract daily counts
        timestamps = []
        for d in deviations:
            timestamp = d.get('detected_at') or d.get('timestamp')
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        dt = datetime.strptime(timestamp.split('.')[0], '%Y-%m-%d %H:%M:%S')
                        timestamps.append(dt)
                except Exception:
                    continue

        if len(timestamps) < 20:
            return {
                'available': False,
                'message': 'Insufficient data for change-point detection (need at least 20 time points)'
            }

        daily_counts = Counter(dt.date() for dt in timestamps)
        dates = sorted(daily_counts.keys())
        counts = np.array([daily_counts[d] for d in dates])

        # Use PELT (Pruned Exact Linear Time) algorithm
        algo = rpt.Pelt(model="rbf").fit(counts.reshape(-1, 1))
        change_points = algo.predict(pen=3)  # penalty parameter

        # Remove the last point (end of signal)
        change_points = [cp for cp in change_points if cp < len(counts)]

        return {
            'available': True,
            'change_points': change_points,
            'change_dates': [str(dates[cp]) for cp in change_points if cp < len(dates)],
            'interpretation': f"Detected {len(change_points)} significant change points in deviation patterns",
            'segments': len(change_points) + 1
        }

    # ========================================================================
    # WORKFLOW LOG ANALYSIS METHODS (analyze logs, not deviations)
    # ========================================================================

    @staticmethod
    def time_series_analysis_logs(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Time-series analysis on workflow LOGS (not deviations).
        Shows trends in workflow execution: logs per day, case completion rates, etc.
        """
        logger.info(f"Starting time-series analysis on {len(logs)} workflow logs")

        # Extract timestamps from logs
        timestamps = []
        failed_parses = 0
        sample_timestamps = []

        for i, log in enumerate(logs):
            timestamp = log.get('timestamp')
            if i < 3:  # Log first 3 timestamps for debugging
                sample_timestamps.append(timestamp)

            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                            try:
                                dt = datetime.strptime(timestamp.split('.')[0], fmt)
                                timestamps.append(dt)
                                break
                            except ValueError:
                                continue
                        else:
                            failed_parses += 1
                except Exception as e:
                    failed_parses += 1
                    if i < 3:
                        logger.warning(f"Failed to parse timestamp: {timestamp}, error: {str(e)}")

        logger.info(f"Timestamp extraction: {len(timestamps)} successful, {failed_parses} failed")
        logger.info(f"Sample timestamps from logs: {sample_timestamps}")

        if len(timestamps) < 7:
            logger.warning(f"Only {len(timestamps)} timestamps found from {len(logs)} logs")
            return {
                'available': False,
                'message': f'Insufficient temporal data in logs (found {len(timestamps)} timestamps, need at least 7 days)'
            }

        # Create daily log counts
        daily_counts = Counter(dt.date() for dt in timestamps)
        dates = sorted(daily_counts.keys())
        counts = [daily_counts[d] for d in dates]

        # Calculate moving averages
        df = pd.DataFrame({'date': dates, 'count': counts})
        df['ma_7'] = df['count'].rolling(window=min(7, len(df)), min_periods=1).mean()
        df['ma_14'] = df['count'].rolling(window=min(14, len(df)), min_periods=1).mean()

        # Exponential smoothing
        df['ema'] = df['count'].ewm(alpha=0.3, adjust=False).mean()

        # Rolling standard deviation
        df['rolling_std'] = df['count'].rolling(window=min(7, len(df)), min_periods=1).std()

        # Trend detection (linear regression)
        x = np.arange(len(counts))
        try:
            # Check for valid data before polyfit
            if len(counts) < 2 or np.std(counts) == 0 or np.any(np.isnan(counts)) or np.any(np.isinf(counts)):
                # Insufficient or invalid data for trend analysis
                slope = 0.0
                intercept = np.mean(counts) if len(counts) > 0 else 0.0
            else:
                slope, intercept = np.polyfit(x, counts, 1)
        except (np.linalg.LinAlgError, ValueError, RuntimeWarning):
            # Fallback if polyfit fails
            slope = 0.0
            intercept = np.mean(counts) if len(counts) > 0 else 0.0

        trend_direction = "increasing" if slope > 0.1 else "decreasing" if slope < -0.1 else "stable"

        return {
            'available': True,
            'date_range': {
                'start': str(dates[0]),
                'end': str(dates[-1]),
                'days': len(dates)
            },
            'daily_log_counts': {
                'mean': round(float(np.mean(counts)), 2),
                'std': round(float(np.std(counts)), 2),
                'min': int(np.min(counts)),
                'max': int(np.max(counts))
            },
            'moving_averages': {
                '7_day': [round(float(x), 2) for x in df['ma_7'].tolist()[-10:]],  # Last 10 days
                '14_day': [round(float(x), 2) for x in df['ma_14'].tolist()[-10:]]
            },
            'exponential_smoothing': {
                'values': [round(float(x), 2) for x in df['ema'].tolist()[-10:]]
            },
            'volatility': {
                'rolling_std': [round(float(x), 2) if not np.isnan(x) else 0 for x in df['rolling_std'].tolist()[-10:]]
            },
            'trend': {
                'direction': trend_direction,
                'slope': round(float(slope), 3),
                'interpretation': f"Workflow activity {trend_direction} by {abs(slope):.2f} logs per day"
            }
        }

    @staticmethod
    def control_charts_logs(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Control charts on workflow LOGS (not deviations).
        Shows if workflow execution is stable or out of control.
        """
        logger.info(f"Generating control charts for {len(logs)} workflow logs")

        # Extract timestamps
        timestamps = []
        failed_parses = 0
        sample_timestamps = []

        for i, log in enumerate(logs):
            timestamp = log.get('timestamp')
            if i < 3:  # Log first 3 timestamps for debugging
                sample_timestamps.append(timestamp)

            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                            try:
                                dt = datetime.strptime(timestamp.split('.')[0], fmt)
                                timestamps.append(dt)
                                break
                            except ValueError:
                                continue
                        else:
                            failed_parses += 1
                except Exception as e:
                    failed_parses += 1

        logger.info(f"Control charts: {len(timestamps)} timestamps extracted, {failed_parses} failed")
        logger.info(f"Sample timestamps: {sample_timestamps}")

        if len(timestamps) < 10:
            logger.warning(f"Only {len(timestamps)} timestamps found from {len(logs)} logs")
            return {
                'available': False,
                'message': f'Insufficient data for control charts (found {len(timestamps)} timestamps, need at least 10 time points)'
            }

        daily_counts = Counter(dt.date() for dt in timestamps)
        dates = sorted(daily_counts.keys())
        counts = np.array([daily_counts[d] for d in dates])

        # Shewhart control chart (X-bar chart)
        mean = np.mean(counts)
        std = np.std(counts)
        ucl = mean + 3 * std  # Upper Control Limit
        lcl = max(0, mean - 3 * std)  # Lower Control Limit (can't be negative)

        out_of_control = np.sum((counts > ucl) | (counts < lcl))

        return {
            'available': True,
            'shewhart': {
                'mean': round(float(mean), 2),
                'std': round(float(std), 2),
                'ucl': round(float(ucl), 2),
                'lcl': round(float(lcl), 2),
                'out_of_control_points': int(out_of_control),
                'status': f"In Control" if out_of_control == 0 else f"Out of Control ({out_of_control} points)"
            },
            'interpretation': f"Workflow execution is {'stable' if out_of_control == 0 else 'unstable with ' + str(out_of_control) + ' anomalous days'}"
        }

    @staticmethod
    def change_point_detection_logs(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Change-point detection on workflow LOGS (not deviations).
        Detects when workflow patterns significantly changed.
        """
        if not RUPTURES_AVAILABLE:
            return {
                'available': False,
                'message': 'ruptures library not installed'
            }

        logger.info(f"Detecting change points in {len(logs)} workflow logs")

        # Extract timestamps
        timestamps = []
        failed_parses = 0
        sample_timestamps = []

        for i, log in enumerate(logs):
            timestamp = log.get('timestamp')
            if i < 3:  # Log first 3 timestamps for debugging
                sample_timestamps.append(timestamp)

            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                            try:
                                dt = datetime.strptime(timestamp.split('.')[0], fmt)
                                timestamps.append(dt)
                                break
                            except ValueError:
                                continue
                        else:
                            failed_parses += 1
                except Exception as e:
                    failed_parses += 1

        logger.info(f"Change-point detection: {len(timestamps)} timestamps extracted, {failed_parses} failed")
        logger.info(f"Sample timestamps: {sample_timestamps}")

        if len(timestamps) < 20:
            logger.warning(f"Only {len(timestamps)} timestamps found from {len(logs)} logs")
            return {
                'available': False,
                'message': f'Insufficient data for change-point detection (found {len(timestamps)} timestamps, need at least 20 time points)'
            }

        daily_counts = Counter(dt.date() for dt in timestamps)
        dates = sorted(daily_counts.keys())
        counts = np.array([daily_counts[d] for d in dates])

        # Check if data has sufficient variance and length for change-point detection
        if len(counts) < 10 or np.std(counts) == 0 or np.any(np.isnan(counts)) or np.any(np.isinf(counts)):
            logger.warning(f"Insufficient variance or length for change-point detection: len={len(counts)}, std={np.std(counts)}")
            return {
                'available': False,
                'message': f'Insufficient data variance for change-point detection (need at least 10 days with varying counts)'
            }

        try:
            # Use PELT algorithm with adaptive penalty based on data length
            penalty = max(1, len(counts) // 5)  # Adaptive penalty
            algo = rpt.Pelt(model="rbf").fit(counts.reshape(-1, 1))
            change_points = algo.predict(pen=penalty)

            # Remove the last point (ruptures includes end point)
            change_points = [cp for cp in change_points if cp < len(counts)]

            return {
                'available': True,
                'change_points': change_points,
                'change_dates': [str(dates[cp]) for cp in change_points if cp < len(dates)],
                'interpretation': f"Detected {len(change_points)} significant changes in workflow execution patterns",
                'segments': len(change_points) + 1
            }
        except Exception as e:
            logger.warning(f"Change-point detection failed: {e}")
            return {
                'available': False,
                'message': f'Change-point detection failed: {str(e)}'
            }
