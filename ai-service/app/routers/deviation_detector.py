from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    DeviationDetectionRequest,
    DeviationDetectionResponse,
    PatternAnalysisRequest,
    PatternAnalysisResponse
)
from app.services.deviation.sequence_checker import SequenceChecker
from app.services.deviation.rule_validator import RuleValidator
from app.services.deviation.eligibility_checker import EligibilityChecker
from app.services.deviation.kyc_checker import KYCChecker
from app.services.deviation.documentation_checker import DocumentationChecker
from app.services.deviation.collateral_checker import CollateralChecker
from app.services.deviation.disbursement_checker import DisbursementChecker
from app.services.deviation.collection_checker import CollectionChecker
from app.services.deviation.regulatory_checker import RegulatoryChecker
from app.services.deviation.data_quality_checker import DataQualityChecker
from app.services.deviation.conditional_rule_evaluator import ConditionalRuleEvaluator
from app.services.deviation.temporal_rule_evaluator import TemporalRuleEvaluator
from app.services.deviation.regulatory_aggregator import RegulatoryAggregator
from app.utils.clean_logger import clean_logger
from collections import Counter

router = APIRouter(prefix='/ai/deviation', tags=['Deviation Detection'])

# Regulatory limits configuration for portfolio-level compliance checks
REGULATORY_LIMITS = {
    'total_capital': 10000000,  # $10M capital base
    'customer_exposure_percent': 25,  # Max 25% to single customer
    'group_exposure_percent': 40,  # Max 40% to related group
    'sector_concentration_percent': 15,  # Max 15% to single sector
    'branch_concentration_percent': 30,  # Max 30% handled by single branch
}

