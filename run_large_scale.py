import sys
import os
import re
from datetime import datetime, timezone
sys.path.insert(0, '.')

os.environ['PYTHONIOENCODING'] = 'utf-8'

from cleaners.data_cleaner import DataCleaner
from analyzers.llm_analyzer import LLMAnalyzer
from configs.config import Config
from utils.helpers import save_to_json, logger

def remove_emoji(text):
    """移除文本中的emoji字符"""
    if not isinstance(text, str):
        return str(text)
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
                           "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def safe_print(text):
    """安全打印，处理Unicode字符"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(remove_emoji(text))

def get_current_date():
    return datetime.now(timezone.utc).strftime('%Y%m%d')

def generate_test_tweets():
    """生成测试用的推文数据"""
    test_tweets = [
        {
            'tweet_id': '1',
            'tweet_text': 'Bitcoin will reach $100k by the end of this year! This is bullish news for crypto investors.',
            'author_name': 'CryptoExpert',
            'author_handle': '@CryptoExpert',
            'timestamp': '2026-05-12T10:00:00Z',
            'retweets': 1200,
            'likes': 5400,
            'hashtags': ['#Bitcoin', '#Crypto'],
            'data_source': 'twitter'
        },
        {
            'tweet_id': '2',
            'tweet_text': 'SEC approves Bitcoin ETF! This is a game changer for institutional adoption.',
            'author_name': 'CoinDesk',
            'author_handle': '@CoinDesk',
            'timestamp': '2026-05-12T09:30:00Z',
            'retweets': 8500,
            'likes': 23000,
            'hashtags': ['#BTC', '#ETF'],
            'data_source': 'twitter'
        },
        {
            'tweet_id': '3',
            'tweet_text': 'Warning: Bitcoin is flashing a rare sell signal. Expect a drop below $70k.',
            'author_name': 'CryptoAnalyst',
            'author_handle': '@CryptoAnalyst',
            'timestamp': '2026-05-12T08:45:00Z',
            'retweets': 3200,
            'likes': 8900,
            'hashtags': ['#Bitcoin', '#Trading'],
            'data_source': 'twitter'
        },
        {
            'tweet_id': '4',
            'tweet_text': 'Ethereum upgrades are coming! The merge will bring significant improvements.',
            'author_name': 'VitalikButerin',
            'author_handle': '@VitalikButerin',
            'timestamp': '2026-05-12T08:00:00Z',
            'retweets': 15000,
            'likes': 45000,
            'hashtags': ['#Ethereum', '#ETH'],
            'data_source': 'twitter'
        },
        {
            'tweet_id': '5',
            'tweet_text': 'Altcoin season is starting! SOL and AVAX will outperform this quarter.',
            'author_name': 'CryptoCapo',
            'author_handle': '@CryptoCapo',
            'timestamp': '2026-05-12T07:30:00Z',
            'retweets': 4500,
            'likes': 12000,
            'hashtags': ['#Altcoins', '#SOL'],
            'data_source': 'twitter'
        },
        {
            'tweet_id': '6',
            'tweet_text': 'Bitcoin price analysis: current support at $78k, resistance at $85k.',
            'author_name': 'TradingView',
            'author_handle': '@TradingView',
            'timestamp': '2026-05-12T07:00:00Z',
            'retweets': 2300,
            'likes': 6700,
            'hashtags': ['#BTC', '#TechnicalAnalysis'],
            'data_source': 'twitter'
        },
        {
            'tweet_id': '7',
            'tweet_text': 'Binance lists new memecoin. This could be the next big pump!',
            'author_name': 'cz_binance',
            'author_handle': '@cz_binance',
            'timestamp': '2026-05-12T06:30:00Z',
            'retweets': 8900,
            'likes': 28000,
            'hashtags': ['#Binance', '#Memecoin'],
            'data_source': 'twitter'
        },
        {
            'tweet_id': '8',
            'tweet_text': 'Regulatory crackdown continues. This could negatively impact crypto markets.',
            'author_name': 'CryptoNews',
            'author_handle': '@CryptoNews',
            'timestamp': '2026-05-12T06:00:00Z',
            'retweets': 5600,
            'likes': 15000,
            'hashtags': ['#Regulation', '#Crypto'],
            'data_source': 'twitter'
        },
        {
            'tweet_id': '9',
            'tweet_text': 'Michael Saylor buys another 10k BTC! MicroStrategy continues accumulation.',
            'author_name': 'saylor',
            'author_handle': '@saylor',
            'timestamp': '2026-05-12T05:30:00Z',
            'retweets': 12000,
            'likes': 35000,
            'hashtags': ['#Bitcoin', '#MicroStrategy'],
            'data_source': 'twitter'
        },
        {
            'tweet_id': '10',
            'tweet_text': 'Fear and Greed Index is at 75 - bullish sentiment continues.',
            'author_name': 'Alternative',
            'author_handle': '@Alternative',
            'timestamp': '2026-05-12T05:00:00Z',
            'retweets': 3400,
            'likes': 9800,
            'hashtags': ['#FearGreed', '#Crypto'],
            'data_source': 'twitter'
        },
        {
            'tweet_id': '11',
            'tweet_text': '$BTC FAST SCALP SHORT risky trade Be careful Safe trading everyone',
            'author_name': 'CryptoTrader',
            'author_handle': '@CryptoTrader',
            'timestamp': '2026-05-12T04:30:00Z',
            'retweets': 890,
            'likes': 2300,
            'hashtags': ['#BTC', '#Trading'],
            'data_source': 'twitter'
        },
        {
            'tweet_id': '12',
            'tweet_text': '$11T CHARLES SCHWAB FOLLOWS MORGAN STANLEY INTO BITCOIN INSTITUTIONAL ADOPTION',
            'author_name': 'CryptoWhale',
            'author_handle': '@CryptoWhale',
            'timestamp': '2026-05-12T04:00:00Z',
            'retweets': 15000,
            'likes': 42000,
            'hashtags': ['#Bitcoin', '#Institutional'],
            'data_source': 'twitter'
        }
    ]
    return test_tweets

def run_large_scale_test():
    """大规模数据采集与分析测试"""
    current_date = get_current_date()
    safe_print("=" * 70)
    safe_print(f"大规模测试运行 - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    safe_print("=" * 70)
    
    # 初始化目录
    Config.init_dirs()
    
    all_results = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'twitter': {},
        'analysis': {}
    }
    
    # 1. 生成测试数据
    safe_print("\n[1/4] 生成测试数据")
    safe_print("-" * 50)
    test_tweets = generate_test_tweets()
    save_to_json(test_tweets, f"{Config.RAW_DATA_DIR}/twitter_test_data_{current_date}.json")
    safe_print(f"  [OK] 生成测试数据: {len(test_tweets)} 条推文")
    all_results['twitter']['raw_count'] = len(test_tweets)
    
    # 2. 数据清洗
    safe_print("\n[2/4] 数据清洗")
    safe_print("-" * 50)
    try:
        cleaner = DataCleaner()
        cleaned_tweets = cleaner.clean_twitter_data(test_tweets)
        save_to_json(cleaned_tweets, f"{Config.CLEANED_DATA_DIR}/cleaned_twitter_{current_date}.json")
        safe_print(f"  [OK] 数据清洗完成: {len(cleaned_tweets)} 条")
        all_results['analysis']['cleaned_count'] = len(cleaned_tweets)
    except Exception as e:
        safe_print(f"  [ERROR] 数据清洗失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. LLM 情感分析
    safe_print("\n[3/4] LLM 情感分析")
    safe_print("-" * 50)
    try:
        analyzer = LLMAnalyzer()
        
        # 准备数据
        texts_to_analyze = []
        for tweet in cleaned_tweets:
            if isinstance(tweet, dict):
                if 'text' in tweet:
                    texts_to_analyze.append({'text': tweet['text']})
                elif 'tweet_text' in tweet:
                    texts_to_analyze.append({'text': tweet['tweet_text']})
        
        # 执行分析
        safe_print(f"  正在分析 {len(texts_to_analyze)} 条推文...")
        results = analyzer.analyze_dataset(texts_to_analyze)
        save_to_json(results, f"{Config.ANALYSIS_DIR}/llm_analysis_{current_date}.json")
        
        # 统计结果
        sentiments = {}
        emotions = {}
        directions = {'incremental': 0, 'decremental': 0, 'neutral': 0, 'null': 0}
        predictive_count = 0
        bullish_count = 0
        bearish_count = 0
        neutral_count = 0
        
        for r in results:
            llm_analysis = r.get('llm_analysis', r)
            sent = llm_analysis.get('sentiment', 'unknown').lower()
            emo = llm_analysis.get('primary_emotion', 'UNKNOWN')
            direction = llm_analysis.get('predictive_direction', 'null')
            is_pred = llm_analysis.get('is_predictive', False)
            
            sentiments[sent] = sentiments.get(sent, 0) + 1
            emotions[emo] = emotions.get(emo, 0) + 1
            if direction in directions:
                directions[direction] += 1
            if is_pred:
                predictive_count += 1
            if sent == 'bullish':
                bullish_count += 1
            elif sent == 'bearish':
                bearish_count += 1
            elif sent == 'neutral':
                neutral_count += 1
        
        # 保存统计结果
        all_results['analysis']['sentiment_distribution'] = sentiments
        all_results['analysis']['emotion_distribution'] = emotions
        all_results['analysis']['direction_distribution'] = directions
        all_results['analysis']['predictive_count'] = predictive_count
        all_results['analysis']['total_analyzed'] = len(results)
        
        safe_print(f"  [OK] LLM 分析完成")
        safe_print(f"       预测性语句: {predictive_count}/{len(results)} ({100*predictive_count/len(results):.1f}%)")
        safe_print(f"       看涨: {bullish_count}, 看跌: {bearish_count}, 中性: {neutral_count}")
        
        # 显示分析示例
        safe_print("\n  分析示例:")
        for i, r in enumerate(results[:5]):
            llm_analysis = r.get('llm_analysis', r)
            text_preview = remove_emoji(r.get('text', ''))[:30]
            safe_print(f"    [{i+1}] {text_preview}...")
            safe_print(f"        sentiment={llm_analysis.get('sentiment')}, direction={llm_analysis.get('predictive_direction')}, emotion={llm_analysis.get('primary_emotion')}")
            
    except Exception as e:
        safe_print(f"  [ERROR] LLM 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. 生成报告
    safe_print("\n[4/4] 生成分析报告")
    safe_print("-" * 50)
    report = generate_report(all_results)
    report_path = f"{Config.ANALYSIS_DIR}/analysis_report_{current_date}.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    safe_print(f"  [OK] 报告已生成: {report_path}")
    
    # 保存测试结果
    save_to_json(all_results, f"{Config.ANALYSIS_DIR}/large_scale_test_results_{current_date}.json")
    
    # 打印总结
    safe_print("\n" + "=" * 70)
    safe_print("大规模测试总结")
    safe_print("=" * 70)
    
    safe_print("\n📊 采集数据量:")
    safe_print(f"  Twitter 推文: {all_results['twitter'].get('raw_count', 0)} 条")
    
    safe_print("\n🔍 分析结果:")
    safe_print(f"  清洗后数据: {all_results['analysis'].get('cleaned_count', 0)} 条")
    safe_print(f"  分析数量: {all_results['analysis'].get('total_analyzed', 0)} 条")
    safe_print(f"  预测性语句: {all_results['analysis'].get('predictive_count', 0)} 条")
    safe_print(f"  情感分布: {all_results['analysis'].get('sentiment_distribution', {})}")
    safe_print(f"  方向分布: {all_results['analysis'].get('direction_distribution', {})}")
    
    safe_print("\n📁 数据文件保存至:")
    safe_print("  - data/raw/ (原始数据)")
    safe_print("  - data/cleaned/ (清洗后数据)")
    safe_print("  - data/analysis/ (分析结果和报告)")

def generate_report(results):
    """生成分析报告"""
    report = f"""# 加密货币数据分析报告

