import sys
sys.path.insert(0, '.')
from analyzers.llm_analyzer import LLMAnalyzer
import json

print("=" * 70)
print("HYBRID PROMPT - FORMAL TEST")
print("=" * 70)

analyzer = LLMAnalyzer()

test_cases = [
    # (text, expected_direction, description)
    ("Bitcoin will reach $100k by end of year", "INCREMENTAL", "看涨预测"),
    ("ETH to drop below $2k warns analyst", "DECREMENTAL", "看跌预测"),
    ("SEC approves Bitcoin ETF", "NON_PREDICTIVE", "事实性新闻"),
    ("BTC to surge next week", "INCREMENTAL", "短期看涨"),
    ("Market crash warning issued", "DECREMENTAL", "市场警告"),
    ("SHIB will pump 100x soon", "INCREMENTAL", "暴涨预测"),
    ("DOGE to dump after selloff", "DECREMENTAL", "抛售预测"),
    ("Ethereum upgrade completed", "NON_PREDICTIVE", "技术升级"),
    (" whales accumulating BTC", "NON_PREDICTIVE", "机构动向"),
    ("Altcoin season starting", "INCREMENTAL", "季节预测"),
]

results = []
print(f"\nTesting {len(test_cases)} cases...\n")

for i, (text, expected, desc) in enumerate(test_cases):
    print(f"[{i+1}/{len(test_cases)}] {text[:40]}...", flush=True)

    r = analyzer.analyze_text(text, use_cache=False)

    if r:
        direction = r.get('predictive_direction', 'N/A')
        is_pred = r.get('is_predictive', False)
        sentiment = r.get('sentiment', 'N/A')
        emotion = r.get('primary_emotion', 'N/A')
        importance = r.get('importance', 0)

        # 判断正确性 - 注意大小写
        if expected == "NON_PREDICTIVE":
            correct = not is_pred
        else:
            # direction返回小写(incremental/decremental)，expected是大写
            correct = (is_pred and direction.lower() == expected.lower())

        status = "[OK]" if correct else "[FAIL]"

        print(f"    {status} 方向={direction:12} 情绪={sentiment:8} 重要性={importance}")

        results.append({
            'text': text,
            'expected': expected,
            'direction': direction,
            'sentiment': sentiment,
            'emotion': emotion,
            'importance': importance,
            'correct': correct
        })
    else:
        print(f"    [ERROR] No result returned")
        results.append({
            'text': text,
            'expected': expected,
            'error': True
        })

print("\n" + "=" * 70)
print("DETAILED RESULTS")
print("=" * 70)

for i, r in enumerate(results):
    if 'error' in r:
        continue
    print(f"\n[{i+1}] {r['text']}")
    print(f"    预期: {r['expected']}")
    print(f"    实际: direction={r['direction']}, sentiment={r['sentiment']}")
    print(f"    情绪: {r['emotion']}, 重要性: {r['importance']}/10")

correct_count = sum(1 for r in results if not 'error' in r and r['correct'])
total = len([r for r in results if not 'error' in r])

print("\n" + "=" * 70)
print("ACCURACY SUMMARY")
print("=" * 70)
print(f"\n总体准确率: {correct_count}/{total} ({100*correct_count/total:.1f}%)")

# 分类统计
incremental_correct = sum(1 for r in results if not 'error' in r and r['expected'] == 'INCREMENTAL' and r['correct'])
incremental_total = sum(1 for r in results if not 'error' in r and r['expected'] == 'INCREMENTAL')
decremental_correct = sum(1 for r in results if not 'error' in r and r['expected'] == 'DECREMENTAL' and r['correct'])
decremental_total = sum(1 for r in results if not 'error' in r and r['expected'] == 'DECREMENTAL')
non_pred_correct = sum(1 for r in results if not 'error' in r and r['expected'] == 'NON_PREDICTIVE' and r['correct'])
non_pred_total = sum(1 for r in results if not 'error' in r and r['expected'] == 'NON_PREDICTIVE')

print(f"\n增量预测准确率(INCREMENTAL): {incremental_correct}/{incremental_total} ({100*incremental_correct/incremental_total:.1f}%)" if incremental_total > 0 else "\n增量预测: N/A")
print(f"减量预测准确率(DECREMENTAL): {decremental_correct}/{decremental_total} ({100*decremental_correct/decremental_total:.1f}%)" if decremental_total > 0 else "减量预测: N/A")
print(f"非预测判断准确率(NON_PRED): {non_pred_correct}/{non_pred_total} ({100*non_pred_correct/non_pred_total:.1f}%)" if non_pred_total > 0 else "非预测: N/A")

# 情绪分布
sentiments = {}
emotions = {}
for r in results:
    if 'error' in r:
        continue
    sent = r.get('sentiment', 'unknown')
    emo = r.get('emotion', 'UNKNOWN')
    sentiments[sent] = sentiments.get(sent, 0) + 1
    emotions[emo] = emotions.get(emo, 0) + 1

print(f"\n情绪分布: {sentiments}")
print(f"Emotion分布: {emotions}")

print("\n" + "=" * 70)
print("TEST COMPLETED")
print("=" * 70)
