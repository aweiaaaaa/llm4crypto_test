import sys
import os
import re
from datetime import datetime, timezone
sys.path.insert(0, '.')

os.environ['PYTHONIOENCODING'] = 'utf-8'

from cleaners.data_cleaner import DataCleaner
from analyzers.llm_analyzer import LLMAnalyzer
from collectors.coingecko_collector import CoinGeckoCollector
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

def run_full_test():
    """完整测试：CoinGecko API + 数据清洗 + LLM 分析"""
    current_date = get_current_date()
    safe_print("=" * 70)
    safe_print(f"完整测试运行 - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    safe_print("=" * 70)
    
    # 初始化目录
    Config.init_dirs()
    
    all_results = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'coingecko': {},
        'analysis': {}
    }
    
    # 1. CoinGecko 数据采集
    safe_print("\n[1/5] CoinGecko 数据采集")
    safe_print("-" * 50)
    try:
        cg_collector = CoinGeckoCollector()
        
        # 获取全球市场数据
        safe_print("  正在获取全球市场数据...")
        global_data = cg_collector.get_global_data()
        global_file = f"{Config.RAW_DATA_DIR}/coingecko_global_{current_date}.json"
        save_to_json(global_data, global_file)
        safe_print(f"  [OK] 全球市场数据已保存")
        
        # 获取市场数据（前 50 个币种）
        safe_print("  正在获取市场数据（前 50 个币种）...")
        market_data = cg_collector.get_coins_market_data(per_page=50)
        market_file = f"{Config.RAW_DATA_DIR}/coingecko_market_{current_date}.json"
        save_to_json(market_data, market_file)
        safe_print(f"  [OK] 市场数据已保存: {len(market_data)} 个币种")
        
        # 获取热门趋势币
        safe_print("  正在获取热门趋势币...")
        trending_data = cg_collector.get_trending_coins()
        trending_file = f"{Config.RAW_DATA_DIR}/coingecko_trending_{current_date}.json"
        save_to_json(trending_data, trending_file)
        safe_print(f"  [OK] 热门趋势币已保存: {len(trending_data)} 个")
        
        # 获取 BTC 和 ETH 的详细信息
        safe_print("  正在获取 BTC 和 ETH 详细信息...")
        btc_info = cg_collector.get_coin_info('bitcoin')
        eth_info = cg_collector.get_coin_info('ethereum')
        coin_info_file = f"{Config.RAW_DATA_DIR}/coingecko_coin_info_{current_date}.json"
        save_to_json({'bitcoin': btc_info, 'ethereum': eth_info}, coin_info_file)
        safe_print(f"  [OK] 币种详细信息已保存")
        
        all_results['coingecko']['market_count'] = len(market_data)
        all_results['coingecko']['trending_count'] = len(trending_data)
        
    except Exception as e:
        safe_print(f"  [ERROR] CoinGecko 采集失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 2. 数据清洗
    safe_print("\n[2/5] 数据清洗")
    safe_print("-" * 50)
    try:
        cleaner = DataCleaner()
        
        # 清洗 CoinGecko 市场数据
        cleaned_coingecko = cleaner.clean_coingecko_data(market_data)
        save_to_json(cleaned_coingecko, f"{Config.CLEANED_DATA_DIR}/cleaned_coingecko_{current_date}.json")
        safe_print(f"  [OK] CoinGecko 数据清洗完成: {len(cleaned_coingecko)} 条")
        
        all_results['analysis']['cleaned_coingecko_count'] = len(cleaned_coingecko)
        
    except Exception as e:
        safe_print(f"  [ERROR] 数据清洗失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. LLM 情感分析
    safe_print("\n[3/5] LLM 情感分析")
    safe_print("-" * 50)
    try:
        analyzer = LLMAnalyzer()
        
        # 准备数据（分析前 20 条清洗后的数据）
        texts_to_analyze = []
        for item in cleaned_coingecko[:20]:
            if isinstance(item, dict):
                if 'text' in item:
                    texts_to_analyze.append({'text': item['text']})
        
        # 执行分析
        safe_print(f"  正在分析 {len(texts_to_analyze)} 条数据...")
        results = analyzer.analyze_dataset(texts_to_analyze)
        save_to_json(results, f"{Config.ANALYSIS_DIR}/llm_analysis_coingecko_{current_date}.json")
        
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
            text_preview = remove_emoji(r.get('text', ''))[:40]
            safe_print(f"    [{i+1}] {text_preview}...")
            safe_print(f"        sentiment={llm_analysis.get('sentiment')}, direction={llm_analysis.get('predictive_direction')}, emotion={llm_analysis.get('primary_emotion')}")
            
    except Exception as e:
        safe_print(f"  [ERROR] LLM 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. 高级特征工程
    safe_print("\n[4/5] 高级特征工程")
    safe_print("-" * 50)
    try:
        # 准备情绪概率数据
        sentiment_probs = []
        for r in results:
            llm_analysis = r.get('llm_analysis', r)
            sent = llm_analysis.get('sentiment', 'neutral').lower()
            pos_prob = 0.5
            neg_prob = 0.5
            neu_prob = 0.0
            
            if sent == 'bullish':
                pos_prob = 0.8
                neg_prob = 0.1
                neu_prob = 0.1
            elif sent == 'bearish':
                pos_prob = 0.1
                neg_prob = 0.8
                neu_prob = 0.1
            else:
                pos_prob = 0.3
                neg_prob = 0.3
                neu_prob = 0.4
            
            sentiment_probs.append({
                'positive': pos_prob,
                'negative': neg_prob,
                'neutral': neu_prob
            })
        
        # 准备价格回报率数据（使用 price_change_24h）
        price_returns = []
        for item in cleaned_coingecko[:len(sentiment_probs)]:
            price_change = item.get('price_change_24h', 0)
            price_returns.append(price_change / 100)  # 转换为小数
        
        # 执行高级特征工程
        safe_print(f"  正在执行高级特征工程...")
        enhanced, pca_features, price_labels = cleaner.advanced_feature_engineering(
            cleaned_coingecko[:len(sentiment_probs)],
            sentiment_probabilities=sentiment_probs,
            price_returns=price_returns,
            n_pca_components=5,
            n_clusters=3
        )
        
        save_to_json(enhanced, f"{Config.CLEANED_DATA_DIR}/enhanced_coingecko_{current_date}.json")
        safe_print(f"  [OK] 高级特征工程完成: {len(enhanced)} 条")
        
        # 获取特征重要性报告
        importance = cleaner.get_feature_importance_report()
        safe_print(f"       PCA 方差解释: {[f'{x:.2%}' for x in importance['explained_variance_ratio']]}")
        safe_print(f"       累积方差解释: {[f'{x:.2%}' for x in importance['cumulative_explained_variance']]}")
        safe_print(f"       价格标签分布: {dict(zip(['下跌', '中性', '上涨'], [price_labels.count(i) for i in range(3)]))}")
        
        all_results['analysis']['pca_variance'] = importance['explained_variance_ratio']
        all_results['analysis']['price_labels'] = price_labels
        
    except Exception as e:
        safe_print(f"  [ERROR] 高级特征工程失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 5. 生成报告
    safe_print("\n[5/5] 生成分析报告")
    safe_print("-" * 50)
    report = generate_report(all_results, market_data)
    report_path = f"{Config.ANALYSIS_DIR}/full_test_report_{current_date}.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    safe_print(f"  [OK] 报告已生成: {report_path}")
    
    # 保存测试结果
    save_to_json(all_results, f"{Config.ANALYSIS_DIR}/full_test_results_{current_date}.json")
    
    # 打印总结
    safe_print("\n" + "=" * 70)
    safe_print("完整测试总结")
    safe_print("=" * 70)
    
    safe_print("\n📊 采集数据量:")
    safe_print(f"  CoinGecko 市场: {all_results['coingecko'].get('market_count', 0)} 个币种")
    safe_print(f"  CoinGecko 趋势: {all_results['coingecko'].get('trending_count', 0)} 个")
    
    safe_print("\n🔍 分析结果:")
    safe_print(f"  清洗后数据: {all_results['analysis'].get('cleaned_coingecko_count', 0)} 条")
    safe_print(f"  分析数量: {all_results['analysis'].get('total_analyzed', 0)} 条")
    safe_print(f"  预测性语句: {all_results['analysis'].get('predictive_count', 0)} 条")
    safe_print(f"  情感分布: {all_results['analysis'].get('sentiment_distribution', {})}")
    safe_print(f"  方向分布: {all_results['analysis'].get('direction_distribution', {})}")
    
    safe_print("\n📁 数据文件保存至:")
    safe_print("  - data/raw/ (原始数据)")
    safe_print("  - data/cleaned/ (清洗后数据)")
    safe_print("  - data/analysis/ (分析结果和报告)")

def generate_report(results, market_data):
    """生成分析报告"""
    # 获取前 10 个币种信息
    top_coins = market_data[:10] if market_data else []
    
    coins_table = "\n".join([
        f"| {i+1} | {coin.get('name', 'N/A')} ({coin.get('symbol', 'N/A').upper()}) | ${coin.get('current_price', 0):,.2f} | {coin.get('price_change_percentage_24h', 0):.2f}% | ${coin.get('market_cap', 0):,.0f} |"
        for i, coin in enumerate(top_coins)
    ])
    
    report = f"""# 加密货币数据分析报告

生成时间: {results['timestamp']}

## 1. 数据概览

| 数据源 | 数量 |
|--------|------|
| CoinGecko 市场数据 | {results['coingecko'].get('market_count', 0)} 个币种 |
| CoinGecko 热门趋势 | {results['coingecko'].get('trending_count', 0)} 个 |
| 清洗后数据 | {results['analysis'].get('cleaned_coingecko_count', 0)} 条 |
| LLM分析数量 | {results['analysis'].get('total_analyzed', 0)} 条 |

## 2. 市场概览（前 10 名）

| 排名 | 币种 | 价格 | 24h 涨跌 | 市值 |
|------|------|------|----------|------|
{coins_table}

## 3. 情感分析结果

### 3.1 情感分布

| 情感类型 | 数量 | 占比 |
|----------|------|------|
| 看涨 (Bullish) | {results['analysis']['sentiment_distribution'].get('bullish', 0)} | {100*results['analysis']['sentiment_distribution'].get('bullish', 0)/results['analysis'].get('total_analyzed', 1):.1f}% |
| 看跌 (Bearish) | {results['analysis']['sentiment_distribution'].get('bearish', 0)} | {100*results['analysis']['sentiment_distribution'].get('bearish', 0)/results['analysis'].get('total_analyzed', 1):.1f}% |
| 中性 (Neutral) | {results['analysis']['sentiment_distribution'].get('neutral', 0)} | {100*results['analysis']['sentiment_distribution'].get('neutral', 0)/results['analysis'].get('total_analyzed', 1):.1f}% |

### 3.2 预测性分析

- 预测性语句: {results['analysis'].get('predictive_count', 0)}/{results['analysis'].get('total_analyzed', 0)} ({100*results['analysis'].get('predictive_count', 0)/results['analysis'].get('total_analyzed', 1):.1f}%)

### 3.3 方向分布

| 方向 | 数量 |
|------|------|
| 增量 (Incremental) | {results['analysis']['direction_distribution'].get('incremental', 0)} |
| 减量 (Decremental) | {results['analysis']['direction_distribution'].get('decremental', 0)} |
| 中性 (Neutral) | {results['analysis']['direction_distribution'].get('neutral', 0)} |
| 无方向 (Null) | {results['analysis']['direction_distribution'].get('null', 0)} |

## 4. 高级特征工程

### 4.1 PCA 方差解释

| 主成分 | 方差解释比例 | 累积方差解释 |
|--------|--------------|--------------|
| PC1 | {results['analysis'].get('pca_variance', [0, 0, 0, 0, 0])[0]:.2%} | {results['analysis'].get('pca_variance', [0, 0, 0, 0, 0])[0]:.2%} |
| PC2 | {results['analysis'].get('pca_variance', [0, 0, 0, 0, 0])[1]:.2%} | {sum(results['analysis'].get('pca_variance', [0, 0, 0, 0, 0])[:2]):.2%} |
| PC3 | {results['analysis'].get('pca_variance', [0, 0, 0, 0, 0])[2]:.2%} | {sum(results['analysis'].get('pca_variance', [0, 0, 0, 0, 0])[:3]):.2%} |
| PC4 | {results['analysis'].get('pca_variance', [0, 0, 0, 0, 0])[3]:.2%} | {sum(results['analysis'].get('pca_variance', [0, 0, 0, 0, 0])[:4]):.2%} |
| PC5 | {results['analysis'].get('pca_variance', [0, 0, 0, 0, 0])[4]:.2%} | {sum(results['analysis'].get('pca_variance', [0, 0, 0, 0, 0])[:5]):.2%} |

### 4.2 价格标签分布（K-means 聚类）

| 标签 | 含义 | 数量 |
|------|------|------|
| 0 | 下跌 | {results['analysis'].get('price_labels', []).count(0)} |
| 1 | 中性 | {results['analysis'].get('price_labels', []).count(1)} |
| 2 | 上涨 | {results['analysis'].get('price_labels', []).count(2)} |

## 5. 总结

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
    run_full_test()
