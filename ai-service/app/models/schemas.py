from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

# SOP Schemas
class SOPParseRequest(BaseModel):
    file_path: str
    file_type: str

class SOPParseResponse(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = None

class RuleExtractionRequest(BaseModel):
    text: str

# Conditional Logic Schemas
class Condition(BaseModel):
    """Represents a single condition in conditional logic"""
    field: Optional[str] = None  # For simple conditions (e.g., "loan_amount_sanctioned")
    operator: str  # ==, !=, <, >, <=, >=, AND, OR, NOT, IN, NOT_IN
    value: Optional[Any] = None  # For simple conditions (e.g., 10000)
    conditions: Optional[List['Condition']] = None  # For nested logical conditions (AND/OR/NOT)

    model_config = {'extra': 'allow'}

class ThenClause(BaseModel):
    """Represents the 'then' clause of conditional logic"""
    require_step: Optional[str] = None  # Single required step (e.g., "Manager Approval")
    require_steps: Optional[List[str]] = None  # Multiple required steps
    action: Optional[str] = None  # e.g., "reject", "flag_violation"
    severity: Optional[str] = None  # Severity override for the deviation
    reason: Optional[str] = None  # Reason for the requirement

    model_config = {'extra': 'allow'}

class ConditionalLogic(BaseModel):
    """Structured conditional logic for rules"""
    condition: Optional[Condition] = None
    then_clause: ThenClause = Field(alias='then')

    model_config = {
        'populate_by_name': True,
        'extra': 'allow'
    }

class Rule(BaseModel):
    # Field names with aliases for flexibility
    # We ask Claude for 'rule_type' and 'rule_description' in the prompt,
    # but accept 'type' and 'description' as aliases if Claude doesn't follow exactly
    rule_type: str = Field(alias='type')
    rule_description: str = Field(alias='description')
    step_number: Optional[float] = None
    severity: str = 'medium'
    condition_logic: Optional[Union[str, Dict[str, Any], ConditionalLogic]] = None  # Accepts string, dict, or structured ConditionalLogic
    required_fields: Optional[List[str]] = None
    timing_constraint: Optional[str] = None

    # NEW FIELDS for Enhanced Rule Extraction (10 additional fields)
    product_types: Optional[List[str]] = Field(default=["All"])  # Which products this rule applies to
    customer_segments: Optional[List[str]] = Field(default=["All"])  # Which customer segments
    channels: Optional[List[str]] = Field(default=["All"])  # Which channels (digital, branch, etc.)
    geography: Optional[List[str]] = Field(default=["All"])  # Geographic restrictions
    exceptions: Optional[List[Dict[str, Any]]] = None  # Exception cases
    calculation_formula: Optional[str] = None  # For calculation rules (e.g., "LTV = loan_amount / collateral_value")
    temporal_constraint: Optional[Dict[str, Any]] = None  # Step-to-step timing requirements
    threshold_value: Optional[float] = None  # Numeric thresholds (e.g., 10000, 0.8)
    field_dependencies: Optional[List[str]] = None  # Fields this rule depends on
    regulatory_reference: Optional[str] = None  # Legal/regulatory reference

    model_config = {
        # Allow both field names and aliases during validation (input)
        'populate_by_name': True,
        # Accept extra fields from Claude
        'extra': 'allow',
    }

class RuleExtractionResponse(BaseModel):
    rules: List[Rule]

# Deviation Detection Schemas
class WorkflowLog(BaseModel):
    case_id: str
    officer_id: str
    step_name: str
    action: str
    timestamp: str
    duration_seconds: Optional[int] = None
    status: Optional[str] = None

    # CRITICAL FIX: Allow extra fields from metadata (loan_amount, product_type, etc.)
    model_config = {
        'extra': 'allow',
    }

class SOPRule(BaseModel):
    id: int
    rule_type: str = Field(alias='type')
    rule_description: str = Field(alias='description')
    step_number: Optional[int] = None
    severity: str

    model_config = {
        'populate_by_name': True,
        'extra': 'allow',
    }

class DeviationDetectionRequest(BaseModel):
    logs: List[WorkflowLog]
    rules: List[SOPRule]

class Deviation(BaseModel):
    case_id: str
    officer_id: str
    timestamp: Optional[str] = None  # Case start time for temporal pattern analysis
    deviation_type: str
    rule_id: Optional[int] = None  # Integer ID for DB rules, None for template rules
    severity: str
    description: str
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

    # Rule Context - Added for LLM pattern analysis
    rule_description: Optional[str] = None
    rule_type: Optional[str] = None  # sequence, approval, timing, calculation, etc.
    rule_severity: Optional[str] = None

    # Case Context - Added for business insights
    loan_amount: Optional[float] = None
    customer_segment: Optional[str] = None
    product_type: Optional[str] = None

    # Phase 4 & 5 Enhancement: Allow additional context fields (credit_score, ltv, mandate_status)
    model_config = {
        'extra': 'allow',
    }

class DeviationDetectionResponse(BaseModel):
    deviations: List[Deviation]
    log_cleaning_report: Optional[Dict[str, Any]] = None  # Workflow log cleaning report
    log_quality: Optional[Dict[str, Any]] = None          # Workflow log quality score

# Behavioral Profiling Schemas
class BehavioralProfileRequest(BaseModel):
    officer_id: str
    logs: List[WorkflowLog]
    deviations: List[Dict[str, Any]]

class BehavioralProfileResponse(BaseModel):
    officer_id: str
    total_cases: int
    deviation_count: int
    deviation_rate: float
    average_workload: float
    risk_score: float
    patterns: Optional[Dict[str, Any]] = None

class PatternDetectionRequest(BaseModel):
    officer_id: str
    logs: List[WorkflowLog]
    deviations: List[Dict[str, Any]]

class Pattern(BaseModel):
    pattern_type: str
    description: str
    trigger_condition: Dict[str, Any]
    frequency: int
    confidence_score: float

class PatternDetectionResponse(BaseModel):
    patterns: List[Pattern]

# Synthetic Log Generation Schemas
class SyntheticLogRequest(BaseModel):
    scenario_type: str
    parameters: Dict[str, Any]

class SyntheticLogResponse(BaseModel):
    logs: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None

# Column Mapping Schemas
class ColumnMappingRequest(BaseModel):
    headers: List[str]
    sample_rows: Optional[List[Dict[str, Any]]] = None

class ColumnMappingResponse(BaseModel):
    mappings: Dict[str, Any]
    notes_column: Optional[str] = None
    unmapped_columns: List[str]
    warnings: List[str]

# Pattern Analysis Schemas
class PatternAnalysisRequest(BaseModel):
    deviations: List[Dict[str, Any]]
    workflow_logs: Optional[List[Dict[str, Any]]] = None  # For time-series/control charts

class PatternAnalysisResponse(BaseModel):
    overall_summary: str
    behavioral_patterns: List[Dict[str, Any]]
    hidden_rules: List[Dict[str, Any]]
    systemic_issues: List[Dict[str, Any]]
    time_patterns: Optional[List[Dict[str, Any]]] = []
    justification_analysis: Dict[str, Any]
    risk_insights: List[str]
    recommendations: List[str]
    api_calls_made: int
    deviations_analyzed: int

    # Phase 1: Data Processing metadata
    data_quality: Optional[Dict[str, Any]] = None
    log_cleaning_report: Optional[Dict[str, Any]] = None  # Workflow log cleaning report
    log_quality: Optional[Dict[str, Any]] = None          # Workflow log quality score
    statistical_summary: Optional[Dict[str, Any]] = None

    # Phase 2: ML metadata
    ml_summary: Optional[Dict[str, Any]] = None
