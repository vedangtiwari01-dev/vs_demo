"""
Test LLM Pattern Analysis - Using only Python standard library (no requests needed)
"""

import urllib.request
import json

print("=" * 100)
print("LLM PATTERN ANALYSIS TEST - REAL API CALL")
print("=" * 100)

# Load the test data
with open('test_llm_call.json', 'r') as f:
    payload = json.load(f)

print(f"\nTest Setup:")
print(f"  - Sample deviations: {len(payload['deviations'])}")
print(f"  - Deviation types: {len(set(d['deviation_type'] for d in payload['deviations']))} unique types")
print(f"  - Officers: {len(set(d['officer_id'] for d in payload['deviations']))} unique officers")

print("\n" + "=" * 100)
print("CALLING AI SERVICE...")
print("=" * 100)

try:
    # Prepare the request
    url = 'http://localhost:8000/ai/deviation/analyze-patterns'
    data = json.dumps(payload).encode('utf-8')

    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'}
    )

    # Make the request
    with urllib.request.urlopen(req, timeout=120) as response:
        result = json.loads(response.read().decode('utf-8'))

    print("\n✓ API call successful!\n")
    print("=" * 100)
    print("LLM RESPONSE")
    print("=" * 100)

    # Display the analysis
    if 'analysis' in result:
        print(result['analysis'])
    else:
        print(json.dumps(result, indent=2))

    print("\n" + "=" * 100)
    print("TEST COMPLETE")
    print("=" * 100)

    # Show metadata if available
    if 'metadata' in result:
        print("\nResponse Metadata:")
        print(f"  - Model: {result['metadata'].get('model', 'N/A')}")
        print(f"  - Tokens used: {result['metadata'].get('tokens_used', 'N/A')}")
        print(f"  - Processing time: {result['metadata'].get('processing_time_ms', 'N/A')}ms")

except urllib.error.URLError as e:
    if hasattr(e, 'reason'):
        print(f"\n✗ ERROR: Could not connect to AI service")
        print(f"Reason: {e.reason}")
        print("\nMake sure the AI service is running:")
        print("  cd ai-service")
        print("  venv\\Scripts\\activate")
        print("  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    elif hasattr(e, 'code'):
        print(f"\n✗ ERROR: HTTP {e.code}")
        print(f"Response: {e.read().decode('utf-8')}")

except TimeoutError:
    print("\n✗ ERROR: Request timed out (LLM took too long to respond)")

except Exception as e:
    print(f"\n✗ ERROR: {type(e).__name__}: {e}")

print("\n")
