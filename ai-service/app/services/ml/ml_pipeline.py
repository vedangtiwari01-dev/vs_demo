"""
ML Pipeline Orchestrator

Coordinates the complete ML analysis pipeline:
1. Feature Engineering
2. Clustering
3. Anomaly Detection
4. Intelligent Sampling

This is Layer 4 in the deviation analysis flow (between statistics and LLM).
"""

import logging
import numpy as np
from typing import List, Dict, Any, Tuple

from .feature_engineer import FeatureEngineer
from .clustering import DeviationClusterer
from .anomaly_detector import AnomalyDetector
from .intelligent_sampler import IntelligentSampler

logger = logging.getLogger(__name__)


class MLPipeline:
    """
    Orchestrates the complete ML analysis pipeline for deviation analysis.
    """

    def __init__(self, target_sample_size: int = 75, contamination: float = 0.1):
        """
        Initialize ML pipeline.

        Args:
            target_sample_size: Target number of samples for LLM analysis
            contamination: Expected proportion of anomalies (default 10%)
        """
        self.target_sample_size = target_sample_size
        self.contamination = contamination

        self.feature_engineer = FeatureEngineer()
        self.clusterer = DeviationClusterer()
        self.anomaly_detector = AnomalyDetector(contamination=contamination)
        self.sampler = IntelligentSampler(target_sample_size=target_sample_size)

    def analyze(self, deviations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run complete ML analysis pipeline.

        Args:
            deviations: List of cleaned deviation dictionaries

        Returns:
            Dictionary containing:
            - selected_indices: Indices of sampled deviations
            - selected_deviations: Actual sampled deviation data
            - ml_metadata: Complete ML analysis results
        """
        logger.info(f"=== ML PIPELINE STARTED for {len(deviations)} deviations ===")

        if len(deviations) < 10:
            logger.warning("Too few deviations for ML analysis, returning all")
            return {
                'selected_indices': list(range(len(deviations))),
                'selected_deviations': deviations,
                'ml_metadata': {
                    'ml_applied': False,
                    'reason': 'insufficient_data',
                    'minimum_required': 10
                }
            }

        # ===================================================================
        # STEP 1: Feature Engineering
        # ===================================================================
        logger.info("Step 1: Feature Engineering...")
        feature_matrix, feature_metadata = self.feature_engineer.fit_transform(deviations)

        if feature_matrix.shape[1] == 0:
            logger.error("Feature engineering failed, returning all deviations")
            return {
                'selected_indices': list(range(len(deviations))),
                'selected_deviations': deviations,
                'ml_metadata': {
                    'ml_applied': False,
                    'reason': 'feature_engineering_failed'
                }
            }

        logger.info(f"  ✓ Generated {feature_matrix.shape[1]} features")

        # ===================================================================
        # STEP 2: Clustering
        # ===================================================================
        logger.info("Step 2: Clustering...")
        cluster_labels, cluster_metadata = self.clusterer.cluster(feature_matrix)
        cluster_summary = self.clusterer.get_cluster_summary(cluster_labels, deviations)

        logger.info(f"  ✓ Created {cluster_metadata['n_clusters']} clusters using {cluster_metadata['method']}")

        # Get cluster representatives
        cluster_representatives = self.clusterer.get_cluster_representatives(
            cluster_labels,
            feature_matrix,
            n_per_cluster=5
        )

        # ===================================================================
        # STEP 3: Anomaly Detection
        # ===================================================================
        logger.info("Step 3: Anomaly Detection...")
        anomaly_labels, anomaly_scores, anomaly_metadata = self.anomaly_detector.detect_anomalies(feature_matrix)
        anomaly_analysis = self.anomaly_detector.analyze_anomalies(
            anomaly_labels,
            anomaly_scores,
            deviations
        )

        logger.info(f"  ✓ Detected {anomaly_metadata['n_anomalies']} anomalies ({anomaly_metadata['anomaly_percentage']:.1f}%)")

        # ===================================================================
        # STEP 4: Intelligent Sampling
        # ===================================================================
        logger.info("Step 4: Intelligent Sampling...")
        selected_indices, sampling_report = self.sampler.sample(
            deviations,
            cluster_labels,
            anomaly_labels,
            anomaly_scores,
            feature_matrix,
            cluster_representatives
        )

        logger.info(f"  ✓ Selected {len(selected_indices)} representatives ({sampling_report['compression_ratio']:.1f}x compression)")

        # ===================================================================
        # Prepare output
        # ===================================================================

        # Extract selected deviations
        selected_deviations = [deviations[i] for i in selected_indices]

        # Add ML labels to selected deviations
        for i, dev_idx in enumerate(selected_indices):
            selected_deviations[i]['ml_labels'] = {
                'cluster': int(cluster_labels[dev_idx]) if cluster_labels[dev_idx] != -1 else 'noise',
                'is_anomaly': bool(anomaly_labels[dev_idx] == -1),
                'anomaly_score': float(anomaly_scores[dev_idx])
            }

        # Compile metadata
        ml_metadata = {
            'ml_applied': True,
            'pipeline_steps': ['feature_engineering', 'clustering', 'anomaly_detection', 'intelligent_sampling'],

            # Feature engineering
            'features': feature_metadata,

            # Clustering
            'clustering': {
                **cluster_metadata,
                'cluster_summary': cluster_summary
            },

            # Anomaly detection
            'anomaly_detection': {
                **anomaly_metadata,
                'anomaly_analysis': anomaly_analysis
            },

            # Sampling
            'sampling': sampling_report
        }

        logger.info("=== ML PIPELINE COMPLETED ===")

        return {
            'selected_indices': selected_indices,
            'selected_deviations': selected_deviations,
            'ml_metadata': ml_metadata
        }

    def get_ml_context_for_llm(self, ml_metadata: Dict[str, Any]) -> str:
        """
        Format ML analysis results as context for LLM prompt.

        Args:
            ml_metadata: ML metadata from analyze()

        Returns:
            Formatted string for LLM prompt
        """
        if not ml_metadata.get('ml_applied'):
            return ""

        clustering = ml_metadata.get('clustering', {})
        anomaly = ml_metadata.get('anomaly_detection', {})
        sampling = ml_metadata.get('sampling', {})

        context = f"""
**ML ANALYSIS CONTEXT:**

🔬 **Clustering Analysis:**
- Method: {clustering.get('method', 'N/A')}
- Clusters Found: {clustering.get('n_clusters', 0)}
- Noise Points: {clustering.get('noise_count', 0)}

📊 **Cluster Summary:**
"""

        # Add cluster summaries
        cluster_summary = clustering.get('cluster_summary', {})
        for cluster_name, info in cluster_summary.items():
            if cluster_name != 'noise':
                context += f"""
  {cluster_name.upper()}: {info['size']} deviations ({info['percentage']}%)
    - Top Type: {info['top_deviation_type']}
    - Top Severity: {info['top_severity']}
"""

        context += f"""
🚨 **Anomaly Detection:**
- Anomalies Detected: {anomaly.get('n_anomalies', 0)} ({anomaly.get('anomaly_percentage', 0):.1f}%)
- Method: {anomaly.get('method', 'N/A')}
"""

        anomaly_analysis = anomaly.get('anomaly_analysis', {})
        if anomaly_analysis.get('count', 0) > 0:
            context += f"""
  Most Anomalous Case:
    - Case: {anomaly_analysis.get('most_anomalous', {}).get('case_id', 'N/A')}
    - Type: {anomaly_analysis.get('most_anomalous', {}).get('deviation_type', 'N/A')}
    - Score: {anomaly_analysis.get('most_anomalous', {}).get('score', 0):.3f}
"""

        context += f"""
🎯 **Intelligent Sampling:**
- Total Deviations: {sampling.get('total_deviations', 0)}
- Selected for Analysis: {sampling.get('selected_count', 0)}
- Compression: {sampling.get('compression_ratio', 0):.1f}x
- Composition:
  • ALL {sampling.get('composition', {}).get('anomalies', 0)} anomalies (100% included)
  • {sampling.get('composition', {}).get('cluster_representatives', 0)} cluster representatives

**IMPORTANT:** You are analyzing {sampling.get('selected_count', 0)} carefully selected representatives that cover ALL patterns across {sampling.get('total_deviations', 0)} total deviations.
- ALL anomalies are included (none missed)
- Representatives selected from each cluster
- Diverse coverage ensured (severity, time, officers)

Use the cluster labels and anomaly flags to understand which deviations are unusual vs. part of common patterns.
"""

        return context
