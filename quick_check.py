import sys
sys.path.insert(0, '.')
import requests
import json
from configs.config import Config

api_key = Config.OPENAI_API_KEY
base_url = Config.OPENAI_BASE_URL
model = Config.OPENAI_MODEL

test_text = "ETH to drop below $2k warns analyst"

prompt = f"""Analyze this cryptocurrency text and provide structured analysis.

TEXT: {test_text}

## STEP 1: IS THIS POSITIVE OR NEGATIVE?
Simply determine if the overall sentiment is positive or negative for crypto markets.

## STEP 2: IS THIS PREDICTIVE?
- PREDICTIVE = Claims about FUTURE prices
- NON-PREDICTIVE = Current facts

## STEP 3: IF PREDICTIVE, WHAT DIRECTION?
- INCREMENTAL = Price will GO UP
- DECREMENTAL = Price will GO DOWN

## STEP 4: EMOTION
- JOY/FEAR/ANGER/ANTICIPATION

## OUTPUT JSON:
{{
    "sentiment": "bullish/bearish/neutral",
    "is_positive": true/false,
    "is_predictive": true/false,
    "predictive_direction": "incremental/decremental/neutral/null",
    "primary_emotion": "JOY/FEAR/ANGER/ANTICIPATION",
    "summary": "brief"
}}

Output only valid JSON."""

headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
data = {
    'model': model,
    'messages': [{"role": "user", "content": prompt}]
}

print("TEST: ETH to drop below $2k")
print("Expected: DECREMENTAL")
print("-" * 40)

response = requests.post(base_url, headers=headers, json=data, timeout=60)
content = response.json()['choices'][0]['message']['content']

print(f"Raw Response:\n{content}")
print("-" * 40)

analysis = json.loads(content)
print(f"\nParsed Results:")
print(f"  is_predictive: {analysis.get('is_predictive')}")
print(f"  predictive_direction: {analysis.get('predictive_direction')}")
print(f"  sentiment: {analysis.get('sentiment')}")

if analysis.get('predictive_direction') == 'decremental':
    print("\n[OK] Correctly identified as DECREMENTAL!")
else:
    print(f"\n[FAIL] Expected 'decremental', got: {analysis.get('predictive_direction')}")
