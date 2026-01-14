"""
Test Rule Extraction - Direct LLM Testing

This script tests rule extraction by directly calling Claude with our prompt,
bypassing the backend to isolate prompt engineering issues.

It tests each type of rule individually to identify which rules are not being extracted correctly.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from anthropic import Anthropic

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.config import settings

# ============================================================================
# IMPROVED PROMPT - Clear Structure with Inline Examples
# ============================================================================

IMPROVED_EXTRACTION_PROMPT = """You are an expert at analyzing Standard Operating Procedures (SOPs) and extracting structured compliance rules.

Your task: Extract ALL rules from the SOP document and return them as a JSON array.

# OUTPUT FORMAT

Return a JSON object with this EXACT structure:

```json
{
  "rules": [
    {
      "rule_type": "sequence|approval|timing|eligibility|credit_risk|kyc|aml|documentation|collateral|disbursement|post_disbursement_qc|collection|restructuring|regulatory|data_quality|operational",
      "rule_description": "Clear description of the rule",
      "step_number": 5,
      "severity": "critical|high|medium|low",
      "threshold_value": 10000,
      "field_dependencies": ["loan_amount_sanctioned", "collateral_value"],
      "condition_logic": {
        "condition": {"field": "loan_amount", "operator": ">=", "value": 10000},
        "then": {"require_step": "Manager Approval", "severity": "critical"}
      },
      "product_types": ["All"],
      "customer_segments": ["All"],
      "channels": ["All"],
      "geography": ["All"],
      "exceptions": [],
      "calculation_formula": "LTV = loan_amount / collateral_value",
      "temporal_constraint": {"step_a": "Risk Assessment", "step_b": "Approval", "max_hours": 48},
      "regulatory_reference": null,
      "timing_constraint": "within 48 hours"
    }
  ]
}
```

