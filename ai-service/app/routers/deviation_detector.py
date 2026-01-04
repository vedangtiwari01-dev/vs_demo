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

        # ===================================================================
        # STEP 0: CLEAN WORKFLOW LOGS (Before deviation detection)
        # ===================================================================
        logger.info("--- Step 0: Cleaning Workflow Logs ---")
        from app.services.data import WorkflowLogCleaner

        cleaned_logs, log_cleaning_report = WorkflowLogCleaner.clean_logs(
            logs_dict,
            remove_duplicates=True,
            validate_types=True,
            handle_missing=True,
            normalize_text=True
        )

        log_quality = WorkflowLogCleaner.get_data_quality_score(log_cleaning_report)
        logger.info(f"Workflow log cleaning complete: {len(logs_dict)} → {len(cleaned_logs)} logs")
        logger.info(f"Log Quality Score: {log_quality['score']}/100 (Grade: {log_quality['grade']})")

        if len(cleaned_logs) == 0:
            logger.error("No valid logs after cleaning")
            return DeviationDetectionResponse(deviations=[])

        # Use cleaned logs for deviation detection
        logs_dict = cleaned_logs

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
        # LAYER 1: SKIP DEVIATION CLEANING (Logs already cleaned at Step 0)
        # ===================================================================
        # NOTE: We don't clean deviations because:
        # 1. Workflow logs are already cleaned (Step 0)
        # 2. Multiple occurrences of same deviation are valid (not duplicates)
        # 3. Cleaning deviations can hide important patterns
        logger.info("--- Layer 1: Using raw deviations (no cleaning) ---")
        cleaned_deviations = request.deviations
        logger.info(f"Total deviations to analyze: {len(cleaned_deviations)}")

        # ===================================================================
        # LAYER 2: STATISTICAL ANALYSIS (Basic + Advanced)
        # ===================================================================
        logger.info("--- Layer 2: Statistical Analysis ---")
        statistical_analysis = StatisticalAnalyzer.analyze(cleaned_deviations)

        # Add advanced statistical analysis
        logger.info("--- Layer 2a: Advanced Statistical Analysis ---")
        from app.services.data import AdvancedStatistics

        # Correlations and lift/odds on deviations
        statistical_analysis['advanced_correlations'] = AdvancedStatistics.analyze_correlations(cleaned_deviations)
        statistical_analysis['lift_and_odds'] = AdvancedStatistics.calculate_lift_and_odds(cleaned_deviations)

        # Time-series, control charts, change-point detection on WORKFLOW LOGS (if provided)
        # This shows workflow health trends, not just deviation trends
        if request.workflow_logs:
            logger.info(f"Analyzing workflow logs for temporal patterns ({len(request.workflow_logs)} logs)")
            statistical_analysis['time_series'] = AdvancedStatistics.time_series_analysis_logs(request.workflow_logs)
            statistical_analysis['control_charts'] = AdvancedStatistics.control_charts_logs(request.workflow_logs)
            statistical_analysis['change_points'] = AdvancedStatistics.change_point_detection_logs(request.workflow_logs)
        else:
            logger.warning("No workflow logs provided - temporal analysis will be limited")
            statistical_analysis['time_series'] = {'available': False, 'message': 'Workflow logs not provided'}
            statistical_analysis['control_charts'] = {'available': False, 'message': 'Workflow logs not provided'}
            statistical_analysis['change_points'] = {'available': False, 'message': 'Workflow logs not provided'}

        logger.info("Advanced statistical analysis complete")

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
        # LAYER 3: ML ANALYSIS (clustering, anomaly detection, sampling)
        # ===================================================================
        logger.info("--- Layer 3: ML Analysis ---")
        logger.info("Running ML pipeline: feature engineering, clustering, anomaly detection, intelligent sampling...")

        # Import ML pipeline
        from app.services.ml.ml_pipeline import MLPipeline

        # Initialize ML pipeline
        # Target sample size: 75-100 deviations for LLM
        # Contamination: 10% expected anomalies
        ml_pipeline = MLPipeline(target_sample_size=75, contamination=0.1)

        # Run ML analysis
        ml_results = ml_pipeline.analyze(cleaned_deviations)

        # Extract results
        ml_selected_deviations = ml_results['selected_deviations']
        ml_metadata = ml_results['ml_metadata']

        if ml_metadata.get('ml_applied'):
            logger.info(f"ML analysis complete:")
            logger.info(f"  - Original: {len(cleaned_deviations)} deviations")
            logger.info(f"  - Selected: {len(ml_selected_deviations)} deviations")
            logger.info(f"  - Compression: {ml_metadata['sampling']['compression_ratio']:.1f}x")
            logger.info(f"  - Clusters: {ml_metadata['clustering']['n_clusters']}")
            logger.info(f"  - Anomalies: {ml_metadata['anomaly_detection']['n_anomalies']}")
        else:
            logger.warning(f"ML analysis skipped: {ml_metadata.get('reason', 'unknown')}")
            ml_selected_deviations = cleaned_deviations  # Use all if ML not applied

        # ===================================================================
        # LAYER 4: AI PATTERN ANALYSIS (with statistical + ML context)
        # ===================================================================
        logger.info("--- Layer 4: AI Pattern Analysis ---")
        logger.info("Preparing context-enhanced analysis with statistical insights and ML labels...")

        # Initialize notes analyzer
        analyzer = NotesAnalyzer()

        # Prepare combined context for LLM
        ml_context_text = ml_pipeline.get_ml_context_for_llm(ml_metadata) if ml_metadata.get('ml_applied') else None

        # Perform batch pattern analysis with statistical + ML context (1 API call!)
        # Pass selected deviations (sampled intelligently) and full context
        pattern_result = analyzer.analyze_pattern_batch(
            ml_selected_deviations,
            statistical_context=statistical_analysis,
            ml_context=ml_context_text
        )

        # Enhance the response with statistical and ML metadata
        pattern_result['statistical_summary'] = {
            'total_analyzed': statistical_analysis['overview']['total_deviations'],
            'severity_score': statistical_analysis['severity_distribution']['severity_score'],
            'severity_assessment': statistical_analysis['severity_distribution']['severity_assessment'],
            'top_deviation_types': statistical_analysis['deviation_type_distribution']['top_10_types'][:5],
            'critical_mass_score': statistical_analysis['risk_indicators']['critical_mass_score'],
            'risk_assessment': statistical_analysis['risk_indicators']['critical_mass_assessment'],
            # Add advanced statistics
            'advanced_correlations': statistical_analysis.get('advanced_correlations'),
            'lift_and_odds': statistical_analysis.get('lift_and_odds'),
            'time_series': statistical_analysis.get('time_series'),
            'control_charts': statistical_analysis.get('control_charts'),
            'change_points': statistical_analysis.get('change_points')
        }

        # Add ML summary if applied
        if ml_metadata.get('ml_applied'):
            pattern_result['ml_summary'] = {
                'ml_applied': True,
                'original_count': len(cleaned_deviations),
                'selected_count': len(ml_selected_deviations),
                'compression_ratio': ml_metadata['sampling']['compression_ratio'],
                'clusters_found': ml_metadata['clustering']['n_clusters'],
                'anomalies_detected': ml_metadata['anomaly_detection']['n_anomalies'],
                'clustering_method': ml_metadata['clustering']['method'],
                'sampling_composition': ml_metadata['sampling']['composition']
            }
        else:
            pattern_result['ml_summary'] = {
                'ml_applied': False,
                'reason': ml_metadata.get('reason', 'unknown')
            }

        logger.info("=== LAYERED PATTERN ANALYSIS COMPLETED (4 LAYERS) ===")
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
