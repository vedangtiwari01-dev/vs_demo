"""
ML Analysis Router

FastAPI endpoints for machine learning analysis services.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from app.services.ml.intelligent_sampler import IntelligentSampler

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/ml', tags=['ML Analysis'])


class IntelligentSamplingRequest(BaseModel):
    """Request model for intelligent sampling."""
    deviations: List[Dict[str, Any]] = Field(..., description="All deviations to sample from")
    statistical_insights: Optional[Dict[str, Any]] = Field(None, description="Statistical insights from Layer 3")
    target_sample_size: int = Field(75, ge=10, le=200, description="Target number of representatives (10-200)")


class IntelligentSamplingResponse(BaseModel):
    """Response model for intelligent sampling."""
    representative_sample: List[Dict[str, Any]]
    cluster_assignments: List[int]
    anomaly_scores: List[float]
    cluster_statistics: Dict[str, Any]
    sampling_metadata: Dict[str, Any]


@router.post('/sample', response_model=IntelligentSamplingResponse)
async def intelligent_sampling(request: IntelligentSamplingRequest):
    """
    Intelligently sample deviations using ML clustering and anomaly detection.

    This endpoint implements Layer 4 of the 5-layer pipeline:
    - Feature engineering (TF-IDF, one-hot, severity, temporal, officer)
    - DBSCAN clustering (primary) or K-means (fallback)
    - Isolation Forest anomaly detection
    - Intelligent sampling strategy (anomalies + cluster reps + coverage)

    **Compression**: 1500-3000 deviations → 50-100 representatives (20x)
    **Time**: ~20-30 seconds for 3000 deviations
    **Goal**: Cost-effective LLM analysis while preserving ALL patterns

    Args:
        request: Sampling request with deviations and configuration

    Returns:
        IntelligentSamplingResponse with selected representatives and metadata
    """
    try:
        logger.info(f"Intelligent sampling request: {len(request.deviations)} deviations")

        # Validate input
        if not request.deviations:
            raise HTTPException(
                status_code=400,
                detail="No deviations provided for sampling"
            )

        # Initialize sampler
        sampler = IntelligentSampler()

        # Perform intelligent sampling
        result = sampler.sample_deviations(
            deviations=request.deviations,
            statistical_insights=request.statistical_insights or {},
            target_sample_size=request.target_sample_size
        )

        logger.info(
            f"Sampling complete: {result['sampling_metadata']['representatives_selected']} "
            f"representatives ({result['sampling_metadata']['compression_ratio']} compression)"
        )

        return IntelligentSamplingResponse(**result)

    except Exception as e:
        logger.error(f"Intelligent sampling failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Intelligent sampling failed: {str(e)}"
        )


@router.get('/health')
async def ml_health_check():
    """
    Health check endpoint for ML service.

    Returns:
        Health status and available ML capabilities
    """
    try:
        # Check if ML libraries are available
        import numpy as np
        import pandas as pd
        import sklearn

        return {
            'status': 'healthy',
            'service': 'ml_analysis',
            'capabilities': [
                'intelligent_sampling',
                'clustering (DBSCAN, K-means)',
                'anomaly_detection (Isolation Forest)',
                'feature_engineering (TF-IDF, one-hot)'
            ],
            'libraries': {
                'numpy': np.__version__,
                'pandas': pd.__version__,
                'scikit-learn': sklearn.__version__
            }
        }
    except ImportError as e:
        return {
            'status': 'degraded',
            'service': 'ml_analysis',
            'error': f'Missing ML library: {str(e)}'
        }


@router.post('/test-sample')
async def test_sampling():
    """
    Test endpoint with sample data for debugging.

    Returns:
        Sample result demonstrating intelligent sampling
    """
    # Create test deviations
    test_deviations = [
        {
            'case_id': f'CASE-{i:03d}',
            'deviation_type': ['kyc_cdd', 'approval_authority', 'timing', 'documentation'][i % 4],
            'severity': ['critical', 'high', 'medium', 'low'][i % 4],
            'description': f'Test deviation {i}',
            'officer_id': f'OFF{(i % 5) + 1:02d}',
            'timestamp': f'2025-01-{(i % 28) + 1:02d} 10:00:00'
        }
        for i in range(100)
    ]

    sampler = IntelligentSampler()
    result = sampler.sample_deviations(
        deviations=test_deviations,
        statistical_insights={},
        target_sample_size=20
    )

    return {
        'message': 'Test sampling successful',
        'input_size': len(test_deviations),
        'output_size': len(result['representative_sample']),
        'metadata': result['sampling_metadata']
    }