**IMPORTANT - Keep Output Compact:**
- **OMIT fields that are null or empty** (don't include them at all)
- Only include optional fields (temporal_constraint, calculation_formula, regulatory_reference, timing_constraint, exceptions) when they have actual values
- ALWAYS include: rule_type, rule_description, severity, field_dependencies
- Include threshold_value only if the rule has a numeric threshold

# CRITICAL RULES FOR EXTRACTION

## Rule 1: ALWAYS Extract threshold_value

**What it is:** The NUMERIC value in the rule (age limits, amounts, ratios, percentages)

**Examples:**
- "Minimum Age: 21 years" → threshold_value: 21
- "Maximum LTV: 80%" → threshold_value: 0.8 (decimal format for percentages)
- "Loans above $10,000" → threshold_value: 10000
- "EMI ratio max 55%" → threshold_value: 0.55
- "Credit score minimum 650" → threshold_value: 650

**VALIDATION:** Age thresholds MUST be 18-100. If you extract 40000 as age, YOU ARE WRONG - that's a loan amount!

## Rule 2: ALWAYS Extract field_dependencies

**What it is:** List of ALL data fields this rule needs to check

**Examples:**
- "Minimum age 21" → field_dependencies: ["customer_age"]
- "LTV must not exceed 80%" → field_dependencies: ["loan_amount_sanctioned", "collateral_value"]
- "EMI ratio below 55%" → field_dependencies: ["emi_to_income_ratio"]
- "Credit score above 650 for loans over $500K" → field_dependencies: ["credit_score_bureau", "loan_amount_sanctioned"]
- "KYC must be completed before approval" → field_dependencies: ["step_name", "kyc_status"]

## Rule 3: ALWAYS Extract condition_logic for conditional rules

**What it is:** Structured IF-THEN logic for rules that have conditions

**Format:**
```json
{
  "condition": {
    "field": "loan_amount_sanctioned",
    "operator": ">=",
    "value": 1000000
  },
  "then": {
    "require_step": "Regional Credit Manager Approval",
    "severity": "critical"
  }
}
```

**When to use:**
- Approval rules with amount thresholds: "Loans above $1M require Regional Manager approval"
- Risk-based rules: "Credit score below 650 requires exception"
- Conditional requirements: "Self-employed customers must provide ITR"

## Rule 4: Extract product_types, customer_segments, channels if mentioned

**Examples:**
- "For Home Loans, property valuation is mandatory" → product_types: ["Home Loan"]
- "Priority customers can have EMI ratio up to 60%" → customer_segments: ["Priority"]
- "Digital channel loans limited to $3M" → channels: ["Digital"]
- If NOT mentioned, use: ["All"]

## Rule 5: Extract exceptions if mentioned

**What it is:** Exception cases or special conditions

**Examples:**
- "Age limit 65, except existing premium customers can be 68" → exceptions: [{"condition": "existing premium customer", "override": "maximum age 68"}]
- "Credit score minimum 650, except with strong collateral" → exceptions: [{"condition": "strong collateral", "override": "score below 650 acceptable"}]

# SPECIFIC EXTRACTION RULES BY TYPE

## A. ELIGIBILITY RULES

Extract as SEPARATE rules (do NOT combine):

**Age Rules:**
```json
{
  "rule_type": "eligibility",
  "rule_description": "Minimum age requirement is 21 years",
  "threshold_value": 21,
  "field_dependencies": ["customer_age"],
  "condition_logic": {
    "condition": {"field": "customer_age", "operator": "<", "value": 21},
    "then": {"action": "reject", "reason": "Below minimum age"}
  },
  "severity": "critical",
  "product_types": ["All"],
  "customer_segments": ["All"]
}
```

Note: No null fields included - only fields with actual values.

**Income Rules:**
```json
{
  "rule_type": "eligibility",
  "rule_description": "Minimum monthly income for salaried customers is INR 25,000",
  "threshold_value": 25000,
  "field_dependencies": ["monthly_income", "customer_type"],
  "condition_logic": {
    "condition": {
      "operator": "AND",
      "conditions": [
        {"field": "customer_type", "operator": "==", "value": "Salaried"},
        {"field": "monthly_income", "operator": "<", "value": 25000}
      ]
    },
    "then": {"action": "reject"}
  },
  "customer_segments": ["Salaried"],
  "severity": "critical"
}
```

## B. CREDIT RISK RULES

**EMI-to-Income Rules:**
```json
{
  "rule_type": "credit_risk",
  "rule_description": "Maximum EMI-to-Income ratio is 55% for salaried customers",
  "threshold_value": 0.55,
  "field_dependencies": ["emi_to_income_ratio", "customer_type"],
  "condition_logic": {
    "condition": {
      "operator": "AND",
      "conditions": [
        {"field": "customer_type", "operator": "==", "value": "Salaried"},
        {"field": "emi_to_income_ratio", "operator": ">", "value": 0.55}
      ]
    },
    "then": {"action": "flag_violation", "severity": "high"}
  },
  "customer_segments": ["Salaried"],
  "exceptions": [{"condition": "income > INR 100,000/month", "override": "60% EMI ratio acceptable"}],
  "severity": "high"
}
```

**Credit Score Rules:**
```json
{
  "rule_type": "credit_risk",
  "rule_description": "Minimum credit score requirement is 650",
  "threshold_value": 650,
  "field_dependencies": ["credit_score_bureau"],
  "condition_logic": {
    "condition": {"field": "credit_score_bureau", "operator": "<", "value": 650},
    "then": {"require_step": "Credit Committee Approval", "severity": "critical"}
  },
  "severity": "critical"
}
```

## C. APPROVAL AUTHORITY RULES

**Amount-Based Approval:**
```json
{
  "rule_type": "approval",
  "rule_description": "Loans above INR 1,000,000 require Regional Credit Manager approval",
  "threshold_value": 1000000,
  "field_dependencies": ["loan_amount_sanctioned"],
  "condition_logic": {
    "condition": {"field": "loan_amount_sanctioned", "operator": ">", "value": 1000000},
    "then": {"require_step": "Credit Approval (Level 2 - Regional Credit Manager)", "severity": "critical"}
  },
  "severity": "critical"
}
```

## D. SEQUENCE RULES

**IMPORTANT:** If the SOP lists a mandatory workflow with numbered steps (Step 1, Step 2, etc.),
extract each step as a SEPARATE sequence rule:

```json
{
  "rule_type": "sequence",
  "rule_description": "Application Received and Registration is Step 1 in the mandatory workflow",
  "step_number": 1,
  "field_dependencies": ["step_name"],
  "severity": "critical",
  "product_types": ["All"]
}
```

**Dependency Rules (no step_number, but include temporal_constraint):**
```json
{
  "rule_type": "sequence",
  "rule_description": "KYC Verification must be completed before Credit Approval",
  "field_dependencies": ["step_name", "kyc_status"],
  "temporal_constraint": {
    "step_a": "Customer KYC and AML Verification",
    "step_b": "Credit Approval (Level 1 - Branch Manager)"
  },
  "severity": "critical",
  "product_types": ["All"]
}
```

Note: Omitted max_hours from temporal_constraint when not specified.

## E. TIMING RULES

```json
{
  "rule_type": "timing",
  "rule_description": "Post-Disbursement Quality Audit must be completed within 48 hours of disbursement",
  "timing_constraint": "within 48 hours",
  "threshold_value": 48,
  "field_dependencies": ["step_name", "timestamp"],
  "temporal_constraint": {
    "step_a": "Loan Disbursement",
    "step_b": "Post-Disbursement Quality Audit",
    "max_hours": 48
  },
  "severity": "critical",
  "product_types": ["All"]
}
```

Note: temporal_constraint is included here because it's a timing rule. For non-timing rules, omit it.

## F. COLLATERAL RULES

**LTV Rules:**
```json
{
  "rule_type": "collateral",
  "rule_description": "Maximum LTV for residential property is 75%",
  "threshold_value": 0.75,
  "calculation_formula": "LTV = loan_amount_sanctioned / collateral_value",
  "field_dependencies": ["loan_amount_sanctioned", "collateral_value", "collateral_type"],
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
      "value": 0.75
    },
    "then": {"action": "flag_violation", "severity": "high"}
  },
  "product_types": ["Property Backed Loan"],
  "severity": "high"
}
```

## G. REGULATORY RULES

**Customer Exposure Limits:**
```json
{
  "rule_type": "regulatory",
  "rule_description": "Maximum exposure to single customer (including group entities) is INR 15,000,000",
  "threshold_value": 15000000,
  "field_dependencies": ["total_customer_exposure", "customer_id", "group_entity_ids"],
  "condition_logic": {
    "condition": {"field": "total_customer_exposure", "operator": ">", "value": 15000000},
    "then": {"action": "flag_violation", "severity": "critical"}
  },
  "regulatory_reference": "Customer Exposure Limits Policy",
  "severity": "critical"
}
```

# EXTRACTION CHECKLIST

Before returning your JSON, verify:

1. ✅ EVERY numeric threshold has threshold_value field (ages, amounts, ratios)
2. ✅ EVERY rule has field_dependencies listing which fields it needs
3. ✅ Conditional rules have condition_logic
4. ✅ Age thresholds are 18-100 (NOT 40000 or other large numbers)
5. ✅ Percentages are in decimal format (0.55 for 55%, 0.8 for 80%)
6. ✅ Each workflow step is a separate rule (not combined)
7. ✅ Approval authority rules extracted for EACH threshold mentioned
8. ✅ All exceptions are captured in exceptions field
9. ✅ Customer exposure limits are classified as "regulatory" type (NOT "credit_risk")

# SOP DOCUMENT TO ANALYZE

{sop_text}

# YOUR RESPONSE

Return ONLY the JSON object starting with {"rules": [...]}.
No markdown code fences, no explanations, just the JSON.
"""

def format_extraction_prompt(sop_text: str) -> str:
    """
    Format the extraction prompt by replacing the SOP text placeholder.
    Using replace() instead of format() to avoid escaping all JSON braces.
    """
    return IMPROVED_EXTRACTION_PROMPT.replace("{sop_text}", sop_text)

# ============================================================================
# TEST CASES - Individual Rule Types + Full SOP
# ============================================================================

# Load full SOP for comprehensive testing
FULL_SOP_PATH = Path(__file__).parent.parent / "syn_sop.txt"

TEST_CASES = [
    {
        "name": "FULL SOP DOCUMENT (Load Test)",
        "sop_file": str(FULL_SOP_PATH),
        "is_full_sop": True,
        "expected_fields": {
            "minimum_rules": 50,  # Should extract at least 50 rules from full SOP
            "rule_types_required": ["sequence", "eligibility", "credit_risk", "approval", "collateral", "kyc", "regulatory"],
            "threshold_values_required": [21, 65, 0.55, 0.50, 650, 700, 1000000, 3000000, 10000000, 15000000],  # Key thresholds
            "all_rules_have_field_dependencies": True,
            "eligibility_rules_have_threshold": True
        }
    }
]

# ============================================================================
# Test Functions
# ============================================================================

def call_claude_direct(prompt: str, api_key: str, max_tokens: int = 16000) -> Dict[str, Any]:
    """
    Call Claude API directly with the prompt.

    Args:
        prompt: The extraction prompt
        api_key: Anthropic API key
        max_tokens: Maximum tokens for response

    Returns:
        Dict with 'text', 'input_tokens', 'output_tokens'
    """
    client = Anthropic(api_key=api_key)

    logger.info(f"Calling Claude with prompt length: {len(prompt)} chars")

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=max_tokens,
        temperature=0.0,  # Deterministic for testing
        system="You are an expert at analyzing compliance documents and extracting structured rules. Return ONLY valid JSON.",
        messages=[{"role": "user", "content": prompt}]
    )

    text_content = ""
    for block in response.content:
        if block.type == "text":
            text_content += block.text

    return {
        "text": text_content,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "stop_reason": response.stop_reason
    }

def validate_extracted_rules(rules: List[Dict[str, Any]], expected_fields: Dict[str, Any], is_full_sop: bool = False) -> Dict[str, Any]:
    """
    Validate that extracted rules contain expected fields.

    Args:
        rules: List of extracted rules
        expected_fields: Dict of expected field values
        is_full_sop: Whether this is a full SOP test (different validation logic)

    Returns:
        Validation report with pass/fail status
    """
    report = {
        "total_rules": len(rules),
        "checks": {},
        "passed": True,
        "missing_fields": [],
        "issues": []
    }

    # Full SOP validation (load test)
    if is_full_sop:
        # Check minimum rule count
        if "minimum_rules" in expected_fields:
            min_rules = expected_fields["minimum_rules"]
            report["checks"]["minimum_rules"] = {
                "expected_minimum": min_rules,
                "actual": len(rules),
                "passed": len(rules) >= min_rules
            }
            if len(rules) < min_rules:
                report["passed"] = False
                report["issues"].append(f"Only extracted {len(rules)} rules, expected at least {min_rules}")

        # Check required rule types present
        if "rule_types_required" in expected_fields:
            required_types = set(expected_fields["rule_types_required"])
            found_types = set(r.get("rule_type") for r in rules)
            missing_types = required_types - found_types

            report["checks"]["rule_types_coverage"] = {
                "required": list(required_types),
                "found": list(found_types),
                "missing": list(missing_types),
                "passed": len(missing_types) == 0
            }
            if missing_types:
                report["passed"] = False
                report["issues"].append(f"Missing rule types: {missing_types}")

        # Check key threshold values extracted
        if "threshold_values_required" in expected_fields:
            required_thresholds = set(expected_fields["threshold_values_required"])
            found_thresholds = set()
            for rule in rules:
                if rule.get("threshold_value") is not None:
                    found_thresholds.add(rule["threshold_value"])

            missing_thresholds = required_thresholds - found_thresholds
            report["checks"]["key_thresholds"] = {
                "required": list(required_thresholds),
                "found": list(found_thresholds),
                "missing": list(missing_thresholds),
                "passed": len(missing_thresholds) == 0
            }
            if missing_thresholds:
                report["passed"] = False
                report["issues"].append(f"Missing key threshold values: {missing_thresholds}")

        # Check all rules have field_dependencies
        if expected_fields.get("all_rules_have_field_dependencies"):
            rules_without_deps = [i for i, r in enumerate(rules) if not r.get("field_dependencies")]
            report["checks"]["all_have_field_dependencies"] = {
                "total_rules": len(rules),
                "rules_with_deps": len(rules) - len(rules_without_deps),
                "rules_without_deps": len(rules_without_deps),
                "passed": len(rules_without_deps) == 0
            }
            if rules_without_deps:
                report["passed"] = False
                report["issues"].append(f"{len(rules_without_deps)}/{len(rules)} rules missing field_dependencies")

        # Check eligibility rules have threshold_value
        if expected_fields.get("eligibility_rules_have_threshold"):
            eligibility_rules = [r for r in rules if r.get("rule_type") == "eligibility"]
            eligibility_without_threshold = [r for r in eligibility_rules if not r.get("threshold_value")]

            report["checks"]["eligibility_thresholds"] = {
                "total_eligibility_rules": len(eligibility_rules),
                "with_threshold": len(eligibility_rules) - len(eligibility_without_threshold),
                "without_threshold": len(eligibility_without_threshold),
                "passed": len(eligibility_without_threshold) == 0
            }
            if eligibility_without_threshold:
                report["passed"] = False
                report["issues"].append(f"{len(eligibility_without_threshold)}/{len(eligibility_rules)} eligibility rules missing threshold_value")

        return report

    # Individual test validation (existing logic)
    # Check threshold_value
    if "threshold_value" in expected_fields:
        expected_thresholds = set(expected_fields["threshold_value"])
        found_thresholds = set()
        for rule in rules:
            if rule.get("threshold_value") is not None:
                found_thresholds.add(rule["threshold_value"])

        missing = expected_thresholds - found_thresholds
        report["checks"]["threshold_value"] = {
            "expected": list(expected_thresholds),
            "found": list(found_thresholds),
            "missing": list(missing),
            "passed": len(missing) == 0
        }
        if missing:
            report["passed"] = False
            report["issues"].append(f"Missing threshold values: {missing}")

    # Check field_dependencies
    if "field_dependencies" in expected_fields:
        rules_with_deps = [r for r in rules if r.get("field_dependencies")]
        report["checks"]["field_dependencies"] = {
            "rules_with_field_dependencies": len(rules_with_deps),
            "total_rules": len(rules),
            "passed": len(rules_with_deps) > 0
        }
        if len(rules_with_deps) == 0:
            report["passed"] = False
            report["issues"].append("No rules have field_dependencies")

    # Check rule_type
    if "rule_type" in expected_fields:
        expected_types = set(expected_fields["rule_type"])
        found_types = set(r.get("rule_type") for r in rules)

        missing = expected_types - found_types
        report["checks"]["rule_type"] = {
            "expected": list(expected_types),
            "found": list(found_types),
            "missing": list(missing),
            "passed": len(missing) == 0
        }
        if missing:
            report["passed"] = False
            report["issues"].append(f"Missing rule types: {missing}")

    # Check condition_logic
    if expected_fields.get("condition_logic"):
        rules_with_logic = [r for r in rules if r.get("condition_logic")]
        report["checks"]["condition_logic"] = {
            "rules_with_condition_logic": len(rules_with_logic),
            "total_rules": len(rules),
            "passed": len(rules_with_logic) > 0
        }
        if len(rules_with_logic) == 0:
            report["passed"] = False
            report["issues"].append("No rules have condition_logic")

    # Check temporal_constraint
    if expected_fields.get("temporal_constraint"):
        rules_with_temporal = [r for r in rules if r.get("temporal_constraint")]
        report["checks"]["temporal_constraint"] = {
            "rules_with_temporal_constraint": len(rules_with_temporal),
            "total_rules": len(rules),
            "passed": len(rules_with_temporal) > 0
        }
        if len(rules_with_temporal) == 0:
            report["passed"] = False
            report["issues"].append("No rules have temporal_constraint")

    return report

def test_rule_extraction(test_case: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    """
    Test rule extraction for a single test case.

    Args:
        test_case: Test case with name, sop_text or sop_file, expected_fields
        api_key: Anthropic API key

    Returns:
        Test result with validation report
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"Testing: {test_case['name']}")
    logger.info(f"{'='*80}")

    # Load SOP text from file or use provided text
    if "sop_file" in test_case:
        logger.info(f"Loading SOP from file: {test_case['sop_file']}")
        try:
            with open(test_case['sop_file'], 'r', encoding='utf-8') as f:
                sop_text = f.read()
            logger.info(f"Loaded {len(sop_text)} characters from file")
        except FileNotFoundError:
            logger.error(f"SOP file not found: {test_case['sop_file']}")
            return {
                "test_case": test_case["name"],
                "error": f"File not found: {test_case['sop_file']}",
                "validation": {"passed": False}
            }
    else:
        sop_text = test_case["sop_text"]

    # Format prompt (use replace instead of format to avoid escaping JSON braces)
    prompt = format_extraction_prompt(sop_text)

    # Call Claude
    try:
        response = call_claude_direct(prompt, api_key)
        logger.info(f"Response received: {response['input_tokens']} input tokens, {response['output_tokens']} output tokens")

        # Parse JSON
        response_text = response["text"].strip()

        # Remove markdown code fences if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]

        result = json.loads(response_text)
        rules = result.get("rules", [])

        logger.info(f"Extracted {len(rules)} rules")

        is_full_sop = test_case.get("is_full_sop", False)

        # Print extracted rules (limit to 10 for full SOP)
        if is_full_sop:
            logger.info("\n=== FULL SOP EXTRACTION SUMMARY ===")

            # Count by rule type
            rule_type_counts = {}
            for rule in rules:
                rt = rule.get('rule_type', 'unknown')
                rule_type_counts[rt] = rule_type_counts.get(rt, 0) + 1

            logger.info(f"Rules by type:")
            for rt, count in sorted(rule_type_counts.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  {rt}: {count}")

            # Count rules with key fields
            with_threshold = sum(1 for r in rules if r.get('threshold_value') is not None)
            with_deps = sum(1 for r in rules if r.get('field_dependencies'))
            with_condition = sum(1 for r in rules if r.get('condition_logic'))

            logger.info(f"\nField coverage:")
            logger.info(f"  With threshold_value: {with_threshold}/{len(rules)} ({with_threshold/len(rules)*100:.1f}%)")
            logger.info(f"  With field_dependencies: {with_deps}/{len(rules)} ({with_deps/len(rules)*100:.1f}%)")
            logger.info(f"  With condition_logic: {with_condition}/{len(rules)} ({with_condition/len(rules)*100:.1f}%)")

            # Show first 10 rules
            logger.info(f"\n=== FIRST 10 RULES ===")
            for i, rule in enumerate(rules[:10], 1):
                logger.info(f"\nRule {i}:")
                logger.info(f"  Type: {rule.get('rule_type')}")
                logger.info(f"  Description: {rule.get('rule_description', '')[:80]}...")
                logger.info(f"  Threshold: {rule.get('threshold_value')}")
                logger.info(f"  Dependencies: {rule.get('field_dependencies')}")
        else:
            # Print all rules for individual tests
            for i, rule in enumerate(rules, 1):
                logger.info(f"\nRule {i}:")
                logger.info(f"  Type: {rule.get('rule_type')}")
                logger.info(f"  Description: {rule.get('rule_description', '')[:80]}...")
                logger.info(f"  Threshold Value: {rule.get('threshold_value')}")
                logger.info(f"  Field Dependencies: {rule.get('field_dependencies')}")
                logger.info(f"  Has Condition Logic: {rule.get('condition_logic') is not None}")
                logger.info(f"  Has Temporal Constraint: {rule.get('temporal_constraint') is not None}")

        # Validate
        validation = validate_extracted_rules(rules, test_case["expected_fields"], is_full_sop=is_full_sop)

        logger.info(f"\n{'='*80}")
        logger.info(f"VALIDATION RESULT: {'✅ PASSED' if validation['passed'] else '❌ FAILED'}")
        logger.info(f"{'='*80}")

        if not validation["passed"]:
            logger.error("Issues found:")
            for issue in validation["issues"]:
                logger.error(f"  - {issue}")

        return {
            "test_case": test_case["name"],
            "rules_extracted": len(rules),
            "validation": validation,
            "response": response,
            "rules": rules
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.error(f"Response text: {response['text'][:500]}...")
        return {
            "test_case": test_case["name"],
            "error": f"JSON parsing failed: {str(e)}",
            "validation": {"passed": False},
            "response": response
        }
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return {
            "test_case": test_case["name"],
            "error": str(e),
            "validation": {"passed": False}
        }

def run_all_tests(api_key: str):
    """Run all test cases and generate summary report."""
    logger.info("\n" + "="*80)
    logger.info("STARTING RULE EXTRACTION TESTS")
    logger.info("="*80)

    results = []
    for test_case in TEST_CASES:
        result = test_rule_extraction(test_case, api_key)
        results.append(result)

    # Summary
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)

    passed = sum(1 for r in results if r.get("validation", {}).get("passed", False))
    total = len(results)

    logger.info(f"\nTotal Tests: {total}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {total - passed}")
    logger.info(f"Success Rate: {passed/total*100:.1f}%")

    logger.info("\n" + "-"*80)
    logger.info("DETAILED RESULTS")
    logger.info("-"*80)

    for result in results:
        status = "✅ PASS" if result.get("validation", {}).get("passed", False) else "❌ FAIL"
        logger.info(f"{status} - {result['test_case']}")
        if not result.get("validation", {}).get("passed", False):
            validation = result.get("validation", {})
            if "issues" in validation:
                for issue in validation["issues"]:
                    logger.info(f"       {issue}")

    # Save detailed results to file
    output_file = project_root / "test_extraction_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"\nDetailed results saved to: {output_file}")

    return results

# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    # Get API key from environment
    api_key = os.getenv("ANTHROPIC_API_KEY") or settings.ANTHROPIC_API_KEY

    if not api_key or api_key == "your-api-key-here":
        logger.error("ANTHROPIC_API_KEY not set. Please set it in .env file or environment.")
        sys.exit(1)

    logger.info(f"Using API key: {api_key[:10]}...")

    # Run tests
    results = run_all_tests(api_key)

    # Exit with status
    passed = sum(1 for r in results if r.get("validation", {}).get("passed", False))
    exit_code = 0 if passed == len(results) else 1

    sys.exit(exit_code)
