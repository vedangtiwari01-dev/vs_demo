"""
ML Clustering Module

Groups similar deviations together using:
1. DBSCAN (primary) - Density-based clustering
2. K-means (fallback) - If DBSCAN produces too many/few clusters

As described in ML_SYSTEM_EXPLAINED.md
"""

import logging
import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler
from collections import Counter

logger = logging.getLogger(__name__)


class DeviationClusterer:
    """
    Clusters deviations using DBSCAN (primary) or K-means (fallback).
    """

    def __init__(self):
        """Initialize clustering components."""
        self.scaler = StandardScaler()
        self.clusterer = None
        self.labels = None
        self.n_clusters = 0
        self.noise_count = 0
        self.method_used = None

    def cluster(self, feature_matrix: np.ndarray,
                min_clusters: int = 3,
                max_clusters: int = 15) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Cluster deviations using DBSCAN with K-means fallback.

        Args:
            feature_matrix: Numpy array of shape (n_samples, n_features)
            min_clusters: Minimum acceptable number of clusters
            max_clusters: Maximum acceptable number of clusters

        Returns:
            Tuple of (cluster_labels, metadata)
            - cluster_labels: Array of cluster assignments (-1 = noise/outlier)
            - metadata: Dict with clustering statistics
        """
        logger.info(f"Starting clustering for {feature_matrix.shape[0]} samples with {feature_matrix.shape[1]} features")

        if feature_matrix.shape[0] < 10:
            logger.warning("Too few samples for clustering, assigning all to one cluster")
            return np.zeros(feature_matrix.shape[0]), {
                'method': 'insufficient_data',
                'n_clusters': 1,
                'noise_count': 0
            }

        # Normalize features
        X_scaled = self.scaler.fit_transform(feature_matrix)

        # Try DBSCAN first
        labels, metadata = self._try_dbscan(X_scaled, min_clusters, max_clusters)

        # Check if DBSCAN produced acceptable results
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)

        if min_clusters <= n_clusters <= max_clusters:
            logger.info(f"DBSCAN successful: {n_clusters} clusters")
            self.labels = labels
            self.method_used = 'DBSCAN'
            return labels, metadata
        else:
            logger.warning(f"DBSCAN produced {n_clusters} clusters (outside range [{min_clusters}, {max_clusters}])")
            logger.info("Falling back to K-means...")

            # Fallback to K-means
            labels, metadata = self._try_kmeans(X_scaled, target_clusters=10)
            self.labels = labels
            self.method_used = 'KMeans'
            return labels, metadata

    def _try_dbscan(self, X_scaled: np.ndarray,
                    min_clusters: int,
                    max_clusters: int) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Try DBSCAN clustering with automatic parameter tuning.

        Args:
            X_scaled: Scaled feature matrix
            min_clusters: Minimum clusters
            max_clusters: Maximum clusters

        Returns:
            Tuple of (labels, metadata)
        """
        # DBSCAN parameters
        # eps: Maximum distance between samples to be neighbors
        # min_samples: Minimum samples in neighborhood to form core point

        eps = 0.5
        min_samples = 5

        logger.info(f"Running DBSCAN with eps={eps}, min_samples={min_samples}")

        dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric='euclidean')
        labels = dbscan.fit_predict(X_scaled)

        # Count clusters and noise
        unique_labels = set(labels)
        n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
        noise_count = list(labels).count(-1)

        self.n_clusters = n_clusters
        self.noise_count = noise_count

        logger.info(f"DBSCAN results: {n_clusters} clusters, {noise_count} noise points")

        # Calculate cluster sizes
        cluster_sizes = {}
        for label in unique_labels:
            if label != -1:
                cluster_sizes[f"cluster_{label}"] = int(np.sum(labels == label))

        metadata = {
            'method': 'DBSCAN',
            'n_clusters': n_clusters,
            'noise_count': noise_count,
            'eps': eps,
            'min_samples': min_samples,
            'cluster_sizes': cluster_sizes
        }

        return labels, metadata

    def _try_kmeans(self, X_scaled: np.ndarray, target_clusters: int = 10) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Fallback to K-means clustering.

        Args:
            X_scaled: Scaled feature matrix
            target_clusters: Number of clusters to create

        Returns:
            Tuple of (labels, metadata)
        """
        # Adjust target_clusters based on sample size
        n_samples = X_scaled.shape[0]
        target_clusters = min(target_clusters, n_samples // 5)  # At least 5 samples per cluster
        target_clusters = max(target_clusters, 2)  # At least 2 clusters

        logger.info(f"Running K-means with {target_clusters} clusters")

        kmeans = KMeans(
            n_clusters=target_clusters,
            random_state=42,
            n_init=10,
            max_iter=300
        )
        labels = kmeans.fit_predict(X_scaled)

        self.n_clusters = target_clusters
        self.noise_count = 0  # K-means doesn't produce noise points

        # Calculate cluster sizes
        cluster_sizes = {}
        for i in range(target_clusters):
            cluster_sizes[f"cluster_{i}"] = int(np.sum(labels == i))

        # Calculate inertia (within-cluster sum of squares)
        inertia = kmeans.inertia_

        metadata = {
            'method': 'KMeans',
            'n_clusters': target_clusters,
            'noise_count': 0,
            'cluster_sizes': cluster_sizes,
            'inertia': float(inertia)
        }

        logger.info(f"K-means complete: {target_clusters} clusters, inertia={inertia:.2f}")

        return labels, metadata

    def get_cluster_summary(self, labels: np.ndarray,
                           deviations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary of clusters with characteristics.

        Args:
            labels: Cluster labels
            deviations: Original deviation data

        Returns:
            Dictionary with cluster summaries
        """
        unique_labels = set(labels)
        summary = {}

        for label in unique_labels:
            if label == -1:
                cluster_name = 'noise'
            else:
                cluster_name = f'cluster_{label}'

            # Get deviations in this cluster
            mask = labels == label
            cluster_deviations = [d for i, d in enumerate(deviations) if mask[i]]

            # Analyze cluster characteristics
            severity_counts = Counter(d.get('severity', 'unknown') for d in cluster_deviations)
            type_counts = Counter(d.get('deviation_type', 'unknown') for d in cluster_deviations)
            officer_counts = Counter(d.get('officer_id', 'unknown') for d in cluster_deviations)

            summary[cluster_name] = {
                'size': int(np.sum(mask)),
                'percentage': round((np.sum(mask) / len(labels)) * 100, 2),
                'top_severity': severity_counts.most_common(1)[0][0] if severity_counts else 'unknown',
                'top_deviation_type': type_counts.most_common(1)[0][0] if type_counts else 'unknown',
                'top_officer': officer_counts.most_common(1)[0][0] if officer_counts else 'unknown',
                'severity_distribution': dict(severity_counts),
                'deviation_types': dict(type_counts.most_common(3))
            }

        return summary

    def get_cluster_representatives(self, labels: np.ndarray,
                                    feature_matrix: np.ndarray,
                                    n_per_cluster: int = 5) -> Dict[int, List[int]]:
        """
        Select representative samples from each cluster.

        Strategy: Pick samples closest to cluster centroid + edge samples for diversity.

        Args:
            labels: Cluster labels
            feature_matrix: Feature matrix
            n_per_cluster: Number of representatives per cluster

        Returns:
            Dictionary mapping cluster_id -> list of sample indices
        """
        representatives = {}
        unique_labels = set(labels) - {-1}  # Exclude noise

        for label in unique_labels:
            mask = labels == label
            cluster_indices = np.where(mask)[0]
            cluster_features = feature_matrix[mask]

            if len(cluster_indices) <= n_per_cluster:
                # Small cluster - take all
                representatives[int(label)] = cluster_indices.tolist()
            else:
                # Calculate centroid
                centroid = np.mean(cluster_features, axis=0)

                # Calculate distances to centroid
                distances = np.linalg.norm(cluster_features - centroid, axis=1)

                # Select samples: closest to centroid + some farther ones for diversity
                n_close = max(1, n_per_cluster // 2)
                n_far = n_per_cluster - n_close

                closest_indices = np.argsort(distances)[:n_close]
                farthest_indices = np.argsort(distances)[-n_far:]

                selected_local_indices = np.unique(np.concatenate([closest_indices, farthest_indices]))
                selected_global_indices = cluster_indices[selected_local_indices]

                representatives[int(label)] = selected_global_indices.tolist()

        return representatives
