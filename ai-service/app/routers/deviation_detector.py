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
    Analyze patterns across ALL deviations with LAYERED APPROACH:

    Layer 1: Data Cleaning
    - Remove duplicates
    - Validate data types
    - Handle missing values
    - Normalize text fields

    Layer 2: Statistical Analysis
    - Distribution analysis (severity, types)
    - Temporal patterns (time-based trends)
    - Officer-level statistics
    - Risk indicators

    Layer 3: AI Pattern Analysis (with statistical context)
    - Behavioral patterns (officer habits)
    - Hidden rules (informal practices)
    - Systemic issues (recurring problems)
    - Enhanced recommendations

    Makes 1 API call for all deviations instead of individual analysis.
    """
    try:
        from app.services.deviation.notes_analyzer import NotesAnalyzer
        from app.services.data import DataCleaner, StatisticalAnalyzer
        from app.models.schemas import PatternAnalysisResponse
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"=== LAYERED PATTERN ANALYSIS STARTED ===")
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

        # ===================================================================
        # LAYER 1: DATA CLEANING
        # ===================================================================
        logger.info("--- Layer 1: Data Cleaning ---")
        cleaned_deviations, cleaning_report = DataCleaner.clean_deviations(
            request.deviations,
            remove_duplicates=True,
            validate_types=True,
            handle_missing=True,
            normalize_text=True
        )

        data_quality = DataCleaner.get_data_quality_score(cleaning_report)
        logger.info(f"Data cleaning complete: {len(cleaned_deviations)}/{len(request.deviations)} deviations retained")
        logger.info(f"Data Quality Score: {data_quality['score']}/100 (Grade: {data_quality['grade']})")
        logger.info(f"Cleaning summary: {cleaning_report['duplicates_removed']} duplicates, "
                   f"{cleaning_report['invalid_types_fixed']} type fixes, "
                   f"{cleaning_report['missing_values_handled']} missing handled")

        if len(cleaned_deviations) == 0:
            logger.error("No valid deviations after cleaning")
            return PatternAnalysisResponse(
                overall_summary=f"All {len(request.deviations)} deviations were filtered out during data cleaning. "
                              f"Data quality issues: {cleaning_report['validation_errors'][:3]}",
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
                risk_insights=[f"Data quality: {data_quality['assessment']}"],
                recommendations=["Improve data quality at source", "Review data validation rules"],
                api_calls_made=0,
                deviations_analyzed=0
            )

        # ===================================================================
        # LAYER 2: STATISTICAL ANALYSIS
        # ===================================================================
        logger.info("--- Layer 2: Statistical Analysis ---")
        statistical_analysis = StatisticalAnalyzer.analyze(cleaned_deviations)

        logger.info(f"Statistical analysis complete:")
        logger.info(f"  - Total deviations: {statistical_analysis['overview']['total_deviations']}")
        logger.info(f"  - Unique cases: {statistical_analysis['overview']['unique_cases']}")
        logger.info(f"  - Unique officers: {statistical_analysis['overview']['unique_officers']}")
        logger.info(f"  - Severity score: {statistical_analysis['severity_distribution']['severity_score']}/100")
        logger.info(f"  - Top deviation type: {statistical_analysis['deviation_type_distribution']['top_10_types'][0]['type'] if statistical_analysis['deviation_type_distribution']['top_10_types'] else 'N/A'}")

        # Count deviations with notes (for logging)
        deviations_with_notes = [d for d in cleaned_deviations if d.get('notes')]
        logger.info(f"Found {len(deviations_with_notes)} deviations with notes, "
                   f"{len(cleaned_deviations) - len(deviations_with_notes)} without notes")

        # ===================================================================
        # LAYER 3: AI PATTERN ANALYSIS (with statistical context)
        # ===================================================================
        logger.info("--- Layer 3: AI Pattern Analysis ---")
        logger.info("Preparing context-enhanced analysis with statistical insights...")

        # Initialize notes analyzer
        analyzer = NotesAnalyzer()

        # Perform batch pattern analysis with statistical context (1 API call!)
        # Pass both cleaned deviations and statistical analysis as context
        pattern_result = analyzer.analyze_pattern_batch(
            cleaned_deviations,
            statistical_context=statistical_analysis
        )

        # Enhance the response with cleaning and statistical metadata
        pattern_result['data_quality'] = data_quality
        pattern_result['cleaning_report'] = cleaning_report
        pattern_result['statistical_summary'] = {
            'total_analyzed': statistical_analysis['overview']['total_deviations'],
            'severity_score': statistical_analysis['severity_distribution']['severity_score'],
            'severity_assessment': statistical_analysis['severity_distribution']['severity_assessment'],
            'top_deviation_types': statistical_analysis['deviation_type_distribution']['top_10_types'][:5],
            'critical_mass_score': statistical_analysis['risk_indicators']['critical_mass_score'],
            'risk_assessment': statistical_analysis['risk_indicators']['critical_mass_assessment']
        }

        logger.info("=== LAYERED PATTERN ANALYSIS COMPLETED ===")
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
