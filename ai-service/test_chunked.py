"""Test chunked extraction with the full SOP"""
import sys
import json
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.nlp.llm_rule_parser import LLMRuleParser

# Read SOP
sop_path = Path(__file__).parent / "syn_sop.txt"
with open(sop_path, 'r', encoding='utf-8') as f:
    sop_text = f.read()

print(f"📄 SOP Size: {len(sop_text)} characters")
print(f"🔍 Chunking threshold: 25,000 characters")
print(f"✅ Will use chunking: {len(sop_text) > 25000}\n")

# Initialize parser
parser = LLMRuleParser()

# Extract rules
print("🚀 Starting extraction...")
result = parser.extract_rules(sop_text, use_llm=True, fallback_on_error=True)

# Display results
print("\n" + "="*80)
print("EXTRACTION RESULTS")
print("="*80)
print(f"✅ Extraction Method: {result.get('extraction_method')}")
print(f"✅ Total Rules Extracted: {len(result.get('rules', []))}")
print(f"✅ Confidence: {result.get('confidence', 0):.2f}")

if result.get('extraction_method') == 'llm_chunked':
    print(f"✅ Chunks Processed: {result.get('chunks_processed', 0)}")
    print(f"✅ Chunks Succeeded: {result.get('chunks_succeeded', 0)}")
    print(f"✅ Chunks Failed: {result.get('chunks_failed', 0)}")

# Analyze rules
rules = result.get('rules', [])
print("\n" + "="*80)
print("RULE ANALYSIS")
print("="*80)

# Count by type
rule_types = {}
for rule in rules:
    rule_type = rule.get('rule_type', 'unknown')
    rule_types[rule_type] = rule_types.get(rule_type, 0) + 1

print("\n📊 Rules by Type:")
for rule_type, count in sorted(rule_types.items()):
    print(f"  - {rule_type}: {count}")

# Check critical thresholds
print("\n🔍 Critical Thresholds:")
age_rules = [r for r in rules if 'age' in r.get('rule_description', '').lower()]
emi_rules = [r for r in rules if 'emi' in r.get('rule_description', '').lower()]

print(f"  - Age rules found: {len(age_rules)}")
for rule in age_rules[:3]:  # Show first 3
    print(f"    • {rule.get('rule_description')[:80]}")
    print(f"      threshold_value: {rule.get('threshold_value')}")

print(f"  - EMI rules found: {len(emi_rules)}")
for rule in emi_rules[:3]:  # Show first 3
    print(f"    • {rule.get('rule_description')[:80]}")
    print(f"      threshold_value: {rule.get('threshold_value')}")

# Save results
output_path = Path(__file__).parent / "test_chunked_results.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2)

print(f"\n💾 Full results saved to: {output_path}")
print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
