import json
import logging
import re
from typing import Dict, List, Any, Optional
from app.services.claude.client import ClaudeClient
from app.services.claude.prompts import format_column_mapping_prompt

logger = logging.getLogger(__name__)

def extract_json_from_text(text: str) -> str:
    """Extract JSON from text that might contain markdown code fences or extra text."""
    text = text.strip()

    # Try to find JSON in markdown code fence (non-greedy match)
    json_fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_fence_match:
        json_text = json_fence_match.group(1)
        return clean_json_string(json_text)

    # Try to find JSON object directly (greedy match for complete object)
    # Match from first { to last }
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_text = text[first_brace:last_brace + 1]
        return clean_json_string(json_text)

    return text

def clean_json_string(json_str: str) -> str:
    """Clean common JSON formatting issues."""
    # Remove trailing commas before closing braces/brackets
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    # Remove any text before first { or after last }
    json_str = json_str.strip()
    return json_str

class ColumnMapper:
    """
    Intelligent CSV column mapping using Claude LLM.
    Maps user CSV headers to standardized system fields.
    """

    # System fields that workflow logs must have
    REQUIRED_FIELDS = ['case_id', 'officer_id', 'step_name', 'action', 'timestamp']

    # Extended optional fields - improve analysis quality when present
    OPTIONAL_FIELDS = [
        # Core workflow
        'duration_seconds', 'status', 'notes', 'comments', 'step_id', 'stage_name', 'workflow_version', 'action_type', 'sub_status',
        # Entity identifiers
        'application_id', 'loan_id', 'customer_id', 'customer_name', 'customer_segment', 'customer_type', 'customer_risk_rating',
        'group_id', 'related_party_flag', 'staff_flag', 'portfolio_id',
        # Product & channel
        'product_type', 'sub_product_type', 'scheme_code', 'secured_unsecured_flag',
        'channel', 'branch_code', 'branch_name', 'region', 'geo_code',
        # Amounts & terms
        'loan_amount_requested', 'loan_amount_sanctioned', 'loan_amount_disbursed',
        'interest_rate', 'interest_type', 'processing_fee', 'other_charges',
        'tenor_months', 'tenor_days', 'repayment_frequency', 'emi_amount',
        'ltv_ratio', 'margin_pct', 'total_group_exposure', 'customer_total_exposure',
        # Risk & credit
        'credit_score_bureau', 'credit_score_internal', 'scorecard_version', 'score_band',
        'emi_to_income_ratio', 'dti_ratio', 'risk_grade', 'risk_category',
        # Collateral & security
        'collateral_type', 'collateral_description', 'collateral_value', 'collateral_value_date',
        'valuation_status', 'valuation_firm_id', 'security_created_flag', 'security_perfected_flag',
        # KYC / AML
        'kyc_status', 'kyc_completed_flag', 'kyc_date', 'kyc_mode',
        'sanctions_hit_flag', 'watchlist_hit_flag', 'pep_flag', 'aml_risk_rating',
        # Workflow detail
        'officer_name', 'officer_role', 'approval_role', 'approval_level',
        'timestamp_start', 'timestamp_end', 'step_time', 'business_date',
        'queue_name', 'queue_priority', 'sla_target_timestamp', 'sla_breach_flag',
        # Approvals & exceptions
        'approver_id', 'approver_role', 'approval_decision', 'approval_timestamp',
        'exception_flag', 'exception_reason', 'exception_approver_id',
        'override_flag', 'override_reason', 'override_approver_id',
        # Disbursement
        'disbursement_date', 'disbursement_amount', 'disbursement_mode',
        'mandate_status', 'first_emi_date', 'statement_generated_flag',
        'post_disbursement_qc_flag', 'post_disbursement_qc_date', 'qc_findings',
        # Collections & restructuring
        'overdue_days', 'bucket', 'collection_status', 'collection_agent_id',
        'restructure_flag', 'restructure_date', 'restructure_type',
        'writeoff_flag', 'writeoff_amount', 'writeoff_date',
        # Audit & data quality
        'created_by', 'created_at', 'updated_by', 'updated_at',
        'source_system', 'source_file_name', 'import_batch_id',
        'audit_trail_id', 'log_level', 'error_code', 'error_message'
    ]

    def __init__(self):
        """Initialize column mapper with Claude client."""
        try:
            self.claude_client = ClaudeClient()
        except ValueError as e:
            logger.warning(f"Claude client not available: {str(e)}")
            self.claude_client = None

    def analyze_headers(
        self,
        headers: List[str],
        sample_rows: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Analyze CSV headers and suggest mappings to system fields using Claude.

        Args:
            headers: List of column names from the CSV
            sample_rows: Optional list of sample data rows (first 3 rows recommended)

        Returns:
            Dict containing:
                - mappings: Dict mapping CSV columns to system fields
                - confidence_scores: Confidence for each mapping (0-1)
                - notes_column: Name of column containing notes/comments
                - unmapped_columns: Columns that don't map to system fields
                - warnings: Any issues or ambiguities to flag
        """
        if not self.claude_client:
            logger.error("Claude client not available, using fallback mapping")
            return self._fallback_mapping(headers)

        try:
            # Format prompt with headers and sample data
            prompt = format_column_mapping_prompt(headers, sample_rows or [])

            # Call Claude for analysis
            logger.info(f"Analyzing {len(headers)} CSV headers with Claude")
            response = self.claude_client.generate(
                prompt=prompt,
                system="You are an expert at analyzing CSV data structures for loan processing workflows.",
                json_mode=True
            )

            # Extract and parse JSON response (handles markdown code fences)
            json_text = extract_json_from_text(response['text'])

            # Log the extracted JSON for debugging
            logger.info(f"Extracted JSON (first 500 chars): {json_text[:500]}")

            try:
                result = json.loads(json_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {str(e)}")
                logger.error(f"JSON text around error (chars {max(0, e.pos-100)}:{e.pos+100}):")
                logger.error(json_text[max(0, e.pos-100):e.pos+100])
                logger.error(f"Full Claude response: {response['text'][:1000]}")
                raise

            # Validate the response structure
            if not self._validate_mapping_result(result):
                logger.warning("Invalid mapping response from Claude, using fallback")
                return self._fallback_mapping(headers)

            logger.info(f"Successfully mapped {len(result['mappings'])} columns")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {str(e)}")
            logger.info("Using fallback mapping due to JSON parse error")
            return self._fallback_mapping(headers)
        except Exception as e:
            logger.error(f"Error analyzing headers with Claude: {str(e)}")
            return self._fallback_mapping(headers)

    def _validate_mapping_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate that the Claude response has the expected structure.

        Args:
            result: Parsed JSON response from Claude

        Returns:
            True if valid, False otherwise
        """
        required_keys = ['mappings', 'notes_column', 'unmapped_columns', 'warnings']
        if not all(key in result for key in required_keys):
            return False

        # Check that mappings are simple strings, not nested objects
        if not isinstance(result['mappings'], dict):
            logger.error("Mappings must be a dictionary")
            return False

        # Check that we have mappings for all required fields
        # Mappings should now be simple: {"CSV_Col": "system_field"}
        mapped_fields = set(result['mappings'].values())
        missing_required = set(self.REQUIRED_FIELDS) - mapped_fields

        if missing_required:
            logger.warning(f"Missing mappings for required fields: {missing_required}")
            # Don't fail completely, but log the warning
            result['warnings'].append(
                f"Unable to map required fields: {', '.join(missing_required)}"
            )

        return True

    def _fallback_mapping(self, headers: List[str]) -> Dict[str, Any]:
        """
        Fallback mapping using hardcoded rules when Claude is unavailable.

        Args:
            headers: List of CSV column names

        Returns:
            Dict with same structure as analyze_headers
        """
        logger.info("Using fallback mapping with hardcoded rules")

        mappings = {}
        unmapped = []
        notes_column = None

        # Comprehensive hardcoded mapping rules (case-insensitive)
        mapping_rules = {
            # Required fields
            'case_id': ['case_id', 'caseid', 'case id', 'loan_id', 'loanid', 'loan id', 'application_id', 'case', 'loan', 'application'],
            'officer_id': ['officer_id', 'officerid', 'officer id', 'user', 'user_id', 'userid', 'employee', 'employee_id', 'staff_id'],
            'step_name': ['step_name', 'stepname', 'step name', 'step', 'activity', 'task', 'stage', 'stage_name'],
            'action': ['action', 'decision', 'outcome', 'action_type'],
            'timestamp': ['timestamp', 'date', 'time', 'datetime', 'created_at', 'date_time', 'transaction_time'],

            # Core workflow optional
            'duration_seconds': ['duration', 'duration_seconds', 'time_taken', 'elapsed', 'processing_time'],
            'status': ['status', 'state', 'sub_status'],
            'notes': ['notes', 'comments', 'comment', 'remarks', 'note', 'explanation', 'reason', 'justification'],

            # Entity identifiers
            'customer_id': ['customer_id', 'customerid', 'client_id', 'cust_id', 'borrower_id'],
            'customer_name': ['customer_name', 'customername', 'client_name', 'borrower_name', 'applicant_name'],
            'loan_amount_requested': ['loan_amount', 'amount_requested', 'requested_amount', 'loan_amt', 'principal'],
            'loan_amount_sanctioned': ['amount_sanctioned', 'sanctioned_amount', 'approved_amount', 'sanction_amt'],
            'loan_amount_disbursed': ['amount_disbursed', 'disbursed_amount', 'disbursal_amount', 'disbursement_amt'],

            # Product & channel
            'product_type': ['product_type', 'product', 'loan_type', 'product_name', 'scheme'],
            'branch_code': ['branch_code', 'branch', 'branch_id', 'location_code'],
            'channel': ['channel', 'source_channel', 'origination_channel'],

            # Risk & credit
            'credit_score_bureau': ['credit_score', 'bureau_score', 'cibil_score', 'score'],
            'emi_to_income_ratio': ['emi_ratio', 'emi_to_income', 'debt_to_income', 'dti', 'emi_income_ratio'],
            'ltv_ratio': ['ltv', 'ltv_ratio', 'loan_to_value'],
            'risk_grade': ['risk_grade', 'risk_rating', 'risk_category', 'rating'],

            # KYC / AML
            'kyc_status': ['kyc_status', 'kyc', 'kyc_verified', 'kyc_complete'],
            'sanctions_hit_flag': ['sanctions_hit', 'sanctions', 'watchlist_hit', 'screening_result'],
            'pep_flag': ['pep', 'pep_flag', 'politically_exposed'],

            # Collateral
            'collateral_type': ['collateral_type', 'collateral', 'security_type', 'asset_type'],
            'collateral_value': ['collateral_value', 'security_value', 'asset_value', 'property_value'],

            # Approvals
            'approver_id': ['approver_id', 'approver', 'approved_by', 'sanctioned_by'],
            'approval_decision': ['approval_decision', 'approval', 'decision'],
            'exception_flag': ['exception', 'exception_flag', 'deviation', 'override'],

            # Disbursement
            'disbursement_date': ['disbursement_date', 'disbursal_date', 'payout_date', 'release_date'],
            'disbursement_amount': ['disbursement_amount', 'disbursal_amt', 'payout_amount'],

            # Collections
            'overdue_days': ['overdue_days', 'dpd', 'days_past_due', 'delinquent_days'],
            'bucket': ['bucket', 'dpd_bucket', 'collection_bucket', 'aging_bucket']
        }

        for header in headers:
            header_lower = header.lower().strip()
            mapped = False

            for system_field, patterns in mapping_rules.items():
                if any(pattern.lower() == header_lower or pattern.lower() in header_lower for pattern in patterns):
                    # Simple string mapping (no nested objects)
                    mappings[header] = system_field
                    if system_field in ['notes', 'comments'] and not notes_column:
                        notes_column = header
                    mapped = True
                    break

            if not mapped:
                unmapped.append(header)

        # Check for missing required fields
        mapped_fields = set(mappings.values())
        missing_required = set(self.REQUIRED_FIELDS) - mapped_fields

        warnings = []
        if missing_required:
            warnings.append(
                f"Unable to map required fields: {', '.join(missing_required)}. "
                f"Please map these manually."
            )

        return {
            'mappings': mappings,
            'notes_column': notes_column,
            'unmapped_columns': unmapped,
            'warnings': warnings
        }

    def apply_mapping(
        self,
        data: List[Dict[str, Any]],
        mapping: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Apply a confirmed mapping to transform CSV data.

        Args:
            data: List of dictionaries representing CSV rows
            mapping: Dict mapping CSV column names to system field names

        Returns:
            List of transformed dictionaries with system field names
        """
        transformed_data = []

        for row in data:
            transformed_row = {}
            for csv_column, system_field in mapping.items():
                if csv_column in row:
                    transformed_row[system_field] = row[csv_column]

            transformed_data.append(transformed_row)

        logger.info(f"Applied mapping to {len(transformed_data)} rows")
        return transformed_data

    def get_mapping_summary(self, mapping_result: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of the mapping.

        Args:
            mapping_result: Result from analyze_headers

        Returns:
            Human-readable summary string
        """
        summary_lines = [
            "Column Mapping Summary:",
            "-" * 50
        ]

        # Mappings are now simple strings: {"CSV_Col": "system_field"}
        for csv_col, system_field in mapping_result['mappings'].items():
            summary_lines.append(f"✓ {csv_col} → {system_field}")

        if mapping_result['notes_column']:
            summary_lines.append(f"\n📝 Notes column detected: {mapping_result['notes_column']}")

        if mapping_result['unmapped_columns']:
            summary_lines.append(f"\n⚠ Unmapped columns: {', '.join(mapping_result['unmapped_columns'])}")

        if mapping_result['warnings']:
            summary_lines.append("\n⚠ Warnings:")
            for warning in mapping_result['warnings']:
                summary_lines.append(f"  - {warning}")

        return "\n".join(summary_lines)
