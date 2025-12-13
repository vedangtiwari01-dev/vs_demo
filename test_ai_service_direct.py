"""
Direct AI Service Testing - Test individual AI endpoints
"""
import requests
import json

AI_SERVICE_URL = "http://localhost:8000"
SOP_FILE_PATH = r"C:\Users\VedangTiwari\Desktop\test_git\vs_demo\backend\uploads\sops\sop_samp-1765579178433-866410195.docx"

print("="*60)
print("DIRECT AI SERVICE TESTING")
print("="*60)

# Test 1: Parse SOP
print("\n[TEST 1] Parse SOP Document")
print("-"*60)

try:
    response = requests.post(
        f"{AI_SERVICE_URL}/ai/sop/parse",
        json={
            "file_path": SOP_FILE_PATH,
            "file_type": "docx"
        }
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"✓ Success!")
        print(f"Text length: {len(result.get('text', ''))}")
        print(f"First 200 chars: {result.get('text', '')[:200]}...")

        # Save for next test
        sop_text = result.get('text', '')

        # Test 2: Extract Rules
        print("\n[TEST 2] Extract Rules from Text")
        print("-"*60)

        response2 = requests.post(
            f"{AI_SERVICE_URL}/ai/sop/extract-rules?use_llm=true",
            json={
                "text": sop_text
            }
        )

        print(f"Status: {response2.status_code}")

        if response2.status_code == 200:
            result2 = response2.json()
            print(f"✓ Success!")
            print(f"Rules extracted: {len(result2.get('rules', []))}")

            for i, rule in enumerate(result2.get('rules', [])[:3], 1):
                print(f"\n{i}. Type: {rule.get('type')}")
                print(f"   Description: {rule.get('description', '')[:80]}...")
                print(f"   Severity: {rule.get('severity')}")
        else:
            print(f"✗ Failed!")
            print(f"Response: {response2.text}")

    else:
        print(f"✗ Failed!")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"✗ Exception: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
