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
    OPTIONAL_FIELDS = ['duration_seconds', 'status', 'notes', 'comments']

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

        # Hardcoded mapping rules (case-insensitive)
        mapping_rules = {
            'case_id': ['case_id', 'caseid', 'case id', 'loan_id', 'loanid', 'loan id', 'case', 'loan'],
            'officer_id': ['officer_id', 'officerid', 'officer id', 'user', 'user_id', 'userid', 'employee', 'employee_id'],
            'step_name': ['step_name', 'stepname', 'step name', 'step', 'activity', 'action', 'task', 'stage'],
            'action': ['action', 'decision', 'result', 'outcome'],
            'timestamp': ['timestamp', 'date', 'time', 'datetime', 'created_at', 'date_time'],
            'duration_seconds': ['duration', 'duration_seconds', 'time_taken', 'elapsed'],
            'status': ['status', 'state', 'decision', 'result'],
            'notes': ['notes', 'comments', 'comment', 'remarks', 'note', 'explanation', 'reason', 'justification']
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
