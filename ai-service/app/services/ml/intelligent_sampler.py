"""
Intelligent Sampling Module

Selects representative deviations for LLM analysis using ML insights:
1. Include ALL anomalies (top priority)
2. Select representatives from each cluster (proportional)
3. Ensure coverage of all severity levels
4. Ensure temporal coverage
5. Ensure officer coverage

As described in ML_SYSTEM_EXPLAINED.md
"""

import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Set
from collections import Counter

logger = logging.getLogger(__name__)


class IntelligentSampler:
    """
    Intelligently samples deviations for LLM analysis while ensuring 100% pattern coverage.
    """

    def __init__(self, target_sample_size: int = 75):
        """
        Initialize intelligent sampler.

        Args:
            target_sample_size: Target number of samples for LLM (default 75)
        """
        self.target_sample_size = target_sample_size

    def sample(self,
               deviations: List[Dict[str, Any]],
               cluster_labels: np.ndarray,
               anomaly_labels: np.ndarray,
               anomaly_scores: np.ndarray,
               feature_matrix: np.ndarray,
               cluster_representatives: Dict[int, List[int]] = None) -> Tuple[List[int], Dict[str, Any]]:
        """
        Select representative samples using 5-part intelligent sampling strategy.

        Args:
            deviations: Original deviation data
            cluster_labels: Cluster assignments
            anomaly_labels: Anomaly labels (-1 = anomaly)
            anomaly_scores: Anomaly scores
            feature_matrix: Feature matrix
            cluster_representatives: Pre-computed cluster representatives (optional)

        Returns:
            Tuple of (selected_indices, sampling_report)
        """
        logger.info(f"Starting intelligent sampling from {len(deviations)} deviations")
        logger.info(f"Target sample size: {self.target_sample_size}")

        n_total = len(deviations)
        selected_indices = set()

        # ===================================================================
        # PART 1: Include ALL anomalies (top priority)
        # ===================================================================
        anomaly_indices = np.where(anomaly_labels == -1)[0]
        n_anomalies = len(anomaly_indices)

        selected_indices.update(anomaly_indices.tolist())
        logger.info(f"Part 1: Added ALL {n_anomalies} anomalies")

        # ===================================================================
        # PART 2: Cluster representatives (proportional allocation)
        # ===================================================================
        remaining_budget = self.target_sample_size - len(selected_indices)

        if remaining_budget > 0:
            cluster_indices = self._select_cluster_representatives(
                cluster_labels,
                anomaly_labels,
                feature_matrix,
                remaining_budget,
                cluster_representatives
            )
            selected_indices.update(cluster_indices)
            logger.info(f"Part 2: Added {len(cluster_indices)} cluster representatives")

        # ===================================================================
        # PART 3: Ensure severity coverage
        # ===================================================================
        severity_indices = self._ensure_severity_coverage(
            deviations,
            selected_indices
        )
        if severity_indices:
            selected_indices.update(severity_indices)
            logger.info(f"Part 3: Added {len(severity_indices)} for severity coverage")

        # ===================================================================
        # PART 4: Ensure temporal coverage
        # ===================================================================
        temporal_indices = self._ensure_temporal_coverage(
            deviations,
            selected_indices
        )
        if temporal_indices:
            selected_indices.update(temporal_indices)
            logger.info(f"Part 4: Added {len(temporal_indices)} for temporal coverage")

        # ===================================================================
        # PART 5: Ensure officer coverage
        # ===================================================================
        officer_indices = self._ensure_officer_coverage(
            deviations,
            selected_indices,
            max_add=5
        )
        if officer_indices:
            selected_indices.update(officer_indices)
            logger.info(f"Part 5: Added {len(officer_indices)} for officer coverage")

        # Convert to sorted list
        final_indices = sorted(list(selected_indices))

        # Generate sampling report
        report = self._generate_report(
            deviations,
            final_indices,
            cluster_labels,
            anomaly_labels,
            n_anomalies
        )

        logger.info(f"Intelligent sampling complete: {len(final_indices)}/{n_total} samples selected ({report['compression_ratio']:.1f}x compression)")

        return final_indices, report

    def _select_cluster_representatives(self,
                                       cluster_labels: np.ndarray,
                                       anomaly_labels: np.ndarray,
                                       feature_matrix: np.ndarray,
                                       budget: int,
                                       precomputed_reps: Dict[int, List[int]] = None) -> Set[int]:
        """
        Select representatives from each cluster proportionally.

        Args:
            cluster_labels: Cluster assignments
            anomaly_labels: Anomaly labels
            feature_matrix: Feature matrix
            budget: Number of samples to select
            precomputed_reps: Pre-computed representatives (optional)

        Returns:
            Set of selected indices
        """
        # Get unique clusters (exclude -1 if it exists, and exclude anomalies)
        unique_clusters = set(cluster_labels) - {-1}

        if len(unique_clusters) == 0:
            logger.warning("No clusters found")
            return set()

        # Calculate cluster sizes (excluding anomalies)
        normal_mask = anomaly_labels != -1
        cluster_sizes = {}

        for cluster_id in unique_clusters:
            cluster_mask = (cluster_labels == cluster_id) & normal_mask
            cluster_sizes[cluster_id] = np.sum(cluster_mask)

        total_normal = sum(cluster_sizes.values())

        if total_normal == 0:
            return set()

        # Allocate budget proportionally
        allocation = {}
        for cluster_id, size in cluster_sizes.items():
            proportion = size / total_normal
            n_samples = max(1, int(np.round(proportion * budget)))  # At least 1 per cluster
            allocation[cluster_id] = min(n_samples, size)

        # Adjust if over budget
        total_allocated = sum(allocation.values())
        if total_allocated > budget:
            # Reduce largest clusters
            sorted_clusters = sorted(allocation.items(), key=lambda x: x[1], reverse=True)
            reduction_needed = total_allocated - budget
            for cluster_id, count in sorted_clusters:
                if reduction_needed <= 0:
                    break
                reduction = min(reduction_needed, count - 1)  # Keep at least 1
                allocation[cluster_id] -= reduction
                reduction_needed -= reduction

        # Select representatives
        selected = set()

        for cluster_id, n_samples in allocation.items():
            cluster_mask = (cluster_labels == cluster_id) & normal_mask
            cluster_indices = np.where(cluster_mask)[0]

            if len(cluster_indices) == 0:
                continue

            if precomputed_reps and cluster_id in precomputed_reps:
                # Use pre-computed representatives
                reps = precomputed_reps[cluster_id][:n_samples]
            else:
                # Select based on distance to centroid
                cluster_features = feature_matrix[cluster_indices]
                centroid = np.mean(cluster_features, axis=0)
                distances = np.linalg.norm(cluster_features - centroid, axis=1)

                # Mix: closest + farthest for diversity
                n_close = max(1, n_samples // 2)
                n_far = n_samples - n_close

                closest_local = np.argsort(distances)[:n_close]
                farthest_local = np.argsort(distances)[-n_far:] if n_far > 0 else []

                selected_local = np.unique(np.concatenate([closest_local, farthest_local]))
                reps = cluster_indices[selected_local].tolist()

            selected.update(reps[:n_samples])

        return selected

    def _ensure_severity_coverage(self,
                                  deviations: List[Dict[str, Any]],
                                  selected_indices: Set[int]) -> Set[int]:
        """
        Ensure all severity levels are represented.

        Args:
            deviations: Original deviations
            selected_indices: Already selected indices

        Returns:
            Additional indices to add
        """
        all_severities = {'critical', 'high', 'medium', 'low'}
        selected_severities = set(deviations[i].get('severity', 'unknown').lower()
                                  for i in selected_indices)

        missing_severities = all_severities - selected_severities
        additional = set()

        for severity in missing_severities:
            # Find a deviation with this severity
            for i, dev in enumerate(deviations):
                if i not in selected_indices and dev.get('severity', '').lower() == severity:
                    additional.add(i)
                    break

        return additional

    def _ensure_temporal_coverage(self,
                                  deviations: List[Dict[str, Any]],
                                  selected_indices: Set[int]) -> Set[int]:
        """
        Ensure all time periods are represented.

        Args:
            deviations: Original deviations
            selected_indices: Already selected indices

        Returns:
            Additional indices to add
        """
        from datetime import datetime

        time_periods = {
            'morning': (6, 12),
            'afternoon': (12, 18),
            'evening': (18, 24),
            'night': (0, 6)
        }

        covered_periods = set()

        # Check which periods are already covered
        for i in selected_indices:
            timestamp = deviations[i].get('detected_at') or deviations[i].get('created_at')
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp.split('.')[0].replace(' ', 'T'))
                    else:
                        dt = timestamp

                    hour = dt.hour
                    for period, (start, end) in time_periods.items():
                        if start <= hour < end:
                            covered_periods.add(period)
                            break
                except:
                    pass

        missing_periods = set(time_periods.keys()) - covered_periods
        additional = set()

        for period in missing_periods:
            start, end = time_periods[period]

            # Find a deviation in this period
            for i, dev in enumerate(deviations):
                if i in selected_indices:
                    continue

                timestamp = dev.get('detected_at') or dev.get('created_at')
                if timestamp:
                    try:
                        if isinstance(timestamp, str):
                            dt = datetime.fromisoformat(timestamp.split('.')[0].replace(' ', 'T'))
                        else:
                            dt = timestamp

                        if start <= dt.hour < end:
                            additional.add(i)
                            break
                    except:
                        pass

        return additional

    def _ensure_officer_coverage(self,
                                 deviations: List[Dict[str, Any]],
                                 selected_indices: Set[int],
                                 max_add: int = 5) -> Set[int]:
        """
        Ensure diverse officer representation.

        Args:
            deviations: Original deviations
            selected_indices: Already selected indices
            max_add: Maximum officers to add

        Returns:
            Additional indices to add
        """
        # Get all officers
        all_officers = set(d.get('officer_id') for d in deviations)

        # Get covered officers
        covered_officers = set(deviations[i].get('officer_id') for i in selected_indices)

        # Find uncovered officers
        uncovered_officers = all_officers - covered_officers
        additional = set()

        count = 0
        for officer in uncovered_officers:
            if count >= max_add:
                break

            # Find a deviation from this officer
            for i, dev in enumerate(deviations):
                if i not in selected_indices and dev.get('officer_id') == officer:
                    additional.add(i)
                    count += 1
                    break

        return additional

    def _generate_report(self,
                        deviations: List[Dict[str, Any]],
                        selected_indices: List[int],
                        cluster_labels: np.ndarray,
                        anomaly_labels: np.ndarray,
                        n_anomalies: int) -> Dict[str, Any]:
        """Generate sampling report with statistics."""
        n_total = len(deviations)
        n_selected = len(selected_indices)

        # Count composition
        n_anomalies_selected = sum(1 for i in selected_indices if anomaly_labels[i] == -1)
        n_cluster_reps = n_selected - n_anomalies_selected

        # Check coverage
        selected_severities = set(deviations[i].get('severity', 'unknown').lower()
                                 for i in selected_indices)
        selected_types = set(deviations[i].get('deviation_type') for i in selected_indices)
        selected_officers = set(deviations[i].get('officer_id') for i in selected_indices)

        return {
            'total_deviations': n_total,
            'selected_count': n_selected,
            'compression_ratio': n_total / n_selected if n_selected > 0 else 0,
            'composition': {
                'anomalies': n_anomalies_selected,
                'cluster_representatives': n_cluster_reps
            },
            'coverage': {
                'severity_levels': len(selected_severities),
                'deviation_types': len(selected_types),
                'officers': len(selected_officers)
            }
        }
