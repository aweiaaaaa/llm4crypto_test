"""
大规模数据采集与分析测试脚本
测试规模：
- CoinGecko: 250条市场数据
- Twitter: 多个关键词，每个50条推文
- 完整管道运行
"""

import time
import json
from datetime import datetime
from collectors.coingecko_collector import CoinGeckoCollector
from collectors.twitter_scweet_collector import TwitterScweetCollector
from cleaners.data_cleaner import DataCleaner
from analyzers.llm_analyzer import LLMAnalyzer
from configs.config import Config
from utils.helpers import logger, save_to_json

def run_large_scale_test():
    print("=" * 70)
    print("          大规模数据采集与分析测试")
    print("=" * 70)
    
    test_results = {
        'timestamp': datetime.now().isoformat(),
        'collection': {},
        'cleaning': {},
        'analysis': {},
        'quality_metrics': {}
    }
    
    # ==================== 1. 数据采集阶段 ====================
    print("\n【阶段 1/4】数据采集")
    print("-" * 70)
    
    start_collection = time.time()
    
    # 1.1 CoinGecko 采集
    print("\n1.1 采集 CoinGecko 市场数据 (250 条)...")
    coingecko_collector = CoinGeckoCollector()
    coingecko_data = coingecko_collector.get_coins_market_data('usd', per_page=250)
    print(f"    [OK] 采集完成：{len(coingecko_data)} 条")
    
    # 保存原始数据
    coingecko_raw_file = f"{Config.RAW_DATA_DIR}/coingecko_market_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_to_json(coingecko_data, coingecko_raw_file)
    print(f"    [OK] 数据已保存：{coingecko_raw_file}")
    
    test_results['collection']['coingecko'] = {
        'count': len(coingecko_data),
        'expected': 250,
        'file': coingecko_raw_file
    }
    
    # 1.2 Twitter 采集
    print("\n1.2 采集 Twitter 数据...")
    twitter_collector = TwitterScweetCollector()
    
    # 多关键词搜索
    keywords = ['$BTC', '$ETH', '$SOL', 'Bitcoin', 'Ethereum', 'cryptocurrency']
    all_tweets = []
    
    for keyword in keywords:
        print(f"    搜索关键词：{keyword}...")
        tweets = twitter_collector.search_tweets([keyword], limit=50)
        print(f"      找到 {len(tweets)} 条推文")
        all_tweets.extend(tweets)
        time.sleep(2)  # 避免频率限制
    
    # 保存 Twitter 数据
    twitter_raw_file = f"{Config.RAW_DATA_DIR}/twitter_tweets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    twitter_collector.save_tweets(all_tweets, f"twitter_tweets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    print(f"    [OK] 采集完成：{len(all_tweets)} 条")
    print(f"    [OK] 数据已保存：{twitter_raw_file}")
    
    test_results['collection']['twitter'] = {
        'count': len(all_tweets),
        'keywords': keywords,
        'file': twitter_raw_file
    }
    
    collection_time = time.time() - start_collection
    test_results['collection']['total_time'] = collection_time
    print(f"\n采集阶段完成，耗时：{collection_time:.2f}秒")
    
    # ==================== 2. 数据清洗阶段 ====================
    print("\n【阶段 2/4】数据清洗")
    print("-" * 70)
    
    start_cleaning = time.time()
    cleaner = DataCleaner()
    
    # 2.1 清洗 CoinGecko 数据
    print("\n2.1 清洗 CoinGecko 数据...")
    coingecko_cleaned = cleaner.clean_coingecko_data(coingecko_data)
    print(f"    [OK] 清洗完成：{len(coingecko_cleaned)} 条")
    print(f"    [OK] 过滤率：{(1 - len(coingecko_cleaned)/len(coingecko_data))*100:.1f}%")
    
    # 2.2 清洗 Twitter 数据
    print("\n2.2 清洗 Twitter 数据...")
    twitter_cleaned = cleaner.clean_twitter_data(all_tweets)
    print(f"    [OK] 清洗完成：{len(twitter_cleaned)} 条")
    if len(all_tweets) > 0:
        print(f"    [OK] 过滤率：{(1 - len(twitter_cleaned)/len(all_tweets))*100:.1f}%")
    else:
        print(f"    [INFO] 无原始数据，跳过过滤率计算")
    
    # 2.3 数据质量报告
    print("\n2.3 生成数据质量报告...")
    all_cleaned = coingecko_cleaned + twitter_cleaned
    quality_report = cleaner.get_data_quality_report(all_cleaned)
    
    print(f"    总记录数：{quality_report['total_records']}")
    print(f"    有代币的记录：{quality_report['records_with_tokens']} ({quality_report['percentage_with_tokens']:.1f}%)")
    print(f"    平均文本长度：{quality_report['avg_text_length']:.1f}")
    print(f"    数据源分布：{quality_report['source_distribution']}")
    
    cleaning_time = time.time() - start_cleaning
    test_results['cleaning'] = {
        'coingecko': {
            'raw_count': len(coingecko_data),
            'cleaned_count': len(coingecko_cleaned),
            'filter_rate': (1 - len(coingecko_cleaned)/len(coingecko_data))*100
        },
        'twitter': {
            'raw_count': len(all_tweets),
            'cleaned_count': len(twitter_cleaned),
            'filter_rate': (1 - len(twitter_cleaned)/len(all_tweets))*100
        },
        'quality_report': quality_report,
        'total_time': cleaning_time
    }
    
    print(f"\n清洗阶段完成，耗时：{cleaning_time:.2f}秒")
    
    # ==================== 3. LLM 分析阶段 ====================
    print("\n【阶段 3/4】LLM 情绪分析")
    print("-" * 70)
    
    start_analysis = time.time()
    analyzer = LLMAnalyzer()
    
    print(f"\nAPI 配置：{analyzer.base_url}")
    print(f"模型：{analyzer.model}")
    
    # 3.1 抽样分析（前50条）
    print(f"\n分析样本数据 (50条)...")
    sample_data = all_cleaned[:50]
    
    analysis_results = []
    for i, item in enumerate(sample_data):
        text = item.get('text', '')
        if not text:
            continue
            
        result = analyzer.analyze_text(text)
        if result:
            result['source'] = item.get('source', 'unknown')
            result['original_text'] = text[:100]
            analysis_results.append(result)
        
        if (i + 1) % 10 == 0:
            print(f"    已分析 {i+1}/{len(sample_data)} 条...")
    
    # 3.2 统计结果
    sentiment_stats = {}
    importance_sum = 0
    for result in analysis_results:
        sentiment = result.get('sentiment', 'unknown')
        sentiment_stats[sentiment] = sentiment_stats.get(sentiment, 0) + 1
        importance_sum += result.get('importance', 0)
    
    avg_importance = importance_sum / len(analysis_results) if analysis_results else 0
    
    print(f"\n分析结果统计:")
    print(f"    总分析数：{len(analysis_results)}")
    print(f"    平均重要性：{avg_importance:.2f}/10")
    print(f"    情绪分布：{sentiment_stats}")
    
    analysis_time = time.time() - start_analysis
    test_results['analysis'] = {
        'sample_size': len(sample_data),
        'analyzed_count': len(analysis_results),
        'sentiment_distribution': sentiment_stats,
        'avg_importance': avg_importance,
        'total_time': analysis_time
    }
    
    print(f"\n分析阶段完成，耗时：{analysis_time:.2f}秒")
    
    # ==================== 4. 结果汇总 ====================
    print("\n【阶段 4/4】测试结果汇总")
    print("-" * 70)
    
    total_time = collection_time + cleaning_time + analysis_time
    
    print(f"\n总体统计:")
    print(f"    采集数据总量：{len(coingecko_data) + len(all_tweets)} 条")
    print(f"    清洗后数据量：{len(all_cleaned)} 条")
    print(f"    分析数据量：{len(analysis_results)} 条")
    print(f"    总耗时：{total_time:.2f}秒")
    print(f"    其中:")
    print(f"      - 采集：{collection_time:.2f}秒")
    print(f"      - 清洗：{cleaning_time:.2f}秒")
    print(f"      - 分析：{analysis_time:.2f}秒")
    
    # 保存测试结果
    test_results['total_time'] = total_time
    test_results_file = f"data/test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_to_json(test_results, test_results_file)
    print(f"\n测试结果已保存：{test_results_file}")
    
    print("\n" + "=" * 70)
    print("          大规模测试完成！")
    print("=" * 70)
    
    return test_results, coingecko_data, all_tweets, coingecko_cleaned, twitter_cleaned, analysis_results

if __name__ == "__main__":
    test_results, *data = run_large_scale_test()
