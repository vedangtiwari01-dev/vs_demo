from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    BehavioralProfileRequest,
    BehavioralProfileResponse,
    PatternDetectionRequest,
    PatternDetectionResponse
)
from app.services.behavioral.profile_builder import ProfileBuilder
from app.services.behavioral.pattern_analyzer import PatternAnalyzer

router = APIRouter(prefix='/ai/behavioral', tags=['Behavioral Analysis'])

@router.post('/profile', response_model=BehavioralProfileResponse)
async def build_profile(request: BehavioralProfileRequest):
    """Build behavioral profile for an officer"""
    try:
        logs_dict = [log.model_dump() for log in request.logs]
        profile = ProfileBuilder.build_profile(
            request.officer_id,
            logs_dict,
            request.deviations
        )
        return BehavioralProfileResponse(**profile)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/patterns', response_model=PatternDetectionResponse)
async def detect_patterns(request: PatternDetectionRequest):
    """Detect behavioral patterns"""
    try:
        logs_dict = [log.model_dump() for log in request.logs]
        patterns = PatternAnalyzer.detect_patterns(
            request.officer_id,
            logs_dict,
            request.deviations
        )
        return PatternDetectionResponse(patterns=patterns)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/risk-score')
async def calculate_risk_score(request: BehavioralProfileRequest):
    """Calculate risk score for an officer"""
    try:
        logs_dict = [log.model_dump() for log in request.logs]
        profile = ProfileBuilder.build_profile(
            request.officer_id,
            logs_dict,
            request.deviations
        )
        return {'officer_id': request.officer_id, 'risk_score': profile['risk_score']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
