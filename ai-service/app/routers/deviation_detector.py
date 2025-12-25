from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    DeviationDetectionRequest,
    DeviationDetectionResponse,
    PatternAnalysisRequest,
    PatternAnalysisResponse
)
from app.services.deviation.sequence_checker import SequenceChecker
from app.services.deviation.rule_validator import RuleValidator
from app.services.deviation.ai_rule_evaluator import AIRuleEvaluator

router = APIRouter(prefix='/ai/deviation', tags=['Deviation Detection'])

@router.post('/detect', response_model=DeviationDetectionResponse)
async def detect_deviations(request: DeviationDetectionRequest):
    """
    Detect all deviations in workflow logs using hybrid approach.

    Uses fast hardcoded validation for core 4 rule types (sequence, approval, timing, validation).
    Uses AI-powered generic evaluation for extended 146+ rule types.

    This allows the system to support 150+ banking/compliance rule types without
    hardcoding validation logic for each type.
    """
    try:
        # Convert logs to dict format
        logs_dict = [log.dict() for log in request.logs]
        rules_dict = [rule.dict() for rule in request.rules]

        # Separate core rules from extended rules
        CORE_TYPES = {'sequence', 'approval', 'timing', 'validation'}

        core_rules = []
        extended_rules = []

        for rule in rules_dict:
            rule_type = rule.get('rule_type', rule.get('type', ''))
            if rule_type in CORE_TYPES:
                core_rules.append(rule)
            else:
                extended_rules.append(rule)

        all_deviations = []

        # ==================================================================
        # TIER 1: Fast hardcoded validation for core 4 types
        # ==================================================================
        if core_rules:
            # Check sequences
            sequence_rules = [r for r in core_rules if r.get('rule_type', r.get('type')) == 'sequence']
            if sequence_rules:
                sequence_deviations = SequenceChecker.check_sequence(logs_dict, sequence_rules)
                all_deviations.extend(sequence_deviations)

            # Validate other core rules (approval, timing, validation)
            other_core_rules = [r for r in core_rules if r.get('rule_type', r.get('type')) != 'sequence']
            if other_core_rules:
                rule_deviations = RuleValidator.validate_all(logs_dict, other_core_rules)
                all_deviations.extend(rule_deviations)

        # ==================================================================
        # TIER 2: AI-powered evaluation for extended types
        # ==================================================================
        if extended_rules:
            # Group logs by case_id for AI evaluation
            cases = {}
            for log in logs_dict:
                case_id = log.get('case_id')
                if case_id:
                    if case_id not in cases:
                        cases[case_id] = []
                    cases[case_id].append(log)

            # Evaluate each case with AI
            ai_evaluator = AIRuleEvaluator()
            for case_id, case_logs in cases.items():
                ai_deviations = await ai_evaluator.evaluate_rules(
                    extended_rules,
                    case_logs,
                    case_id
                )
                all_deviations.extend(ai_deviations)

        # Return combined results with metadata
        return DeviationDetectionResponse(
            deviations=all_deviations,
            metadata={
                'total_rules_checked': len(rules_dict),
                'core_rules_checked': len(core_rules),
                'extended_rules_checked': len(extended_rules),
                'detection_methods_used': [
                    'hardcoded' if core_rules else None,
                    'ai_evaluator' if extended_rules else None
                ],
                'total_deviations_found': len(all_deviations)
            }
        )

    except Exception as e:
        import traceback
        print(f"Deviation detection error: {str(e)}")
        print(traceback.format_exc())
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
