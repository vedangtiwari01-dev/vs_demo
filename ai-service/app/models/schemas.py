from pydantic import BaseModel
from typing import List, Optional, Dict, Any
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

class Rule(BaseModel):
    type: str
    description: str
    step_number: Optional[int] = None
    severity: str = 'medium'
    condition_logic: Optional[Dict[str, Any]] = None

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

class SOPRule(BaseModel):
    id: int
    type: str
    description: str
    step_number: Optional[int] = None
    severity: str

class DeviationDetectionRequest(BaseModel):
    logs: List[WorkflowLog]
    rules: List[SOPRule]

class Deviation(BaseModel):
    case_id: str
    officer_id: str
    deviation_type: str
    rule_id: Optional[int] = None
    severity: str
    description: str
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class DeviationDetectionResponse(BaseModel):
    deviations: List[Deviation]

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
