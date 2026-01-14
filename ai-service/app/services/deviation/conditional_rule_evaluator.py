"""
Conditional Rule Evaluator for Dynamic SOP Rule Evaluation

Evaluates conditional rules extracted from SOPs against workflow logs.
Handles conditional logic like:
- IF loan_amount >= 10000 THEN require Manager Approval
- IF credit_score < 600 AND loan_amount > 5000 THEN require Risk Head Approval
- IF loan_amount >= 50000 THEN require multiple approvals

NEW: Enhanced with calculation support and product/segment filtering:
- Cross-field calculations: IF loan_amount / collateral_value > 0.8 THEN flag LTV breach
- EMI validation: Calculate EMI and compare with actual
- Product-specific rules: Apply rules only to certain products/segments/channels
- Supports: DIVIDE, MULTIPLY, ADD, SUBTRACT, PERCENT, EMI, MAX, MIN, SUM, ABS, ROUND

Author: Claude Code
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
import json


class ConditionalRuleEvaluator:
    """
    Evaluates conditional rules extracted from SOPs against workflow logs.

    Handles conditional logic like:
    - IF loan_amount >= 10000 THEN require Manager Approval
    - IF credit_score < 600 AND loan_amount > 5000 THEN require Risk Head Approval

    Supports operators: ==, !=, <, >, <=, >=, IN, NOT_IN, AND, OR, NOT
    """

    SUPPORTED_OPERATORS = {
        '==': lambda a, b: a == b,
        '!=': lambda a, b: a != b,
        '<': lambda a, b: a < b,
        '>': lambda a, b: a > b,
        '<=': lambda a, b: a <= b,
        '>=': lambda a, b: a >= b,
        'IN': lambda a, b: a in b,
        'NOT_IN': lambda a, b: a not in b
    }

    # NEW: Calculation functions for cross-field validations
    SUPPORTED_FUNCTIONS = {
        'MULTIPLY': lambda a, b: a * b,
        'DIVIDE': lambda a, b: a / b if b != 0 else 0,
        'ADD': lambda a, b: a + b,
        'SUBTRACT': lambda a, b: a - b,
        'PERCENT': lambda a, b: (a / b) * 100 if b != 0 else 0,
        'EMI': lambda p, r, n: (p * r * (1+r)**n) / ((1+r)**n - 1) if n > 0 else 0,
        'MAX': lambda *args: max(args) if args else 0,
        'MIN': lambda *args: min(args) if args else 0,
        'SUM': lambda *args: sum(args),
        'ABS': lambda a: abs(a),
        'ROUND': lambda a, decimals=2: round(a, decimals)
    }

    # Phase 4 Enhancement: Hardcoded rule templates for common conditional patterns
    # These supplement rules extracted from SOP to catch violations that LLM may not structure properly
    CONDITIONAL_RULE_TEMPLATES = [
        {
            "id": "ltv_above_80_requires_credit_committee",
            "rule_type": "approval",
            "rule_description": "Loans with LTV exceeding 80% require Credit Committee approval",
            "severity": "critical",
            "condition_logic": {
                "condition": {
                    "calculation": {
                        "function": "DIVIDE",
                        "args": [
                            {"field": "loan_amount_sanctioned"},
                            {"field": "collateral_value"}
                        ]
                    },
                    "operator": ">",
                    "value": 0.80
                },
                "then": {
                    "require_step": "Credit Approval (Level 3 - Credit Committee)",
                    "require_step_alternatives": [
                        "Credit Committee Approval",
                        "Level 3 Credit Approval",
                        "Credit Approval Level 3",
                        "Credit Committee"
                    ],
                    "severity": "critical"
                }
            },
            "required_fields": ["loan_amount_sanctioned", "collateral_value", "step_name"],
            "product_types": ["All"],
            "customer_segments": ["All"],
            "channels": ["All"],
            "geography": ["All"]
        },
        {
            "id": "credit_score_650_699_requires_regional_manager",
            "rule_type": "approval",
            "rule_description": "Credit scores between 650-699 require Regional Credit Manager approval",
            "severity": "critical",
            "condition_logic": {
                "condition": {
                    "operator": "AND",
                    "conditions": [
                        {"field": "credit_score_bureau", "operator": ">=", "value": 650},
                        {"field": "credit_score_bureau", "operator": "<=", "value": 699}
                    ]
                },
                "then": {
                    "require_step": "Credit Approval (Level 2 - Regional Credit Manager)",
                    "require_step_alternatives": [
                        "Regional Credit Manager Approval",
                        "Level 2 Credit Approval",
                        "Credit Approval Level 2",
                        "Regional Manager Approval",
                        "RCM Approval"
                    ],
                    "severity": "critical"
                }
            },
            "required_fields": ["credit_score_bureau", "step_name"],
            "product_types": ["All"],
            "customer_segments": ["All"],
            "channels": ["All"],
            "geography": ["All"]
        },
        {
            "id": "mandate_must_be_active_before_disbursement",
            "rule_type": "disbursement",
            "rule_description": "EMI Mandate must be Active before Loan Disbursement",
            "severity": "critical",
            "condition_logic": {
                "condition": {
                    "field": "mandate_status",
                    "operator": "!=",
                    "value": "Active"
                },
                "then": {
                    "action": "block_step",
                    "blocked_step": "Loan Disbursement",
                    "blocked_step_alternatives": [
                        "Disbursement",
                        "Loan Disbursal",
                        "Disbursal",
                        "Fund Transfer"
                    ],
                    "severity": "critical"
                }
            },
            "required_fields": ["mandate_status", "step_name"],
            "product_types": ["All"],
            "customer_segments": ["All"],
            "channels": ["All"],
            "geography": ["All"]
        }
    ]

    @staticmethod
    def evaluate(logs: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Main entry point for conditional rule evaluation.

        Args:
            logs: Workflow logs with case_id, officer_id, step_name, action, timestamp, etc.
            rules: SOP rules with condition_logic field

        Returns:
            List of deviations detected by conditional rule evaluation
        """
        import logging
        logger = logging.getLogger(__name__)

        deviations = []

        # Group logs by case
        cases = defaultdict(list)
        for log in logs:
            cases[log['case_id']].append(log)

        # Get rules with condition_logic
        conditional_rules = [r for r in rules if r.get('condition_logic')]

        # Phase 4 Enhancement: Merge with hardcoded rule templates
        conditional_rules.extend(ConditionalRuleEvaluator.CONDITIONAL_RULE_TEMPLATES)

        logger.info(f"[ConditionalRuleEvaluator] Total rules: {len(rules)}, Conditional rules: {len(conditional_rules)} (including {len(ConditionalRuleEvaluator.CONDITIONAL_RULE_TEMPLATES)} templates)")
        logger.info(f"[ConditionalRuleEvaluator] Total cases: {len(cases)}")

        # Evaluate each case against each conditional rule
        for case_id, case_logs in cases.items():
            # Show aggregated data for first case
            if case_id == "CASE-001":
                log_data = ConditionalRuleEvaluator._aggregate_log_data(case_logs)
                logger.info(f"[ConditionalRuleEvaluator] CASE-001 aggregated data: loan_amount_sanctioned={log_data.get('loan_amount_sanctioned')}, steps={[l.get('step_name') for l in case_logs]}")

            for rule in conditional_rules:
                deviation = ConditionalRuleEvaluator._check_rule(case_id, case_logs, rule)
                if deviation:
                    deviations.append(deviation)

        logger.info(f"[ConditionalRuleEvaluator] Total deviations found: {len(deviations)}")

        return deviations

    @staticmethod
    def _get_rule_id_for_db(rule: Dict[str, Any]) -> Optional[int]:
        """
        Extract rule_id for database storage.

        Template rules have string IDs (e.g., 'mandate_must_be_active_before_disbursement')
        which can't be stored in the INTEGER rule_id column. Return None for templates.

        Args:
            rule: Rule dictionary

        Returns:
            Integer rule ID if present, None for template rules
        """
        rule_id = rule.get('id')
        if rule_id is None:
            return None

        # If it's already an integer, return it
        if isinstance(rule_id, int):
            return rule_id

        # If it's a string that can be converted to int, convert it
        if isinstance(rule_id, str):
            try:
                return int(rule_id)
            except ValueError:
                # String ID (template rule) - return None
                return None

        return None

    @staticmethod
    def _check_rule(case_id: str, logs: List[Dict[str, Any]], rule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if a conditional rule is violated.

        Args:
            case_id: The case ID being evaluated
            logs: All logs for this case
            rule: The rule with condition_logic

        Returns:
            Deviation dict if violated, None otherwise
        """
        import logging
        logger = logging.getLogger(__name__)

        # Debug for CASE-001 only
        debug_case = case_id == "CASE-001"

        # NEW: Check if rule applies to this case based on product/segment/channel/geography
        if not ConditionalRuleEvaluator._rule_applies_to_case(logs, rule):
            if debug_case:
                logger.info(f"[ConditionalRuleEvaluator] CASE-001: Rule {rule.get('id')} does not apply to this case")
            return None  # Skip this rule - not applicable to this case

        condition_logic = rule.get('condition_logic')

        # Parse condition_logic (could be string or dict)
        if isinstance(condition_logic, str):
            try:
                condition_logic = json.loads(condition_logic)
            except json.JSONDecodeError:
                # Not valid JSON, skip this rule
                if debug_case:
                    logger.warning(f"[ConditionalRuleEvaluator] CASE-001: Rule {rule.get('id')} has invalid JSON in condition_logic")
                return None

        if not isinstance(condition_logic, dict):
            return None

        condition = condition_logic.get('condition')
        then_clause = condition_logic.get('then')

        if not condition or not then_clause:
            return None

        # Build aggregated log data for the case (combines all extended fields from all logs)
        log_data = ConditionalRuleEvaluator._aggregate_log_data(logs)

        # Evaluate condition
        try:
            condition_met = ConditionalRuleEvaluator._evaluate_condition(condition, log_data)

            if debug_case and rule.get('id') == 1:
                logger.info(f"[ConditionalRuleEvaluator] CASE-001: Rule 1 condition evaluation:")
                logger.info(f"  - Condition: {condition}")
                logger.info(f"  - loan_amount_sanctioned in log_data: {log_data.get('loan_amount_sanctioned')}")
                logger.info(f"  - Condition met: {condition_met}")

        except KeyError as e:
            # Required field missing - log warning and skip rule (per user decision)
            # User feedback: "missing fields must be counted in data cleaning before deviation detection starts"
            # Do NOT return missing_core_field as a deviation
            if debug_case:
                logger.warning(f"[ConditionalRuleEvaluator] CASE-001: Rule {rule.get('id')} missing field {str(e)}")
            else:
                # Only log once per rule
                logger.debug(f"[ConditionalRuleEvaluator] {case_id}: Rule {rule.get('id')} skipped - missing field {str(e)}")

            # Return None to skip this rule evaluation
            return None

        # If condition is met, check if requirement is satisfied
        if condition_met:
            if debug_case and rule.get('id') == 1:
                logger.info(f"[ConditionalRuleEvaluator] CASE-001: Rule 1 condition MET, checking then clause")

            deviation = ConditionalRuleEvaluator._check_then_clause(
                case_id, logs, log_data, rule, condition_logic, then_clause
            )

            if debug_case and rule.get('id') == 1:
                logger.info(f"[ConditionalRuleEvaluator] CASE-001: Rule 1 deviation result: {deviation is not None}")

            return deviation

        return None

    @staticmethod
    def _evaluate_condition(condition: Dict[str, Any], log_data: Dict[str, Any]) -> bool:
        """
        Evaluate a single condition or nested conditions.

        Args:
            condition: The condition to evaluate
            log_data: Aggregated log data for the case

        Returns:
            True if condition is met, False otherwise

        Raises:
            KeyError: If required field is missing in log data
        """
        # Handle logical operators (AND, OR, NOT)
        if 'operator' in condition and condition['operator'] in ['AND', 'OR', 'NOT']:
            return ConditionalRuleEvaluator._evaluate_logical_condition(condition, log_data)

        # NEW: Handle calculations (e.g., LTV = loan_amount / collateral_value)
        if 'calculation' in condition:
            calculated_value = ConditionalRuleEvaluator._evaluate_calculation(
                condition['calculation'], log_data
            )
            operator = condition.get('operator')
            compare_value = condition.get('value')

            if operator and compare_value is not None:
                op_func = ConditionalRuleEvaluator.SUPPORTED_OPERATORS.get(operator)
                if not op_func:
                    return False
                try:
                    return op_func(calculated_value, compare_value)
                except (TypeError, ValueError):
                    return False
            return False

        # Handle comparison operators
        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')

        if not field or not operator:
            return False

        # Check if field exists in log data
        if field not in log_data:
            raise KeyError(f"Required field '{field}' not found in log data")

        actual_value = log_data[field]

        # Handle None values
        if actual_value is None:
            return False

        # Type conversion if needed (handle string representations of numbers)
        if isinstance(value, (int, float)) and isinstance(actual_value, str):
            try:
                actual_value = float(actual_value)
            except ValueError:
                return False

        # Apply operator
        op_func = ConditionalRuleEvaluator.SUPPORTED_OPERATORS.get(operator)
        if not op_func:
            return False

        try:
            return op_func(actual_value, value)
        except (TypeError, ValueError):
            # Type mismatch or comparison error
            return False

    @staticmethod
    def _evaluate_logical_condition(condition: Dict[str, Any], log_data: Dict[str, Any]) -> bool:
        """
        Evaluate AND/OR/NOT logical conditions.

        Args:
            condition: Logical condition with operator and sub-conditions
            log_data: Aggregated log data

        Returns:
            Boolean result of logical evaluation
        """
        operator = condition.get('operator')
        conditions = condition.get('conditions', [])

        if operator == 'AND':
            return all(ConditionalRuleEvaluator._evaluate_condition(c, log_data) for c in conditions)
        elif operator == 'OR':
            return any(ConditionalRuleEvaluator._evaluate_condition(c, log_data) for c in conditions)
        elif operator == 'NOT':
            if len(conditions) > 0:
                return not ConditionalRuleEvaluator._evaluate_condition(conditions[0], log_data)
            return False

        return False

    @staticmethod
    def _check_then_clause(
        case_id: str,
        logs: List[Dict[str, Any]],
        log_data: Dict[str, Any],
        rule: Dict[str, Any],
        condition_logic: Dict[str, Any],
        then_clause: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Check if the 'then' requirement is satisfied.

        Args:
            case_id: Case ID
            logs: All logs for the case
            log_data: Aggregated log data
            rule: The rule being evaluated
            condition_logic: Full condition logic for context
            then_clause: The 'then' clause specifying requirements

        Returns:
            Deviation dict if requirement not satisfied, None otherwise
        """
        # Get step names performed (lowercase for case-insensitive matching)
        step_names = [log['step_name'].lower() for log in logs]

        # Check for required single step
        if 'require_step' in then_clause:
            required_step = then_clause['require_step']

            # Phase 4 Enhancement: Use fuzzy matching with alternatives
            alternatives = then_clause.get('require_step_alternatives', [])
            if not ConditionalRuleEvaluator._step_matches_with_alternatives(
                required_step, step_names, alternatives
            ):
                # Extract case context from log_data (if available)
                loan_amount = log_data.get('loan_amount') or log_data.get('loan_amount_sanctioned')
                customer_segment = log_data.get('customer_segment')
                product_type = log_data.get('product_type')

                return {
                    'case_id': case_id,
                    'officer_id': logs[0].get('officer_id', 'unknown'),
                    'timestamp': logs[0].get('timestamp'),
                    'deviation_type': 'conditional_approval_missing',
                    'severity': then_clause.get('severity', rule.get('severity', 'high')),
                    'description': f'Conditional rule violated: {required_step} missing',
                    'expected_behavior': f'When {ConditionalRuleEvaluator._format_condition(condition_logic["condition"])}, {required_step} is required',
                    'actual_behavior': f'{required_step} step not found in workflow',

                    # Rule Context (NEW)
                    'rule_id': ConditionalRuleEvaluator._get_rule_id_for_db(rule),
                    'rule_description': rule.get('rule_description'),
                    'rule_type': rule.get('rule_type'),
                    'rule_severity': rule.get('severity'),

                    # Case Context (NEW)
                    'loan_amount': loan_amount,
                    'customer_segment': customer_segment,
                    'product_type': product_type,

                    'context': {
                        'rule_id': rule.get('id'),
                        'rule_description': rule.get('rule_description'),
                        'condition': condition_logic['condition'],
                        'log_data_sample': {k: v for k, v in log_data.items() if k in ['loan_amount_sanctioned', 'credit_score_bureau', 'emi_to_income_ratio', 'collateral_type', 'product_type']},
                        'required_step': required_step,
                        'steps_performed': step_names
                    }
                }

        # Check for required multiple steps
        if 'require_steps' in then_clause:
            required_steps = then_clause['require_steps']
            missing_steps = []

            for required_step in required_steps:
                # Phase 4 Enhancement: Use fuzzy matching
                if not ConditionalRuleEvaluator._step_matches_with_alternatives(
                    required_step, step_names, None
                ):
                    missing_steps.append(required_step)

            if missing_steps:
                # Extract case context from log_data (if available)
                loan_amount = log_data.get('loan_amount') or log_data.get('loan_amount_sanctioned')
                customer_segment = log_data.get('customer_segment')
                product_type = log_data.get('product_type')

                return {
                    'case_id': case_id,
                    'officer_id': logs[0].get('officer_id', 'unknown'),
                    'timestamp': logs[0].get('timestamp'),
                    'deviation_type': 'conditional_approval_missing',
                    'severity': then_clause.get('severity', rule.get('severity', 'high')),
                    'description': f'Conditional rule violated: {", ".join(missing_steps)} missing',
                    'expected_behavior': f'When {ConditionalRuleEvaluator._format_condition(condition_logic["condition"])}, all of [{", ".join(required_steps)}] are required',
                    'actual_behavior': f'Missing steps: {", ".join(missing_steps)}',

                    # Rule Context (NEW)
                    'rule_id': ConditionalRuleEvaluator._get_rule_id_for_db(rule),
                    'rule_description': rule.get('rule_description'),
                    'rule_type': rule.get('rule_type'),
                    'rule_severity': rule.get('severity'),

                    # Case Context (NEW)
                    'loan_amount': loan_amount,
                    'customer_segment': customer_segment,
                    'product_type': product_type,

                    'context': {
                        'rule_id': rule.get('id'),
                        'rule_description': rule.get('rule_description'),
                        'condition': condition_logic['condition'],
                        'log_data_sample': {k: v for k, v in log_data.items() if k in ['loan_amount_sanctioned', 'credit_score_bureau', 'emi_to_income_ratio', 'collateral_type', 'product_type']},
                        'required_steps': required_steps,
                        'missing_steps': missing_steps,
                        'steps_performed': step_names
                    }
                }

        # Phase 4 Enhancement: Check for block_step action (e.g., mandate validation)
        if 'action' in then_clause and then_clause['action'] == 'block_step':
            blocked_step = then_clause.get('blocked_step')
            if blocked_step:
                # Check if blocked step was performed (it shouldn't have been)
                alternatives = then_clause.get('blocked_step_alternatives', [])
                if ConditionalRuleEvaluator._step_matches_with_alternatives(
                    blocked_step, step_names, alternatives
                ):
                    # Extract case context
                    loan_amount = log_data.get('loan_amount') or log_data.get('loan_amount_sanctioned')
                    customer_segment = log_data.get('customer_segment')
                    product_type = log_data.get('product_type')

                    return {
                        'case_id': case_id,
                        'officer_id': logs[0].get('officer_id', 'unknown'),
                        'timestamp': logs[0].get('timestamp'),
                        'deviation_type': 'precondition_violation',
                        'severity': then_clause.get('severity', rule.get('severity', 'critical')),
                        'description': f'Pre-condition not met: {blocked_step} proceeded despite condition violation',
                        'expected_behavior': f'When {ConditionalRuleEvaluator._format_condition(condition_logic["condition"])}, {blocked_step} should be blocked',
                        'actual_behavior': f'{blocked_step} was performed despite unmet condition',

                        # Rule Context
                        'rule_id': ConditionalRuleEvaluator._get_rule_id_for_db(rule),
                        'rule_description': rule.get('rule_description'),
                        'rule_type': rule.get('rule_type'),
                        'rule_severity': rule.get('severity'),

                        # Case Context
                        'loan_amount': loan_amount,
                        'customer_segment': customer_segment,
                        'product_type': product_type,

                        'context': {
                            'rule_id': rule.get('id'),  # Keep string ID in context for reference
                            'rule_description': rule.get('rule_description'),
                            'condition': condition_logic['condition'],
                            'log_data_sample': {k: v for k, v in log_data.items() if k in ['mandate_status', 'loan_amount_sanctioned', 'product_type']},
                            'blocked_step': blocked_step,
                            'steps_performed': step_names
                        }
                    }

        return None

    @staticmethod
    def _step_matches_with_alternatives(
        required_step: str,
        step_names: List[str],
        alternatives: List[str] = None
    ) -> bool:
        """
        Phase 4 Enhancement: Check if required step exists using fuzzy matching and alternatives.

        Args:
            required_step: Primary required step name
            step_names: List of actual step names from logs
            alternatives: Optional list of alternative step names

        Returns:
            True if step found (with fuzzy matching)
        """
        from difflib import SequenceMatcher

        # Normalize function (same as SequenceChecker)
        def normalize(name):
            import re
            name = re.sub(r'^(?:Step\s+)?\d+[\.\:\-\)]\s*', '', name, flags=re.IGNORECASE)
            name = re.sub(r'\([^)]*\)', '', name)
            name = re.sub(r'\s*\(Step\s+\d+\)\s*', '', name, flags=re.IGNORECASE)
            name = name.lower()
            name = re.sub(r'[^\w\s]', ' ', name)
            name = re.sub(r'\s+', ' ', name)
            return name.strip()

        # Check primary step name
        norm_required = normalize(required_step)
        for actual_step in step_names:
            norm_actual = normalize(actual_step)

            # Exact match after normalization
            if norm_required == norm_actual:
                return True

            # Fuzzy match
            similarity = SequenceMatcher(None, norm_required, norm_actual).ratio()
            if similarity >= 0.75:
                return True

        # Check alternatives if provided
        if alternatives:
            for alt_step in alternatives:
                norm_alt = normalize(alt_step)
                for actual_step in step_names:
                    norm_actual = normalize(actual_step)

                    # Exact match
                    if norm_alt == norm_actual:
                        return True

                    # Fuzzy match
                    similarity = SequenceMatcher(None, norm_alt, norm_actual).ratio()
                    if similarity >= 0.75:
                        return True

        return False

    @staticmethod
    def _aggregate_log_data(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate all extended fields from logs into single dict.
        Takes the first non-None value for each field.

        Args:
            logs: List of workflow logs for a case

        Returns:
            Dictionary with all available fields
        """
        aggregated = {}
        for log in logs:
            for key, value in log.items():
                # Only add if value is not None and key not already in aggregated
                if value is not None and key not in aggregated:
                    aggregated[key] = value
        return aggregated

    @staticmethod
    def _evaluate_calculation(calc: Dict[str, Any], log_data: Dict[str, Any]) -> float:
        """
        NEW METHOD: Evaluate a calculation expression.

        Example calc format:
        {
            "function": "DIVIDE",
            "args": [
                {"field": "loan_amount"},
                {"field": "collateral_value"}
            ]
        }

        Args:
            calc: Calculation specification with function and args
            log_data: Aggregated log data containing field values

        Returns:
            Result of calculation as float

        Raises:
            KeyError: If required field is missing
        """
        function = calc.get('function')
        args = calc.get('args', [])

        if not function or function not in ConditionalRuleEvaluator.SUPPORTED_FUNCTIONS:
            return 0

        # Resolve arguments (can be fields, literal values, or nested calculations)
        resolved_args = []
        for arg in args:
            if 'field' in arg:
                field_name = arg['field']
                if field_name not in log_data:
                    raise KeyError(f"Required field '{field_name}' not found in log data")
                field_value = log_data[field_name]
                # Convert to float if possible
                if isinstance(field_value, str):
                    try:
                        field_value = float(field_value)
                    except ValueError:
                        field_value = 0
                resolved_args.append(field_value)
            elif 'value' in arg:
                resolved_args.append(arg['value'])
            elif 'calculation' in arg:
                # Nested calculation
                resolved_args.append(
                    ConditionalRuleEvaluator._evaluate_calculation(arg['calculation'], log_data)
                )

        # Apply function
        func = ConditionalRuleEvaluator.SUPPORTED_FUNCTIONS[function]
        try:
            return func(*resolved_args)
        except Exception:
            return 0

    @staticmethod
    def _rule_applies_to_case(logs: List[Dict[str, Any]], rule: Dict[str, Any]) -> bool:
        """
        NEW METHOD: Check if rule applies based on product/segment/channel/geography.

        Args:
            logs: All logs for the case
            rule: The rule being evaluated

        Returns:
            True if rule applies to this case, False otherwise
        """
        log_data = ConditionalRuleEvaluator._aggregate_log_data(logs)

        # Check product type
        product_types = rule.get('product_types', ['All'])
        if product_types and 'All' not in product_types:
            case_product = log_data.get('product_type')
            if case_product and case_product not in product_types:
                return False

        # Check customer segment
        customer_segments = rule.get('customer_segments', ['All'])
        if customer_segments and 'All' not in customer_segments:
            case_segment = log_data.get('customer_segment')
            if case_segment and case_segment not in customer_segments:
                return False

        # Check channel
        channels = rule.get('channels', ['All'])
        if channels and 'All' not in channels:
            case_channel = log_data.get('channel')
            if case_channel and case_channel not in channels:
                return False

        # Check geography
        geography = rule.get('geography', ['All'])
        if geography and 'All' not in geography:
            case_geo = log_data.get('geo_code') or log_data.get('region')
            if case_geo and case_geo not in geography:
                return False

        return True  # Rule applies

    @staticmethod
    def _format_condition(condition: Dict[str, Any]) -> str:
        """
        Format condition as human-readable string for deviation messages.

        Args:
            condition: The condition to format

        Returns:
            Human-readable condition string
        """
        if 'operator' in condition and condition['operator'] in ['AND', 'OR', 'NOT']:
            # Logical condition
            operator = condition['operator']
            conditions = condition.get('conditions', [])
            formatted = [ConditionalRuleEvaluator._format_condition(c) for c in conditions]

            if operator == 'NOT':
                return f"NOT ({formatted[0]})" if formatted else "NOT (?)"
            else:
                return f"({' ' + operator + ' '.join(formatted)})"
        else:
            # Simple condition
            field = condition.get('field', '?')
            operator = condition.get('operator', '?')
            value = condition.get('value', '?')
            return f"{field} {operator} {value}"