生成时间: {results['timestamp']}

## 1. 数据概览

| 数据源 | 数量 |
|--------|------|
| 原始推文 | {results['twitter'].get('raw_count', 0)} 条 |
| 清洗后数据 | {results['analysis'].get('cleaned_count', 0)} 条 |
| LLM分析数量 | {results['analysis'].get('total_analyzed', 0)} 条 |

## 2. 情感分析结果

### 2.1 情感分布

| 情感类型 | 数量 | 占比 |
|----------|------|------|
| 看涨 (Bullish) | {results['analysis']['sentiment_distribution'].get('bullish', 0)} | {100*results['analysis']['sentiment_distribution'].get('bullish', 0)/results['analysis'].get('total_analyzed', 1):.1f}% |
| 看跌 (Bearish) | {results['analysis']['sentiment_distribution'].get('bearish', 0)} | {100*results['analysis']['sentiment_distribution'].get('bearish', 0)/results['analysis'].get('total_analyzed', 1):.1f}% |
| 中性 (Neutral) | {results['analysis']['sentiment_distribution'].get('neutral', 0)} | {100*results['analysis']['sentiment_distribution'].get('neutral', 0)/results['analysis'].get('total_analyzed', 1):.1f}% |

### 2.2 预测性分析

- 预测性语句: {results['analysis'].get('predictive_count', 0)}/{results['analysis'].get('total_analyzed', 0)} ({100*results['analysis'].get('predictive_count', 0)/results['analysis'].get('total_analyzed', 1):.1f}%)

