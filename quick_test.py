import sys
sys.path.insert(0, '.')
from analyzers.llm_analyzer import LLMAnalyzer
import json

print("=" * 70)
print("HYBRID PROMPT - QUICK TEST")
print("=" * 70)

analyzer = LLMAnalyzer()

test_cases = [
    ("Bitcoin will reach $100k by end of year", "INCREMENTAL"),
    ("ETH to drop below $2k warns analyst", "DECREMENTAL"),
    ("SEC approves Bitcoin ETF", "NON_PREDICTIVE"),
]

print(f"\nTesting {len(test_cases)} cases...\n")

for i, (text, expected) in enumerate(test_cases):
    print(f"[{i+1}/{len(test_cases)}] {text[:40]}...", flush=True)

    r = analyzer.analyze_text(text, use_cache=False)

    if r:
        direction = r.get('predictive_direction', 'N/A')
        is_pred = r.get('is_predictive', False)
        sentiment = r.get('sentiment', 'N/A')

        print(f"    direction={direction}, is_predictive={is_pred}, sentiment={sentiment}")
    else:
        print(f"    [ERROR] No result returned")
