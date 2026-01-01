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
    import logging
    import traceback
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Received {len(request.logs)} logs and {len(request.rules)} rules")

        # Convert logs to dict format (Pydantic v2 uses model_dump())
        logs_dict = [log.model_dump() for log in request.logs]
        rules_dict = [rule.model_dump() for rule in request.rules]

        logger.info(f"Sample rule after model_dump: {rules_dict[0] if rules_dict else 'No rules'}")
        logger.info(f"Sample log after model_dump: {logs_dict[0] if logs_dict else 'No logs'}")

        # Check sequences
        logger.info("Starting sequence check...")
        sequence_deviations = SequenceChecker.check_sequence(logs_dict, rules_dict)
        logger.info(f"Found {len(sequence_deviations)} sequence deviations")

        # Validate other rules
        logger.info("Starting rule validation...")
        rule_deviations = RuleValidator.validate_all(logs_dict, rules_dict)
        logger.info(f"Found {len(rule_deviations)} rule deviations")

        # Combine all deviations
        all_deviations = sequence_deviations + rule_deviations
        logger.info(f"Total deviations: {len(all_deviations)}")

        return DeviationDetectionResponse(deviations=all_deviations)
    except Exception as e:
        logger.error(f"Deviation detection failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Deviation detection error: {str(e)}")

@router.post('/validate-sequence')
async def validate_sequence(request: DeviationDetectionRequest):
    """Validate workflow sequence only"""
    try:
        logs_dict = [log.model_dump() for log in request.logs]
        rules_dict = [rule.model_dump() for rule in request.rules]

        deviations = SequenceChecker.check_sequence(logs_dict, rules_dict)

        return DeviationDetectionResponse(deviations=deviations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/validate-approval')
async def validate_approval(request: DeviationDetectionRequest):
    """Validate approval requirements only"""
    try:
        logs_dict = [log.model_dump() for log in request.logs]
        rules_dict = [rule.model_dump() for rule in request.rules]

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
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Pattern analysis requested for {len(request.deviations)} deviations")

        # Check if we have any deviations at all
        if len(request.deviations) == 0:
            logger.warning("No deviations provided for analysis")
            return PatternAnalysisResponse(
                overall_summary="No deviations provided for pattern analysis",
                behavioral_patterns=[],
                hidden_rules=[],
                systemic_issues=[],
                time_patterns=[],
                justification_analysis={
                    "most_common_reasons": [],
                    "justified_count": 0,
                    "not_justified_count": 0,
                    "unclear_count": 0
                },
                risk_insights=["No deviations to analyze"],
                recommendations=["Deviations must be detected before pattern analysis"],
                api_calls_made=0,
                deviations_analyzed=0
            )

        # Count deviations with notes (for logging)
        deviations_with_notes = [d for d in request.deviations if d.get('notes')]
        logger.info(f"Found {len(deviations_with_notes)} deviations with notes, {len(request.deviations) - len(deviations_with_notes)} without notes")

        # Initialize notes analyzer
        analyzer = NotesAnalyzer()

        # Perform batch pattern analysis (1 API call!)
        pattern_result = analyzer.analyze_pattern_batch(request.deviations)

        return PatternAnalysisResponse(**pattern_result)

    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Pattern analysis failed: {str(e)}")
        logger.error(traceback.format_exc())

        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze patterns: {str(e)}"
        )