### 2.3 方向分布

| 方向 | 数量 |
|------|------|
| 增量 (Incremental) | {results['analysis']['direction_distribution'].get('incremental', 0)} |
| 减量 (Decremental) | {results['analysis']['direction_distribution'].get('decremental', 0)} |
| 中性 (Neutral) | {results['analysis']['direction_distribution'].get('neutral', 0)} |
| 无方向 (Null) | {results['analysis']['direction_distribution'].get('null', 0)} |

## 3. 情绪分析

### 3.1 细粒度情绪分布

| 情绪类型 | 数量 |
|----------|------|
| JOY | {results['analysis']['emotion_distribution'].get('JOY', 0)} |
| FEAR | {results['analysis']['emotion_distribution'].get('FEAR', 0)} |
| ANGER | {results['analysis']['emotion_distribution'].get('ANGER', 0)} |
| ANTICIPATION | {results['analysis']['emotion_distribution'].get('ANTICIPATION', 0)} |

## 4. 总结

根据分析结果，当前市场情绪整体偏{get_market_sentiment(results)}。

---

*报告由 llm4crypto 系统自动生成*
"""
    return report

def get_market_sentiment(results):
    """根据分析结果判断市场情绪"""
    sentiments = results['analysis'].get('sentiment_distribution', {})
    bullish = sentiments.get('bullish', 0)
    bearish = sentiments.get('bearish', 0)
    total = bullish + bearish
    
    if total == 0:
        return "中性"
    elif bullish > bearish * 1.5:
        return "强烈看涨"
    elif bullish > bearish:
        return "看涨"
    elif bearish > bullish * 1.5:
        return "强烈看跌"
    elif bearish > bullish:
        return "看跌"
    else:
        return "中性"

if __name__ == "__main__":
    run_large_scale_test()
