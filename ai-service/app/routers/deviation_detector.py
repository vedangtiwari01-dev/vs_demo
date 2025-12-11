from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    DeviationDetectionRequest,
    DeviationDetectionResponse,
    PatternAnalysisRequest,
    PatternAnalysisResponse
)
from app.services.deviation.sequence_checker import SequenceChecker
from app.services.deviation.rule_validator import RuleValidator

router = APIRouter(prefix='/ai/deviation', tags=['Deviation Detection'])

@router.post('/detect', response_model=DeviationDetectionResponse)
async def detect_deviations(request: DeviationDetectionRequest):
    """Detect all deviations in workflow logs"""
    try:
        # Convert logs to dict format
        logs_dict = [log.dict() for log in request.logs]
        rules_dict = [rule.dict() for rule in request.rules]

        # Check sequences
        sequence_deviations = SequenceChecker.check_sequence(logs_dict, rules_dict)

        # Validate other rules
        rule_deviations = RuleValidator.validate_all(logs_dict, rules_dict)

        # Combine all deviations
        all_deviations = sequence_deviations + rule_deviations

        return DeviationDetectionResponse(deviations=all_deviations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/validate-sequence')
async def validate_sequence(request: DeviationDetectionRequest):
    """Validate workflow sequence only"""
    try:
        logs_dict = [log.dict() for log in request.logs]
        rules_dict = [rule.dict() for rule in request.rules]

        deviations = SequenceChecker.check_sequence(logs_dict, rules_dict)

        return DeviationDetectionResponse(deviations=deviations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/validate-approval')
async def validate_approval(request: DeviationDetectionRequest):
    """Validate approval requirements only"""
    try:
        logs_dict = [log.dict() for log in request.logs]
        rules_dict = [rule.dict() for rule in request.rules]

        deviations = RuleValidator.validate_all(logs_dict, rules_dict)

        return DeviationDetectionResponse(deviations=deviations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/analyze-patterns')
async def analyze_patterns(request: PatternAnalysisRequest):
    """
    Analyze patterns across ALL deviations with notes using Claude LLM.

    This is a cost-effective batch analysis that finds:
    - Behavioral patterns (officer habits)
    - Hidden rules (informal practices)
    - Systemic issues (recurring problems)
    - Time-based trends

    Makes 1 API call for all deviations instead of individual analysis.
    """
    try:
        from app.services.deviation.notes_analyzer import NotesAnalyzer
        from app.models.schemas import PatternAnalysisResponse

        # Initialize notes analyzer
        analyzer = NotesAnalyzer()

        # Perform batch pattern analysis (1 API call!)
        pattern_result = analyzer.analyze_pattern_batch(request.deviations)

        return PatternAnalysisResponse(**pattern_result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze patterns: {str(e)}"
        )
