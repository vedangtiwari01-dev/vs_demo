#!/usr/bin/env python3
"""Fix curly braces in the improved prompt for Python .format() compatibility"""

# Read the improved prompt
with open('improved_prompt_temp.txt', 'r', encoding='utf-8') as f:
    prompt_content = f.read()

# Escape all curly braces by doubling them
# This makes them literal braces instead of format placeholders
escaped_content = prompt_content.replace('{', '{{').replace('}', '}}')

# Now add back the {sop_text} placeholder (which should be single braces)
escaped_content = escaped_content.replace('{{sop_text}}', '{sop_text}')

# Read the current prompts.py
with open('app/services/claude/prompts.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the prompt boundaries
start_line = None
end_line = None

for i, line in enumerate(lines):
    if 'SOP_RULE_EXTRACTION_PROMPT = """' in line:
        start_line = i
    if start_line is not None and line.strip() == '"""' and i > start_line + 1:
        end_line = i
        break

print(f"Found prompt from line {start_line} to {end_line}")

# Reconstruct the file
new_lines = []

# Lines before the prompt
new_lines.extend(lines[:start_line])

# New prompt
new_lines.append('# SOP Rule Extraction Prompt - IMPROVED (Compact Output + Explicit Instructions)\n')
new_lines.append('SOP_RULE_EXTRACTION_PROMPT = """You are an expert at analyzing Standard Operating Procedures (SOPs) and extracting structured compliance rules.\n')
new_lines.append('\n')
new_lines.append('Your task: Extract ALL rules from the SOP document and return them as a JSON array.\n')
new_lines.append('\n')
new_lines.append(escaped_content)
new_lines.append('\n"""')
new_lines.append('\n')

# Lines after the prompt
new_lines.extend(lines[end_line+1:])

# Write the updated file
with open('app/services/claude/prompts.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✓ prompts.py updated successfully with escaped braces!")
print("All JSON examples now have {{ }} instead of { }")
print("The {sop_text} placeholder is preserved")
