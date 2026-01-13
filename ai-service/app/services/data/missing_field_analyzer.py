"""
Missing Field Analyzer

Analyzes rules and workflow logs to identify missing fields that prevent rule evaluation.
Shows which specific rules require which missing fields.
"""
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class MissingFieldAnalyzer:
    """
    Analyzes rules and workflow logs to identify missing fields that prevent rule evaluation.
    """

    @staticmethod
    def analyze_missing_fields(
        rules: List[Dict[str, Any]],
        workflow_logs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Identify which fields are required by rules but missing from workflow logs.

        Args:
            rules: List of rule dictionaries (must contain id, and optionally field_dependencies/required_fields)
            workflow_logs: List of workflow log dictionaries

        Returns:
            {
                'available_fields': List[str],           # Fields present in logs
                'required_fields_by_rule': Dict,          # {rule_id: [fields]}
                'all_required_fields': List[str],         # Unique set of all required fields
                'missing_fields': List[str],              # Fields required but not available
                'rules_affected': List[Dict],             # Rules that can't evaluate
                'impact_summary': {
                    'total_rules': int,
                    'evaluable_rules': int,
                    'blocked_rules': int,
                    'missing_field_count': int
                }
            }
        """
        logger.info(f"Analyzing missing fields for {len(rules)} rules and {len(workflow_logs)} logs")

        # Step 1: Extract available fields from logs
        available_fields = set()
        for log in workflow_logs:
            available_fields.update(log.keys())

        logger.info(f"Found {len(available_fields)} available fields in workflow logs")

        # Step 2: Extract required fields from rules
        required_fields_by_rule = {}
        all_required_fields = set()

        for rule in rules:
            rule_id = rule.get('id')

            # Get field dependencies (primary source)
            field_deps = rule.get('field_dependencies', [])

            # Also check required_fields as fallback
            req_fields = rule.get('required_fields', [])

            # Combine both sources
            rule_fields = set(field_deps) | set(req_fields)

            if rule_fields:
                required_fields_by_rule[rule_id] = list(rule_fields)
                all_required_fields.update(rule_fields)

        logger.info(f"Found {len(all_required_fields)} unique required fields across all rules")

        # Step 3: Identify missing fields
        missing_fields = all_required_fields - available_fields

        logger.info(f"Identified {len(missing_fields)} missing fields")

        # Step 4: Identify affected rules (which rules need which missing fields)
        rules_affected = []
        for rule in rules:
            rule_id = rule.get('id')
            rule_fields = set(required_fields_by_rule.get(rule_id, []))

            # Check if this rule has missing fields
            rule_missing = rule_fields & missing_fields

            if rule_missing:
                rules_affected.append({
                    'rule_id': rule_id,
                    'rule_type': rule.get('rule_type', 'Unknown'),
                    'rule_description': rule.get('rule_description', 'No description'),
                    'severity': rule.get('severity', 'unknown'),
                    'missing_fields': sorted(list(rule_missing)),
                    'required_fields': sorted(list(rule_fields))
                })

        # Sort by severity (critical first)
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'unknown': 4}
        rules_affected.sort(key=lambda x: severity_order.get(x['severity'], 4))

        logger.info(f"Found {len(rules_affected)} rules affected by missing fields")

        return {
            'available_fields': sorted(list(available_fields)),
            'required_fields_by_rule': required_fields_by_rule,
            'all_required_fields': sorted(list(all_required_fields)),
            'missing_fields': sorted(list(missing_fields)),
            'rules_affected': rules_affected,
            'impact_summary': {
                'total_rules': len(rules),
                'evaluable_rules': len(rules) - len(rules_affected),
                'blocked_rules': len(rules_affected),
                'missing_field_count': len(missing_fields)
            }
        }
