import sys
import os
sys.path.insert(0, '.')

# 设置UTF-8输出
os.environ['PYTHONIOENCODING'] = 'utf-8'

from configs.config import Config
from analyzers.llm_analyzer import LLMAnalyzer
from utils.helpers import load_from_json
import re

def remove_emoji(text):
    """移除文本中的emoji字符"""
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

print("=" * 70)
print("TESTING COLLECTED TWITTER DATA")
print("=" * 70)

Config.init_dirs()

# 检查数据文件
cleaned_file = "C:\\Users\\86186\\Desktop\\UESTC\\llm4crypto\\data\\cleaned\\cleaned_twitter_20260512.json"

print("\n[1/3] 检查数据文件")
print("-" * 50)

cleaned_data = load_from_json(cleaned_file)
if cleaned_data:
    print(f"  [OK] 清洗后数据: {len(cleaned_data)} 条")
else:
    print(f"  [ERROR] 无法加载数据文件")
    sys.exit(1)

# 数据统计
print("\n[2/3] 数据统计")
print("-" * 50)

texts = []
for item in cleaned_data:
    if isinstance(item, dict):
        if 'text' in item:
            texts.append(item['text'])
        elif 'full_text' in item:
            texts.append(item['full_text'])
    
print(f"  总推文数: {len(cleaned_data)}")
print(f"  可分析文本数: {len(texts)}")
print(f"  平均文本长度: {sum(len(t) for t in texts) // len(texts) if texts else 0} 字符")

# 显示前3条示例（移除emoji）
print("\n  示例推文:")
for i, t in enumerate(texts[:3]):
    clean_text = remove_emoji(t)[:60]
    print(f"    [{i+1}] {clean_text}...")

# LLM 分析
print("\n[3/3] LLM 情感分析")
print("-" * 50)

try:
    analyzer = LLMAnalyzer()
    
    if texts:
        # 只分析前5条以节省API调用
        sample_texts = texts[:5]
        print(f"  分析前 {len(sample_texts)} 条推文...")
        
        # 转换格式
        twitter_data = [{'text': t} for t in sample_texts]
        results = analyzer.analyze_dataset(twitter_data)
        
        # 统计结果
        sentiments = {}
        emotions = {}
        directions = {'incremental': 0, 'decremental': 0, 'neutral': 0, 'null': 0}
        predictive_count = 0
        
        for r in results:
            llm_analysis = r.get('llm_analysis', r)
            sent = llm_analysis.get('sentiment', 'unknown')
            emo = llm_analysis.get('primary_emotion', 'UNKNOWN')
            direction = llm_analysis.get('predictive_direction', 'null')
            is_pred = llm_analysis.get('is_predictive', False)
            
            sentiments[sent] = sentiments.get(sent, 0) + 1
            emotions[emo] = emotions.get(emo, 0) + 1
            if direction in directions:
                directions[direction] += 1
            if is_pred:
                predictive_count += 1
        
        print(f"\n  分析结果统计:")
        print(f"  预测性语句: {predictive_count}/{len(results)} ({100*predictive_count/len(results):.1f}%)")
        print(f"\n  情感分布:")
        for s, c in sorted(sentiments.items()):
            print(f"    {s}: {c}")
        print(f"\n  方向分布:")
        for d, c in directions.items():
            if c > 0:
                print(f"    {d}: {c}")
        
        # 显示分析示例
        print("\n  分析示例:")
        for i, r in enumerate(results[:3]):
            llm_analysis = r.get('llm_analysis', r)
            text_preview = remove_emoji(r.get('text', ''))[:30]
            print(f"    [{i+1}] {text_preview}...")
            print(f"        sentiment={llm_analysis.get('sentiment')}, direction={llm_analysis.get('predictive_direction')}, emotion={llm_analysis.get('primary_emotion')}")
        
    else:
        print("  [WARN] 没有可分析的数据")

except Exception as e:
    print(f"  [ERROR] LLM分析失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("TEST COMPLETED")
print("=" * 70)