@router.post('/detect', response_model=DeviationDetectionResponse)
async def detect_deviations(request: DeviationDetectionRequest):
    """Detect all deviations in workflow logs"""
    import traceback

    try:
        clean_logger.endpoint('POST', '/ai/deviation/detect', {
            'Logs': len(request.logs),
            'Rules': len(request.rules)
        })
        timer = clean_logger.start_timer()

        # Convert logs to dict format (Pydantic v2 uses model_dump())
        logs_dict = [log.model_dump() for log in request.logs]
        rules_dict = [rule.model_dump() for rule in request.rules]

        # ===================================================================
        # STEP 0: CLEAN WORKFLOW LOGS (Before deviation detection)
        # ===================================================================
        from app.services.data import WorkflowLogCleaner

        cleaned_logs, log_cleaning_report = WorkflowLogCleaner.clean_logs(
            logs_dict,
            remove_duplicates=True,
            validate_types=True,
            handle_missing=True,
            normalize_text=True,
            rules=rules_dict  # Pass rules for missing field analysis
        )

        log_quality = WorkflowLogCleaner.get_data_quality_score(log_cleaning_report)

        clean_logger.step('Data Cleaning', {
            'Input logs': len(logs_dict),
            'Cleaned logs': len(cleaned_logs),
            'Quality': f"{log_quality['score']}/100 ({log_quality['grade']})"
        })

        if len(cleaned_logs) == 0:
            clean_logger.error("No valid logs after cleaning")
            return DeviationDetectionResponse(deviations=[])

        # Use cleaned logs for deviation detection
        logs_dict = cleaned_logs

        # ===================================================================
        # DEVIATION DETECTION: Run all 13 checkers (with defensive error handling)
        # ===================================================================
        all_deviations = []
        checker_results = {}

        checkers = [
            ('SequenceChecker', lambda: SequenceChecker.check_sequence(logs_dict, rules_dict)),
            ('RuleValidator', lambda: RuleValidator.validate_all(logs_dict, rules_dict)),
            ('DataQualityChecker', lambda: DataQualityChecker.check_data_quality(logs_dict, rules_dict)),
            ('EligibilityChecker', lambda: EligibilityChecker.check_eligibility(logs_dict, rules_dict)),
            ('KYCChecker', lambda: KYCChecker.check_kyc(logs_dict, rules_dict)),
            ('DocumentationChecker', lambda: DocumentationChecker.check_documentation(logs_dict, rules_dict)),
            ('CollateralChecker', lambda: CollateralChecker.check_collateral(logs_dict, rules_dict)),
            ('DisbursementChecker', lambda: DisbursementChecker.check_disbursement(logs_dict, rules_dict)),
            ('CollectionChecker', lambda: CollectionChecker.check_collection(logs_dict, rules_dict)),
            ('RegulatoryChecker', lambda: RegulatoryChecker.check_regulatory(logs_dict, rules_dict)),
            ('ConditionalRuleEvaluator', lambda: ConditionalRuleEvaluator.evaluate(logs_dict, rules_dict)),
            ('TemporalRuleEvaluator', lambda: TemporalRuleEvaluator.evaluate(logs_dict, rules_dict)),
            ('RegulatoryAggregator', lambda: RegulatoryAggregator.evaluate(logs_dict, rules_dict, REGULATORY_LIMITS)),
        ]

        for checker_name, checker_func in checkers:
            try:
                deviations = checker_func()
                checker_results[checker_name] = len(deviations)
                all_deviations.extend(deviations)
            except Exception as e:
                clean_logger.warn(f'{checker_name} failed', str(e))
                checker_results[checker_name] = 0

        # Show aggregated checker results
        clean_logger.aggregated('Checker Results', checker_results)

        # Show deviations by type
        deviation_types = Counter(d['deviation_type'] for d in all_deviations)
        clean_logger.aggregated('Deviations by Type', dict(deviation_types))

        clean_logger.success('Deviation Detection Complete', {
            'Total deviations': len(all_deviations),
            'Checkers run': len(checker_results),
            'Data quality': f"{log_quality['score']}/100",
            'Time': clean_logger.get_elapsed(timer)
        })

        return DeviationDetectionResponse(
            deviations=all_deviations,
            log_cleaning_report=log_cleaning_report,
            log_quality=log_quality
        )
    except Exception as e:
        clean_logger.error('Deviation detection failed', e)
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
        from app.services.data import StatisticalAnalyzer
        from app.models.schemas import PatternAnalysisResponse

        clean_logger.endpoint('POST', '/ai/deviation/analyze-patterns', {
            'Deviations': len(request.deviations),
            'Workflow logs': len(request.workflow_logs) if request.workflow_logs else 0
        })
        timer = clean_logger.start_timer()

        # Check if we have any deviations at all
        if len(request.deviations) == 0:
            clean_logger.warn("No deviations provided for analysis")
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
        # STEP 0: CALCULATE WORKFLOW LOG QUALITY (if logs provided)
        # ===================================================================
        log_cleaning_report = None
        log_quality = None
        if request.workflow_logs:
            from app.services.data import WorkflowLogCleaner

            _, log_cleaning_report = WorkflowLogCleaner.clean_logs(
                request.workflow_logs,
                remove_duplicates=True,
                validate_types=True,
                handle_missing=True,
                normalize_text=True
            )
            log_quality = WorkflowLogCleaner.get_data_quality_score(log_cleaning_report)

            clean_logger.debug('Workflow log quality', {
                'score': f"{log_quality['score']}/100",
                'grade': log_quality['grade']
            })

        # ===================================================================
        # LAYER 1: USE ALL DEVIATIONS (NO CLEANING)
        # ===================================================================
        cleaned_deviations = request.deviations  # Use all deviations

        clean_logger.step('Layered Analysis Pipeline', {
            'Layer 1': 'Data validation',
            'Layer 2': 'Statistical analysis',
            'Layer 3': 'ML clustering & anomaly detection',
            'Layer 4': 'AI pattern recognition',
            'Deviations': len(cleaned_deviations)
        })

        # ===================================================================
        # LAYER 2: STATISTICAL ANALYSIS (Basic + Advanced)
        # ===================================================================
        statistical_analysis = StatisticalAnalyzer.analyze(cleaned_deviations)

        # Add advanced statistical analysis
        from app.services.data import AdvancedStatistics

        # Correlations and lift/odds on deviations
        statistical_analysis['advanced_correlations'] = AdvancedStatistics.analyze_correlations(cleaned_deviations)
        statistical_analysis['lift_and_odds'] = AdvancedStatistics.calculate_lift_and_odds(cleaned_deviations)

        # Time-series, control charts, change-point detection on WORKFLOW LOGS (if provided)
        if request.workflow_logs:
            statistical_analysis['time_series'] = AdvancedStatistics.time_series_analysis_logs(request.workflow_logs)
            statistical_analysis['control_charts'] = AdvancedStatistics.control_charts_logs(request.workflow_logs)
            statistical_analysis['change_points'] = AdvancedStatistics.change_point_detection_logs(request.workflow_logs)
        else:
            statistical_analysis['time_series'] = {'available': False, 'message': 'Workflow logs not provided'}
            statistical_analysis['control_charts'] = {'available': False, 'message': 'Workflow logs not provided'}
            statistical_analysis['change_points'] = {'available': False, 'message': 'Workflow logs not provided'}

        deviations_with_notes = [d for d in cleaned_deviations if d.get('notes')]

        clean_logger.step('Statistical Analysis', {
            'Total deviations': statistical_analysis['overview']['total_deviations'],
            'Unique cases': statistical_analysis['overview']['unique_cases'],
            'Unique officers': statistical_analysis['overview']['unique_officers'],
            'Severity score': f"{statistical_analysis['severity_distribution']['severity_score']}/100",
            'With notes': len(deviations_with_notes)
        })

        # ===================================================================
        # LAYER 3: ML ANALYSIS (clustering, anomaly detection, sampling)
        # ===================================================================

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
            clean_logger.step('ML Analysis', {
                'Original': len(cleaned_deviations),
                'Selected': len(ml_selected_deviations),
                'Compression': f"{ml_metadata['sampling']['compression_ratio']:.1f}x",
                'Clusters': ml_metadata['clustering']['n_clusters'],
                'Anomalies': ml_metadata['anomaly_detection']['n_anomalies']
            })
        else:
            clean_logger.warn('ML analysis skipped', ml_metadata.get('reason', 'unknown'))
            ml_selected_deviations = cleaned_deviations  # Use all if ML not applied

        # ===================================================================
        # LAYER 4: AI PATTERN ANALYSIS (with statistical + ML context)
        # ===================================================================

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

        # Enhance the response with workflow log quality, statistical and ML metadata
        if log_cleaning_report:
            pattern_result['log_cleaning_report'] = log_cleaning_report  # Workflow log cleaning
            pattern_result['log_quality'] = log_quality
        else:
            pattern_result['log_cleaning_report'] = None
            pattern_result['log_quality'] = None

        pattern_result['statistical_summary'] = {
            'total_analyzed': statistical_analysis['overview']['total_deviations'],
            'severity_score': statistical_analysis['severity_distribution']['severity_score'],
            'severity_assessment': statistical_analysis['severity_distribution']['severity_assessment'],
            'top_deviation_types': statistical_analysis['deviation_type_distribution']['top_10_types'][:5],
            'critical_mass_score': statistical_analysis['risk_indicators']['critical_mass_score'],
            'risk_assessment': statistical_analysis['risk_indicators']['critical_mass_assessment'],
            # Add temporal patterns and officer statistics (IMPORTANT FOR FRONTEND CHARTS)
            'temporal_patterns': statistical_analysis.get('temporal_patterns', {}),
            'officer_statistics': statistical_analysis.get('officer_statistics', {}),
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
            # Add full ML metadata for detailed frontend display (includes feature engineering info)
            pattern_result['ml_metadata'] = ml_metadata
        else:
            pattern_result['ml_summary'] = {
                'ml_applied': False,
                'reason': ml_metadata.get('reason', 'unknown')
            }
            pattern_result['ml_metadata'] = None

        clean_logger.success('Pattern Analysis Complete', {
            'Behavioral patterns': len(pattern_result.get('behavioral_patterns', [])),
            'Hidden rules': len(pattern_result.get('hidden_rules', [])),
            'Recommendations': len(pattern_result.get('recommendations', [])),
            'Risk insights': len(pattern_result.get('risk_insights', [])),
            'ML applied': ml_metadata.get('ml_applied', False),
            'Time': clean_logger.get_elapsed(timer)
        })

        return PatternAnalysisResponse(**pattern_result)

    except Exception as e:
        import traceback
        clean_logger.error('Pattern analysis failed', e)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze patterns: {str(e)}"
        )
