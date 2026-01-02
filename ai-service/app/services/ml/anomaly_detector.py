"""
ML Anomaly Detection Module

Detects unusual/outlier deviations using Isolation Forest.

As described in ML_SYSTEM_EXPLAINED.md:
- Outliers are deviations that are different from the majority
- Easy to isolate (require fewer splits in decision trees)
- Score: -1 (outlier) to +1 (normal)

These anomalies are ALWAYS included in the final sample for LLM analysis.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detects anomalies/outliers in deviations using Isolation Forest.
    """

    def __init__(self, contamination: float = 0.1):
        """
        Initialize anomaly detector.

        Args:
            contamination: Expected proportion of outliers (default 10%)
        """
        self.contamination = contamination
        self.model = None
        self.anomaly_scores = None

    def detect_anomalies(self, feature_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Detect anomalies in the feature matrix.

        Args:
            feature_matrix: Numpy array of shape (n_samples, n_features)

        Returns:
            Tuple of (anomaly_labels, anomaly_scores, metadata)
            - anomaly_labels: 1 for normal, -1 for anomaly
            - anomaly_scores: Anomaly scores (more negative = more anomalous)
            - metadata: Detection statistics
        """
        logger.info(f"Starting anomaly detection for {feature_matrix.shape[0]} samples")

        if feature_matrix.shape[0] < 10:
            logger.warning("Too few samples for anomaly detection")
            return (
                np.ones(feature_matrix.shape[0]),  # All normal
                np.zeros(feature_matrix.shape[0]),  # Zero scores
                {'method': 'insufficient_data', 'anomalies': 0}
            )

        # Adjust contamination based on sample size
        adjusted_contamination = min(self.contamination, 0.2)  # Cap at 20%

        logger.info(f"Running Isolation Forest with contamination={adjusted_contamination}")

        # Initialize and fit Isolation Forest
        self.model = IsolationForest(
            contamination=adjusted_contamination,
            random_state=42,
            n_estimators=100,
            max_samples='auto',
            max_features=1.0
        )

        # Predict: 1 = normal, -1 = anomaly
        anomaly_labels = self.model.fit_predict(feature_matrix)

        # Get anomaly scores (more negative = more anomalous)
        # decision_function returns negative scores for outliers
        anomaly_scores = self.model.decision_function(feature_matrix)
        self.anomaly_scores = anomaly_scores

        # Count anomalies
        n_anomalies = np.sum(anomaly_labels == -1)
        anomaly_percentage = (n_anomalies / len(anomaly_labels)) * 100

        logger.info(f"Anomaly detection complete: {n_anomalies} anomalies ({anomaly_percentage:.1f}%)")

        # Find threshold score
        anomaly_threshold = np.min(anomaly_scores[anomaly_labels == 1]) if n_anomalies < len(anomaly_labels) else 0

        metadata = {
            'method': 'IsolationForest',
            'contamination': adjusted_contamination,
            'n_anomalies': int(n_anomalies),
            'anomaly_percentage': round(anomaly_percentage, 2),
            'anomaly_threshold': float(anomaly_threshold),
            'score_range': {
                'min': float(np.min(anomaly_scores)),
                'max': float(np.max(anomaly_scores)),
                'mean': float(np.mean(anomaly_scores)),
                'std': float(np.std(anomaly_scores))
            }
        }

        return anomaly_labels, anomaly_scores, metadata

    def get_top_anomalies(self, anomaly_scores: np.ndarray,
                          anomaly_labels: np.ndarray,
                          n: int = None) -> np.ndarray:
        """
        Get indices of top N anomalies (most anomalous).

        Args:
            anomaly_scores: Anomaly scores from detect_anomalies
            anomaly_labels: Anomaly labels (-1 = anomaly)
            n: Number of top anomalies to return (None = all anomalies)

        Returns:
            Array of indices of top anomalies
        """
        # Get indices of all anomalies
        anomaly_indices = np.where(anomaly_labels == -1)[0]

        if len(anomaly_indices) == 0:
            logger.warning("No anomalies detected")
            return np.array([])

        # Get scores of anomalies (more negative = more anomalous)
        anomaly_scores_subset = anomaly_scores[anomaly_indices]

        # Sort by score (most negative first)
        sorted_indices = np.argsort(anomaly_scores_subset)

        # Take top N
        if n is not None and n < len(sorted_indices):
            sorted_indices = sorted_indices[:n]

        # Map back to original indices
        top_anomaly_indices = anomaly_indices[sorted_indices]

        return top_anomaly_indices

    def analyze_anomalies(self, anomaly_labels: np.ndarray,
                         anomaly_scores: np.ndarray,
                         deviations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze characteristics of detected anomalies.

        Args:
            anomaly_labels: Anomaly labels
            anomaly_scores: Anomaly scores
            deviations: Original deviation data

        Returns:
            Dictionary with anomaly analysis
        """
        anomaly_mask = anomaly_labels == -1
        anomaly_indices = np.where(anomaly_mask)[0]

        if len(anomaly_indices) == 0:
            return {
                'count': 0,
                'percentage': 0.0,
                'characteristics': {}
            }

        # Get anomalous deviations
        anomalous_deviations = [deviations[i] for i in anomaly_indices]

        # Analyze characteristics
        from collections import Counter

        severity_dist = Counter(d.get('severity', 'unknown') for d in anomalous_deviations)
        type_dist = Counter(d.get('deviation_type', 'unknown') for d in anomalous_deviations)
        officer_dist = Counter(d.get('officer_id', 'unknown') for d in anomalous_deviations)

        # Get most anomalous sample
        most_anomalous_idx = anomaly_indices[np.argmin(anomaly_scores[anomaly_mask])]
        most_anomalous = deviations[most_anomalous_idx]

        analysis = {
            'count': len(anomaly_indices),
            'percentage': round((len(anomaly_indices) / len(deviations)) * 100, 2),
            'severity_distribution': dict(severity_dist),
            'top_deviation_types': dict(type_dist.most_common(5)),
            'top_officers': dict(officer_dist.most_common(5)),
            'most_anomalous': {
                'index': int(most_anomalous_idx),
                'score': float(anomaly_scores[most_anomalous_idx]),
                'case_id': most_anomalous.get('case_id'),
                'officer_id': most_anomalous.get('officer_id'),
                'deviation_type': most_anomalous.get('deviation_type'),
                'severity': most_anomalous.get('severity'),
                'description': most_anomalous.get('description', '')[:100]
            }
        }

        return analysis

    def get_anomaly_indices(self, anomaly_labels: np.ndarray) -> np.ndarray:
        """
        Get indices of all anomalies.

        Args:
            anomaly_labels: Anomaly labels (-1 = anomaly, 1 = normal)

        Returns:
            Array of anomaly indices
        """
        return np.where(anomaly_labels == -1)[0]
