"""
ML Feature Engineering Module

Converts deviation data into numerical features for ML algorithms:
1. TF-IDF for text descriptions
2. One-hot encoding for categorical fields
3. Severity scoring (numerical)
4. Temporal features (hour, day of week)
5. Officer features (top 20 officers)

As described in ML_SYSTEM_EXPLAINED.md
"""

import logging
import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from datetime import datetime
from collections import Counter

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Converts deviation data into numerical feature vectors for ML.
    """

    def __init__(self):
        """Initialize feature engineering components."""
        self.tfidf = None
        self.severity_map = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        self.top_officers = None
        self.deviation_types = None
        self.feature_names = []

    def fit_transform(self, deviations: List[Dict[str, Any]]) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Fit the feature engineering pipeline and transform deviations to feature vectors.

        Args:
            deviations: List of deviation dictionaries

        Returns:
            Tuple of (feature_matrix, metadata)
            - feature_matrix: numpy array of shape (n_deviations, n_features)
            - metadata: dict containing feature names, transformers, etc.
        """
        logger.info(f"Starting feature engineering for {len(deviations)} deviations")

        if len(deviations) == 0:
            return np.array([]), {}

        # Extract text descriptions for TF-IDF
        descriptions = [d.get('description', '') for d in deviations]

        # 1. TEXT FEATURES (TF-IDF)
        logger.info("Generating TF-IDF features from descriptions...")
        tfidf_features, tfidf_feature_names = self._create_tfidf_features(descriptions)

        # 2. CATEGORICAL FEATURES (One-hot encoding)
        logger.info("Encoding categorical features...")
        categorical_features, categorical_names = self._create_categorical_features(deviations)

        # 3. NUMERICAL FEATURES (Severity, temporal, officer)
        logger.info("Creating numerical features...")
        numerical_features, numerical_names = self._create_numerical_features(deviations)

        # Combine all features
        all_features = []
        self.feature_names = []

        if tfidf_features.shape[1] > 0:
            all_features.append(tfidf_features)
            self.feature_names.extend(tfidf_feature_names)

        if categorical_features.shape[1] > 0:
            all_features.append(categorical_features)
            self.feature_names.extend(categorical_names)

        if numerical_features.shape[1] > 0:
            all_features.append(numerical_features)
            self.feature_names.extend(numerical_names)

        # Stack horizontally
        feature_matrix = np.hstack(all_features) if all_features else np.array([])

        logger.info(f"Feature engineering complete: {feature_matrix.shape[0]} samples, {feature_matrix.shape[1]} features")

        metadata = {
            'n_features': feature_matrix.shape[1],
            'feature_names': self.feature_names,
            'tfidf_features': tfidf_features.shape[1],
            'categorical_features': categorical_features.shape[1],
            'numerical_features': numerical_features.shape[1],
            'top_officers': self.top_officers,
            'deviation_types': self.deviation_types
        }

        return feature_matrix, metadata

    def _create_tfidf_features(self, descriptions: List[str]) -> Tuple[np.ndarray, List[str]]:
        """
        Create TF-IDF features from text descriptions.

        Args:
            descriptions: List of text descriptions

        Returns:
            Tuple of (tfidf_matrix, feature_names)
        """
        # Initialize TF-IDF with reasonable parameters
        self.tfidf = TfidfVectorizer(
            max_features=100,  # Top 100 words
            min_df=2,  # Must appear in at least 2 documents
            max_df=0.8,  # Ignore words in >80% of documents
            stop_words='english',
            ngram_range=(1, 2)  # Unigrams and bigrams
        )

        try:
            tfidf_matrix = self.tfidf.fit_transform(descriptions).toarray()
            feature_names = [f"tfidf_{name}" for name in self.tfidf.get_feature_names_out()]
            logger.info(f"Generated {len(feature_names)} TF-IDF features")
            return tfidf_matrix, feature_names

        except Exception as e:
            logger.warning(f"TF-IDF generation failed: {e}. Using zero features.")
            return np.zeros((len(descriptions), 0)), []

    def _create_categorical_features(self, deviations: List[Dict[str, Any]]) -> Tuple[np.ndarray, List[str]]:
        """
        Create one-hot encoded features for categorical fields.

        Args:
            deviations: List of deviations

        Returns:
            Tuple of (categorical_matrix, feature_names)
        """
        features = []
        feature_names = []

        # 1. Deviation Type (one-hot encoding for top 20 types)
        deviation_types = [d.get('deviation_type', 'unknown') for d in deviations]
        type_counts = Counter(deviation_types)
        self.deviation_types = [dtype for dtype, _ in type_counts.most_common(20)]

        type_features = np.zeros((len(deviations), len(self.deviation_types)))
        for i, dtype in enumerate(deviation_types):
            if dtype in self.deviation_types:
                idx = self.deviation_types.index(dtype)
                type_features[i, idx] = 1

        features.append(type_features)
        feature_names.extend([f"type_{dtype}" for dtype in self.deviation_types])

        # Combine all categorical features
        categorical_matrix = np.hstack(features) if features else np.zeros((len(deviations), 0))

        logger.info(f"Generated {categorical_matrix.shape[1]} categorical features")
        return categorical_matrix, feature_names

    def _create_numerical_features(self, deviations: List[Dict[str, Any]]) -> Tuple[np.ndarray, List[str]]:
        """
        Create numerical features.

        Args:
            deviations: List of deviations

        Returns:
            Tuple of (numerical_matrix, feature_names)
        """
        features = []
        feature_names = []

        # 1. SEVERITY SCORE (4=critical, 3=high, 2=medium, 1=low)
        severity_scores = np.array([
            self.severity_map.get(d.get('severity', 'low').lower(), 1)
            for d in deviations
        ]).reshape(-1, 1)
        features.append(severity_scores)
        feature_names.append('severity_score')

        # 2. TEMPORAL FEATURES (if timestamps available)
        temporal_features = self._extract_temporal_features(deviations)
        if temporal_features is not None:
            features.append(temporal_features)
            feature_names.extend(['hour_normalized', 'day_of_week_normalized'])

        # 3. OFFICER FEATURES (top 20 officers)
        officer_features = self._extract_officer_features(deviations)
        if officer_features is not None:
            features.append(officer_features)
            feature_names.extend([f"officer_{oid}" for oid in self.top_officers])

        # 4. DESCRIPTION LENGTH
        desc_lengths = np.array([
            len(d.get('description', ''))
            for d in deviations
        ]).reshape(-1, 1)
        features.append(desc_lengths)
        feature_names.append('description_length')

        # Combine all numerical features
        numerical_matrix = np.hstack(features) if features else np.zeros((len(deviations), 0))

        logger.info(f"Generated {numerical_matrix.shape[1]} numerical features")
        return numerical_matrix, feature_names

    def _extract_temporal_features(self, deviations: List[Dict[str, Any]]) -> np.ndarray:
        """Extract temporal features from timestamps."""
        temporal_features = []

        for deviation in deviations:
            timestamp = deviation.get('detected_at') or deviation.get('created_at')

            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        # Try multiple datetime formats
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                            try:
                                dt = datetime.strptime(timestamp.split('.')[0], fmt)
                                break
                            except ValueError:
                                continue
                        else:
                            # No format worked
                            temporal_features.append([0.5, 0.5])  # Default middle values
                            continue
                    elif isinstance(timestamp, datetime):
                        dt = timestamp
                    else:
                        temporal_features.append([0.5, 0.5])
                        continue

                    # Normalize hour (0-23 -> 0-1)
                    hour_normalized = dt.hour / 24.0

                    # Normalize day of week (0-6 -> 0-1)
                    day_normalized = dt.weekday() / 7.0

                    temporal_features.append([hour_normalized, day_normalized])

                except Exception:
                    temporal_features.append([0.5, 0.5])  # Default
            else:
                temporal_features.append([0.5, 0.5])  # No timestamp

        return np.array(temporal_features)

    def _extract_officer_features(self, deviations: List[Dict[str, Any]]) -> np.ndarray:
        """Extract officer features (binary flags for top 20 officers)."""
        officer_ids = [d.get('officer_id', 'unknown') for d in deviations]

        # Get top 20 officers by frequency
        officer_counts = Counter(officer_ids)
        self.top_officers = [oid for oid, _ in officer_counts.most_common(20)]

        # Create binary features
        officer_features = np.zeros((len(deviations), len(self.top_officers)))
        for i, oid in enumerate(officer_ids):
            if oid in self.top_officers:
                idx = self.top_officers.index(oid)
                officer_features[i, idx] = 1

        return officer_features

    def transform(self, deviations: List[Dict[str, Any]]) -> np.ndarray:
        """
        Transform new deviations using fitted transformers.

        Args:
            deviations: List of deviation dictionaries

        Returns:
            Feature matrix
        """
        if self.tfidf is None:
            raise ValueError("FeatureEngineer must be fitted before transform")

        # Apply same transformations
        descriptions = [d.get('description', '') for d in deviations]
        tfidf_features = self.tfidf.transform(descriptions).toarray()

        categorical_features, _ = self._create_categorical_features(deviations)
        numerical_features, _ = self._create_numerical_features(deviations)

        # Combine
        feature_matrix = np.hstack([tfidf_features, categorical_features, numerical_features])

        return feature_matrix
