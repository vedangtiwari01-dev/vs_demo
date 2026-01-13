"""
Rule Parser Module

Centralized rule parsing to extract structured requirements from SOP rules.
This module eliminates hardcoded assumptions by extracting validation logic
directly from the SOP rules provided by the user.

Design Principle: Parse structured rule fields first (threshold_value, condition_logic),
fall back to NLP extraction only if needed.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Set

logger = logging.getLogger(__name__)


class RuleParser:
    """
    Centralized parser for extracting structured requirements from SOP rules.
    All checkers should use this class instead of hardcoded assumptions.
    """

    @staticmethod
    def extract_sequence_steps(rules: List[Dict]) -> Optional[List[str]]:
        """
        Extract ordered step names from sequence rules.

        Args:
            rules: List of all SOP rules

        Returns:
            Ordered list of step names if sequence rules exist, None otherwise

        Logic:
            1. Filter rules with rule_type='sequence'
            2. Sort by step_number field
            3. Extract step names from rule_description or required_fields
            4. Return None if no valid sequence found (triggers skip validation)
        """
        sequence_rules = [r for r in rules if r.get('rule_type') == 'sequence']

        if not sequence_rules:
            return None

        # Try to extract steps from step_number ordering
        steps_with_numbers = []
        for rule in sequence_rules:
            step_number = rule.get('step_number')
            if step_number is not None:
                # Try to extract step name from rule_description
                desc = rule.get('rule_description', '')
                # Look for patterns like "Step 1: Application Received" or "1. Application Received"
                step_name_match = re.search(r'(?:Step\s+\d+:\s*|^\d+\.\s*)(.+?)(?:\s+must|\s+should|$)', desc, re.IGNORECASE)
                if step_name_match:
                    step_name = step_name_match.group(1).strip()
                    steps_with_numbers.append((step_number, step_name))
                else:
                    # If no clear pattern, use the whole description
                    steps_with_numbers.append((step_number, desc.strip()))

        if steps_with_numbers:
            # Sort by step_number and extract step names
            steps_with_numbers.sort(key=lambda x: x[0])
            return [step_name for _, step_name in steps_with_numbers]

        # No explicit sequence found - return None to skip validation
        return None

    @staticmethod
    def extract_document_requirements(rules: List[Dict]) -> Dict[str, Any]:
        """
        Extract mandatory documents and their conditions from documentation rules.

        Args:
            rules: List of all SOP rules

        Returns:
            Dict with:
                - mandatory_docs: Set of required document types
                - conditional_docs: Dict of {condition: [doc_types]}
                - product_specific: Dict of {product_type: [doc_types]}

        Returns empty sets/dicts if no documentation rules exist.
        """
        doc_rules = [r for r in rules if r.get('rule_type') == 'documentation']

        result = {
            'mandatory_docs': set(),
            'conditional_docs': {},
            'product_specific': {}
        }

        if not doc_rules:
            return result

        for rule in doc_rules:
            desc = rule.get('rule_description', '').lower()

            # Try to extract from threshold_value if structured
            threshold = rule.get('threshold_value')
            if isinstance(threshold, dict) and 'documents' in threshold:
                docs = threshold['documents']
                if isinstance(docs, list):
                    result['mandatory_docs'].update(docs)
                continue

            # Try to extract from required_fields
            req_fields = rule.get('required_fields', [])
            if req_fields and isinstance(req_fields, list):
                result['mandatory_docs'].update(req_fields)
                continue

            # Fall back to NLP extraction from description
            # Common document keywords
            doc_keywords = {
                'income_proof': ['income proof', 'income document', 'salary slip', 'itr'],
                'identity_proof': ['identity proof', 'id proof', 'aadhaar', 'pan', 'passport'],
                'address_proof': ['address proof', 'utility bill', 'residence proof'],
                'bank_statement': ['bank statement', 'account statement'],
                'employment_proof': ['employment proof', 'employment letter', 'appointment letter'],
                'collateral_docs': ['property papers', 'title deed', 'encumbrance certificate'],
                'legal_clearance': ['legal clearance', 'legal opinion', 'legal vetting'],
            }

            for doc_type, keywords in doc_keywords.items():
                if any(keyword in desc for keyword in keywords):
                    # Check if it's product-specific
                    product_types = rule.get('product_types', [])
                    if product_types and product_types != ['All']:
                        for product in product_types:
                            if product not in result['product_specific']:
                                result['product_specific'][product] = set()
                            result['product_specific'][product].add(doc_type)
                    else:
                        result['mandatory_docs'].add(doc_type)

        return result

    @staticmethod
    def extract_approval_requirements(rules: List[Dict]) -> Dict[str, Any]:
        """
        Extract which approvals are required and when.

        Args:
            rules: List of all SOP rules

        Returns:
            Dict with:
                - required_approvals: List of required approval step names
                - conditional_approvals: Dict of {condition: approval_step}
                - amount_thresholds: Dict of {threshold_amount: approval_level}

        Returns empty if no approval rules exist.
        """
        approval_rules = [r for r in rules if r.get('rule_type') == 'approval']

        result = {
            'required_approvals': [],
            'conditional_approvals': {},
            'amount_thresholds': {}
        }

        if not approval_rules:
            return result

        for rule in approval_rules:
            desc = rule.get('rule_description', '')

            # Check for conditional logic
            condition_logic = rule.get('condition_logic')
            if condition_logic:
                # This is a conditional approval
                if isinstance(condition_logic, dict):
                    then_action = condition_logic.get('then', {})
                    required_step = then_action.get('require_step') or then_action.get('require_steps')
                    if required_step:
                        condition_desc = str(condition_logic.get('condition', 'condition'))
                        result['conditional_approvals'][condition_desc] = required_step
                continue

            # Check for amount thresholds
            threshold = rule.get('threshold_value')
            if threshold:
                # Try to extract approval step name from description
                approval_match = re.search(r'(manager|senior|branch|credit committee|head)\s+(approval|sanction)', desc, re.IGNORECASE)
                if approval_match:
                    approval_name = approval_match.group(0)
                    result['amount_thresholds'][float(threshold)] = approval_name
                continue

            # Unconditional required approval
            approval_match = re.search(r'(manager|senior|branch|credit committee|head)\s+(approval|sanction)', desc, re.IGNORECASE)
            if approval_match:
                result['required_approvals'].append(approval_match.group(0))

        return result

    @staticmethod
    def extract_kyc_requirements(rules: List[Dict]) -> Dict[str, Any]:
        """
        Extract KYC completion requirements.

        Args:
            rules: List of all SOP rules

        Returns:
            Dict with:
                - kyc_required_before: List of steps that require KYC completion
                - sanctions_action: Required action if sanctions hit ('reject', 'edd', 'escalate', None)
                - pep_requirements: Dict of PEP handling requirements
                - conditional: Whether KYC is conditionally required

        Returns None values if no kyc rules exist.
        """
        kyc_rules = [r for r in rules if r.get('rule_type') in ['kyc', 'aml']]

        result = {
            'kyc_required_before': [],
            'sanctions_action': None,
            'pep_requirements': {},
            'conditional': False
        }

        if not kyc_rules:
            return result

        for rule in kyc_rules:
            desc = rule.get('rule_description', '').lower()
            condition_logic = rule.get('condition_logic')

            # Check if KYC requirement is conditional
            if condition_logic:
                result['conditional'] = True
                if isinstance(condition_logic, dict):
                    then_action = condition_logic.get('then', {})
                    required_step = then_action.get('require_step')
                    if required_step and 'kyc' in required_step.lower():
                        result['kyc_required_before'].append(required_step)

            # Check for "KYC must be complete before X"
            if 'kyc' in desc and 'before' in desc:
                # Extract what step KYC must be complete before
                if 'approval' in desc:
                    result['kyc_required_before'].append('approval')
                if 'disbursement' in desc or 'disburse' in desc:
                    result['kyc_required_before'].append('disbursement')
                if 'sanction' in desc:
                    result['kyc_required_before'].append('sanction')

            # Sanctions handling
            if 'sanction' in desc and 'hit' in desc:
                if 'reject' in desc:
                    result['sanctions_action'] = 'reject'
                elif 'edd' in desc or 'enhanced' in desc:
                    result['sanctions_action'] = 'edd'
                elif 'escalate' in desc:
                    result['sanctions_action'] = 'escalate'

            # PEP handling
            if 'pep' in desc or 'politically exposed' in desc:
                if 'edd' in desc or 'enhanced' in desc:
                    result['pep_requirements']['edd_required'] = True
                if 'approval' in desc:
                    result['pep_requirements']['extra_approval_required'] = True
                if 'senior' in desc or 'compliance' in desc:
                    result['pep_requirements']['approval_level'] = 'senior'

        return result

    @staticmethod
    def extract_eligibility_thresholds(rules: List[Dict]) -> Dict[str, Any]:
        """
        Extract eligibility thresholds (age, tenor, LTV, credit score, etc.).

        Args:
            rules: List of all SOP rules

        Returns:
            Dict with threshold names and values, empty dict if no rules exist.
        """
        eligibility_rules = [r for r in rules if r.get('rule_type') in ['eligibility', 'credit_risk']]

        thresholds = {}

        if not eligibility_rules:
            return thresholds

        for rule in eligibility_rules:
            # Try structured threshold_value first
            threshold_val = rule.get('threshold_value')
            if threshold_val is not None:
                desc = rule.get('rule_description', '').lower()

                # Identify what this threshold is for
                if 'age' in desc:
                    if 'minimum' in desc or 'min' in desc:
                        thresholds['min_age'] = int(threshold_val)
                    elif 'maximum' in desc or 'max' in desc:
                        thresholds['max_age'] = int(threshold_val)
                elif 'tenor' in desc or 'tenure' in desc:
                    if 'maximum' in desc or 'max' in desc:
                        thresholds['max_tenor'] = int(threshold_val)
                elif 'ltv' in desc or 'loan to value' in desc or 'loan-to-value' in desc:
                    if 'maximum' in desc or 'max' in desc:
                        thresholds['max_ltv'] = float(threshold_val)
                elif 'credit score' in desc or 'cibil' in desc:
                    if 'minimum' in desc or 'min' in desc:
                        thresholds['min_credit_score'] = int(threshold_val)
                elif 'emi' in desc and 'income' in desc:
                    if 'maximum' in desc or 'max' in desc:
                        thresholds['max_emi_to_income'] = float(threshold_val)
                continue

            # Fall back to regex extraction from description
            desc = rule.get('rule_description', '')

            # Age pattern: "minimum age 21" or "age should be between 21 and 60"
            age_match = re.search(r'(?:minimum|min)\s+age\s+(?:of\s+)?(\d+)', desc, re.IGNORECASE)
            if age_match:
                thresholds['min_age'] = int(age_match.group(1))

            age_match = re.search(r'(?:maximum|max)\s+age\s+(?:of\s+)?(\d+)', desc, re.IGNORECASE)
            if age_match:
                thresholds['max_age'] = int(age_match.group(1))

            age_range = re.search(r'age\s+(?:should be\s+)?between\s+(\d+)\s+and\s+(\d+)', desc, re.IGNORECASE)
            if age_range:
                thresholds['min_age'] = int(age_range.group(1))
                thresholds['max_age'] = int(age_range.group(2))

            # Tenor pattern
            tenor_match = re.search(r'(?:maximum|max)\s+tenor\s+(?:of\s+)?(\d+)\s*(?:months|years)', desc, re.IGNORECASE)
            if tenor_match:
                tenor_val = int(tenor_match.group(1))
                if 'year' in desc.lower():
                    tenor_val *= 12
                thresholds['max_tenor'] = tenor_val

            # LTV pattern
            ltv_match = re.search(r'(?:maximum|max)\s+ltv\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*%?', desc, re.IGNORECASE)
            if ltv_match:
                ltv_val = float(ltv_match.group(1))
                if ltv_val > 1:  # If given as percentage
                    ltv_val /= 100
                thresholds['max_ltv'] = ltv_val

            # Credit score pattern
            score_match = re.search(r'(?:minimum|min)\s+(?:credit\s+score|cibil)\s+(?:of\s+)?(\d+)', desc, re.IGNORECASE)
            if score_match:
                thresholds['min_credit_score'] = int(score_match.group(1))

        return thresholds

    @staticmethod
    def extract_timing_constraints(rules: List[Dict]) -> List[Dict]:
        """
        Extract SLA/TAT requirements.

        Args:
            rules: List of all SOP rules

        Returns:
            List of timing constraints, empty list if no timing rules exist.
        """
        timing_rules = [r for r in rules if r.get('rule_type') == 'timing']

        constraints = []

        if not timing_rules:
            return constraints

        for rule in timing_rules:
            # Try structured temporal_constraint field first
            temporal = rule.get('temporal_constraint') or rule.get('timing_constraint')
            if temporal and isinstance(temporal, dict):
                constraints.append(temporal)
                continue

            # Fall back to parsing description
            desc = rule.get('rule_description', '')
            threshold = rule.get('threshold_value')

            if threshold:
                # Try to extract what the threshold is for
                constraint = {'max_hours': float(threshold)}

                # Identify the step or process
                step_match = re.search(r'(?:for|after|within)\s+([a-zA-Z\s]+?)(?:\s+step|\s+must|\s+should)', desc, re.IGNORECASE)
                if step_match:
                    constraint['step'] = step_match.group(1).strip()

                constraints.append(constraint)

        return constraints

    @staticmethod
    def extract_disbursement_preconditions(rules: List[Dict]) -> Dict[str, Any]:
        """
        Extract pre-disbursement requirements.

        Args:
            rules: List of all SOP rules

        Returns:
            Dict with:
                - required_steps: List of steps required before disbursement
                - mandate_required: Boolean
                - qc_required: Boolean
                - tolerance_amount: Float or None

        Returns default None/False values if no disbursement rules exist.
        """
        disbursement_rules = [r for r in rules if r.get('rule_type') == 'disbursement']

        result = {
            'required_steps': [],
            'mandate_required': False,
            'qc_required': False,
            'tolerance_percent': None
        }

        if not disbursement_rules:
            return result

        for rule in disbursement_rules:
            desc = rule.get('rule_description', '').lower()

            # Check for conditional logic
            condition_logic = rule.get('condition_logic')
            if condition_logic and isinstance(condition_logic, dict):
                then_action = condition_logic.get('then', {})
                required_step = then_action.get('require_step') or then_action.get('require_steps')
                if required_step:
                    if isinstance(required_step, list):
                        result['required_steps'].extend(required_step)
                    else:
                        result['required_steps'].append(required_step)

            # Check for "must complete X before disbursement"
            if 'before' in desc and 'disburse' in desc:
                if 'approval' in desc:
                    result['required_steps'].append('approval')
                if 'kyc' in desc:
                    result['required_steps'].append('kyc')
                if 'documentation' in desc or 'document' in desc:
                    result['required_steps'].append('documentation')

            # Check for mandate requirement
            if 'mandate' in desc or 'nach' in desc or 'emi setup' in desc:
                if 'required' in desc or 'must' in desc or 'should' in desc:
                    result['mandate_required'] = True

            # Check for QC requirement
            if 'qc' in desc or 'quality check' in desc or 'post disbursement' in desc:
                if 'required' in desc or 'must' in desc:
                    result['qc_required'] = True

            # Check for tolerance
            if 'tolerance' in desc or 'variance' in desc:
                threshold = rule.get('threshold_value')
                if threshold:
                    result['tolerance_percent'] = float(threshold)

        return result

    @staticmethod
    def extract_collection_schedule(rules: List[Dict]) -> Dict[int, str]:
        """
        Extract collection escalation schedule.

        Args:
            rules: List of all SOP rules

        Returns:
            Dict mapping DPD (days past due) to escalation action.
            Returns empty dict if no collection rules exist.
        """
        collection_rules = [r for r in rules if r.get('rule_type') in ['collection', 'restructuring']]

        schedule = {}

        if not collection_rules:
            return schedule

        for rule in collection_rules:
            desc = rule.get('rule_description', '')
            threshold = rule.get('threshold_value')

            # Try to extract DPD and action
            if threshold:
                dpd = int(threshold)

                # Identify the action
                desc_lower = desc.lower()
                if 'legal action' in desc_lower or 'suit' in desc_lower:
                    schedule[dpd] = 'legal_action'
                elif 'legal notice' in desc_lower or 'demand notice' in desc_lower:
                    schedule[dpd] = 'legal_notice'
                elif 'reminder' in desc_lower or 'follow up' in desc_lower:
                    schedule[dpd] = 'reminder'
                elif 'escalate' in desc_lower:
                    schedule[dpd] = 'escalation'
                continue

            # Pattern matching for "after X days, take Y action"
            dpd_match = re.search(r'(?:after|at|beyond)\s+(\d+)\s+days', desc, re.IGNORECASE)
            if dpd_match:
                dpd = int(dpd_match.group(1))

                desc_lower = desc.lower()
                if 'legal action' in desc_lower:
                    schedule[dpd] = 'legal_action'
                elif 'legal notice' in desc_lower:
                    schedule[dpd] = 'legal_notice'
                elif 'reminder' in desc_lower:
                    schedule[dpd] = 'reminder'

        return schedule

    @staticmethod
    def extract_regulatory_thresholds(rules: List[Dict]) -> Optional[Dict[str, Any]]:
        """
        Extract regulatory classification thresholds.

        Args:
            rules: List of all SOP rules

        Returns:
            Dict with classification thresholds if regulatory rules exist, None otherwise.
            Expected structure:
            {
                'standard': {'min_dpd': 0, 'max_dpd': 29, 'provisioning': 0.0025},
                'sub_standard': {'min_dpd': 30, 'max_dpd': 89, 'provisioning': 0.15},
                ...
            }
        """
        regulatory_rules = [r for r in rules if r.get('rule_type') == 'regulatory']

        if not regulatory_rules:
            return None

        # Look for rules with structured threshold_value
        for rule in regulatory_rules:
            threshold = rule.get('threshold_value')
            if threshold and isinstance(threshold, dict):
                # Check if it contains classification thresholds
                if any(key in threshold for key in ['standard', 'sub_standard', 'doubtful', 'loss', 'npa']):
                    return threshold

        # If no structured thresholds found, return None
        # System will skip regulatory validation
        return None

    @staticmethod
    def extract_collateral_requirements(rules: List[Dict]) -> Dict[str, Any]:
        """
        Extract collateral and LTV requirements.

        Args:
            rules: List of all SOP rules

        Returns:
            Dict with:
                - ltv_limits: Dict of {collateral_type: max_ltv}
                - valuation_age_days: Max age of valuation
                - security_required: Boolean

        Returns default None/False values if no collateral rules exist.
        """
        collateral_rules = [r for r in rules if r.get('rule_type') == 'collateral']

        result = {
            'ltv_limits': {},
            'valuation_age_days': None,
            'security_required': False
        }

        if not collateral_rules:
            return result

        for rule in collateral_rules:
            desc = rule.get('rule_description', '').lower()
            threshold = rule.get('threshold_value')

            # LTV extraction
            if 'ltv' in desc or 'loan to value' in desc or 'loan-to-value' in desc:
                if threshold:
                    ltv_val = float(threshold)
                    if ltv_val > 1:  # If given as percentage
                        ltv_val /= 100

                    # Check for collateral type specificity
                    product_types = rule.get('product_types', [])
                    if product_types and product_types != ['All']:
                        for product in product_types:
                            result['ltv_limits'][product] = ltv_val
                    else:
                        result['ltv_limits']['default'] = ltv_val

            # Valuation age
            if 'valuation' in desc and ('age' in desc or 'old' in desc or 'recent' in desc):
                if threshold:
                    result['valuation_age_days'] = int(threshold)
                else:
                    # Try to extract from description
                    days_match = re.search(r'(\d+)\s+days?', desc)
                    months_match = re.search(r'(\d+)\s+months?', desc)
                    if days_match:
                        result['valuation_age_days'] = int(days_match.group(1))
                    elif months_match:
                        result['valuation_age_days'] = int(months_match.group(1)) * 30

            # Security creation requirement
            if 'security' in desc and ('create' in desc or 'register' in desc):
                if 'required' in desc or 'must' in desc:
                    result['security_required'] = True

        return result
