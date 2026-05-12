import sys
sys.path.insert(0, '.')
import requests
import json
from configs.config import Config

api_key = Config.OPENAI_API_KEY
base_url = Config.OPENAI_BASE_URL
model = Config.OPENAI_MODEL

test_cases = [
    ("Bitcoin will reach $100k by end of year", "INCREMENTAL"),
    ("ETH to drop below $2k warns analyst", "DECREMENTAL"),
    ("BTC to surge next week", "INCREMENTAL"),
    ("Market crash warning issued", "DECREMENTAL"),
]

print("DIAGNOSTIC TEST - Checking actual API responses")
print("=" * 70)

for text, expected in test_cases:
    prompt = f"""Analyze this cryptocurrency text and provide structured analysis.

TEXT: {text}

## STEP 1: IS THIS POSITIVE OR NEGATIVE?
Simply determine if the overall sentiment is positive or negative for crypto markets.

## STEP 2: IS THIS PREDICTIVE?
- PREDICTIVE = Claims about FUTURE prices (e.g., "BTC will reach $100k", "ETH to drop below $2k")
- NON-PREDICTIVE = Current facts (e.g., "SEC approved ETF", "Binance listed token")

## STEP 3: IF PREDICTIVE, WHAT DIRECTION?
- INCREMENTAL = Price will GO UP (bullish words: reach, surge, rally, pump, jump, gain, climb, hit new high)
- DECREMENTAL = Price will GO DOWN (bearish words: drop, crash, dump, fall, decline, plummet, lose, below)

## STEP 4: EMOTION (SenticNet)
Choose primary emotion:
- JOY: Positive news, success, gains
- FEAR: Concerns, risks, warnings
- ANGER: Failures, rejections, losses
- ANTICIPATION: Expectations, upcoming events

## OUTPUT JSON:
{{
    "sentiment": "bullish/bearish/neutral",
    "is_positive": true/false,
    "is_predictive": true/false,
    "predictive_direction": "incremental/decremental/neutral/null",
    "tokens": ["TOKEN1"],
    "primary_emotion": "JOY/FEAR/ANGER/ANTICIPATION",
    "importance": 1-10,
    "summary": "brief summary"
}}

IMPORTANT: Output only valid JSON."""

    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    data = {
        'model': model,
        'messages': [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post(base_url, headers=headers, json=data, timeout=60)
        content = response.json()['choices'][0]['message']['content']

        print(f"\n{'='*60}")
        print(f"Text: {text}")
        print(f"Expected: {expected}")
        print(f"Raw Response:\n{content}")
        print("-" * 60)

        try:
            analysis = json.loads(content)
            direction = analysis.get('predictive_direction', 'N/A')
            is_pred = analysis.get('is_predictive', None)
            sentiment = analysis.get('sentiment', 'N/A')

            print(f"Parsed:")
            print(f"  is_predictive: {is_pred}")
            print(f"  predictive_direction: {direction}")
            print(f"  sentiment: {sentiment}")

            # Check if it matches expected
            if expected == "INCREMENTAL" and direction == "incremental":
                print(f"  Result: [OK]")
            elif expected == "DECREMENTAL" and direction == "decremental":
                print(f"  Result: [OK]")
            elif expected == "NON_PREDICTIVE" and not is_pred:
                print(f"  Result: [OK]")
            else:
                print(f"  Result: [FAIL] - Expected {expected}")

        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")

    except Exception as e:
        print(f"API Error: {e}")

print("\n" + "=" * 70)
print("DIAGNOSIS COMPLETE")
print("=" * 70)
