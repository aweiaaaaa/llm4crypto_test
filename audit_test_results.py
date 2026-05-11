"""
大规模测试结果详细审计脚本
对测试结果进行全面审计，检查准确性、完整性和数据质量
"""

import json
from datetime import datetime
from glob import glob
from cleaners.data_cleaner import DataCleaner

def audit_test_results():
    print("=" * 70)
    print("          大规模测试结果详细审计报告")
    print("=" * 70)
    
    audit_report = {
        'timestamp': datetime.now().isoformat(),
        'data_collection_audit': {},
        'data_cleaning_audit': {},
        'llm_analysis_audit': {},
        'accuracy_verification': {},
        'issues_found': []
    }
    
    # ==================== 1. 数据采集审计 ====================
    print("\n【审计 1/4】数据采集审计")
    print("-" * 70)
    
    # 加载最新数据
    coingecko_files = glob('data/raw/coingecko_market_*.json')
    twitter_files = glob('data/raw/twitter_tweets_*.json')
    
    latest_coingecko = max(coingecko_files, key=lambda x: x)
    latest_twitter = max(twitter_files, key=lambda x: x)
    
    with open(latest_coingecko, 'r', encoding='utf-8') as f:
        coingecko_raw = json.load(f)
    
    with open(latest_twitter, 'r', encoding='utf-8') as f:
        twitter_raw = json.load(f)
    
    print(f"\n1.1 CoinGecko 数据采集审计:")
    print(f"    文件：{latest_coingecko}")
    print(f"    采集数量：{len(coingecko_raw)} 条")
    
    # 审计数据完整性
    required_fields = ['id', 'symbol', 'name', 'current_price', 'market_cap']
    complete_count = sum(1 for item in coingecko_raw if all(field in item for field in required_fields))
    completeness = complete_count / len(coingecko_raw) * 100
    
    print(f"    字段完整性：{complete_count}/{len(coingecko_raw)} ({completeness:.1f}%)")
    
    # 审计价格数据
    valid_prices = sum(1 for item in coingecko_raw if item.get('current_price') and item['current_price'] > 0)
    price_validity = valid_prices / len(coingecko_raw) * 100
    
    print(f"    价格有效性：{valid_prices}/{len(coingecko_raw)} ({price_validity:.1f}%)")
    
    # 审计市值排名
    ranked = sum(1 for item in coingecko_raw if item.get('market_cap_rank'))
    rank_validity = ranked / len(coingecko_raw) * 100
    
    print(f"    市值排名：{ranked}/{len(coingecko_raw)} ({rank_validity:.1f}%)")
    
    # 抽样检查数据准确性
    print(f"\n    抽样检查（前 5 条）：")
    for i, item in enumerate(coingecko_raw[:5], 1):
        print(f"      {i}. {item.get('name', 'N/A')} ({item.get('symbol', 'N/A')}) - ${item.get('current_price', 0):,.2f}")
    
    audit_report['data_collection_audit']['coingecko'] = {
        'count': len(coingecko_raw),
        'completeness': completeness,
        'price_validity': price_validity,
        'rank_validity': rank_validity,
        'status': 'PASS' if completeness == 100 and price_validity == 100 else 'FAIL'
    }
    
    print(f"\n    CoinGecko 采集审计结果：{'[PASS]' if completeness == 100 and price_validity == 100 else '[FAIL]'}")
    
    print(f"\n1.2 Twitter 数据采集审计:")
    print(f"    文件：{latest_twitter}")
    print(f"    采集数量：{len(twitter_raw)} 条")
    
    if twitter_raw:
        # 审计字段完整性
        required_fields = ['tweet_text', 'author_handle', 'timestamp']
        complete_count = sum(1 for item in twitter_raw if all(field in item for field in required_fields))
        completeness = complete_count / len(twitter_raw) * 100
        
        print(f"    字段完整性：{complete_count}/{len(twitter_raw)} ({completeness:.1f}%)")
        
        # 审计文本质量
        text_lengths = [len(item.get('tweet_text', '')) for item in twitter_raw]
        avg_length = sum(text_lengths) / len(text_lengths) if text_lengths else 0
        min_length = min(text_lengths) if text_lengths else 0
        max_length = max(text_lengths) if text_lengths else 0
        
        print(f"    文本长度：平均 {avg_length:.1f}, 最小 {min_length}, 最大 {max_length}")
        
        # 审计互动数据
        def safe_int(value):
            try:
                return int(value) if value else 0
            except (ValueError, TypeError):
                return 0
        
        with_likes = sum(1 for item in twitter_raw if safe_int(item.get('likes')) > 0)
        with_retweets = sum(1 for item in twitter_raw if safe_int(item.get('retweets')) > 0)
        
        print(f"    有点赞数据：{with_likes}/{len(twitter_raw)} ({with_likes/len(twitter_raw)*100:.1f}%)")
        print(f"    有转发数据：{with_retweets}/{len(twitter_raw)} ({with_retweets/len(twitter_raw)*100:.1f}%)")
        
        # 抽样检查数据准确性
        print(f"\n    抽样检查（前 3 条）：")
        for i, item in enumerate(twitter_raw[:3], 1):
            text = item.get('tweet_text', '')[:60]
            author = item.get('author_handle', 'N/A')
            print(f"      {i}. @{author}: {text}...")
        
        audit_report['data_collection_audit']['twitter'] = {
            'count': len(twitter_raw),
            'completeness': completeness,
            'avg_text_length': avg_length,
            'with_likes': with_likes/len(twitter_raw)*100,
            'status': 'PASS' if completeness == 100 else 'FAIL'
        }
        
        print(f"\n    Twitter 采集审计结果：{'[PASS]' if completeness == 100 else '[FAIL]'}")
    else:
        print(f"    [WARN] 无 Twitter 数据")
        audit_report['data_collection_audit']['twitter'] = {
            'count': 0,
            'status': 'FAIL',
            'reason': 'No data collected'
        }
    
    # ==================== 2. 数据清洗审计 ====================
    print("\n【审计 2/4】数据清洗审计")
    print("-" * 70)
    
    cleaner = DataCleaner()
    
    # 清洗 CoinGecko 数据
    print(f"\n2.1 CoinGecko 数据清洗审计:")
    coingecko_cleaned = cleaner.clean_coingecko_data(coingecko_raw)
    
    cg_filter_rate = (1 - len(coingecko_cleaned)/len(coingecko_raw)) * 100
    print(f"    原始数据：{len(coingecko_raw)} 条")
    print(f"    清洗后：{len(coingecko_cleaned)} 条")
    print(f"    过滤率：{cg_filter_rate:.1f}%")
    
    # 审计代币提取
    with_tokens = sum(1 for item in coingecko_cleaned if item.get('tokens'))
    token_rate = with_tokens / len(coingecko_cleaned) * 100 if coingecko_cleaned else 0
    
    print(f"    代币提取：{with_tokens}/{len(coingecko_cleaned)} ({token_rate:.1f}%)")
    
    audit_report['data_cleaning_audit']['coingecko'] = {
        'raw_count': len(coingecko_raw),
        'cleaned_count': len(coingecko_cleaned),
        'filter_rate': cg_filter_rate,
        'token_extraction_rate': token_rate,
        'status': 'PASS' if token_rate == 100 else 'FAIL'
    }
    
    # 清洗 Twitter 数据
    print(f"\n2.2 Twitter 数据清洗审计:")
    if twitter_raw:
        twitter_cleaned = cleaner.clean_twitter_data(twitter_raw)
        
        tw_filter_rate = (1 - len(twitter_cleaned)/len(twitter_raw)) * 100
        print(f"    原始数据：{len(twitter_raw)} 条")
        print(f"    清洗后：{len(twitter_cleaned)} 条")
        print(f"    过滤率：{tw_filter_rate:.1f}%")
        
        # 审计代币提取
        with_tokens = sum(1 for item in twitter_cleaned if item.get('tokens'))
        token_rate = with_tokens / len(twitter_cleaned) * 100 if twitter_cleaned else 0
        
        print(f"    代币提取：{with_tokens}/{len(twitter_cleaned)} ({token_rate:.1f}%)")
        
        # 审计文本质量
        text_lengths = [len(item.get('text', '')) for item in twitter_cleaned]
        avg_length = sum(text_lengths) / len(text_lengths) if text_lengths else 0
        
        print(f"    平均文本长度：{avg_length:.1f} 字符")
        
        # 审计 LLM 分析准备度
        ready_for_llm = sum(1 for item in twitter_cleaned if item.get('text') and len(item['text']) > 20)
        llm_readiness = ready_for_llm / len(twitter_cleaned) * 100 if twitter_cleaned else 0
        
        print(f"    LLM 分析准备度：{ready_for_llm}/{len(twitter_cleaned)} ({llm_readiness:.1f}%)")
        
        audit_report['data_cleaning_audit']['twitter'] = {
            'raw_count': len(twitter_raw),
            'cleaned_count': len(twitter_cleaned),
            'filter_rate': tw_filter_rate,
            'token_extraction_rate': token_rate,
            'llm_readiness': llm_readiness,
            'status': 'PASS' if tw_filter_rate < 50 and token_rate > 80 else 'FAIL'
        }
        
        print(f"\n    Twitter 清洗审计结果：{'[PASS]' if tw_filter_rate < 50 and token_rate > 80 else '[FAIL]'}")
    else:
        print(f"    [SKIP] 无 Twitter 数据可清洗")
    
    # ==================== 3. LLM 分析审计 ====================
    print("\n【审计 3/4】LLM 分析审计")
    print("-" * 70)
    
    from analyzers.llm_analyzer import LLMAnalyzer
    
    print(f"\n3.1 LLM 配置审计:")
    analyzer = LLMAnalyzer()
    
    print(f"    API 配置：{analyzer.base_url}")
    print(f"    模型：{analyzer.model}")
    print(f"    API Key：{'已配置' if analyzer.api_key else '未配置'}")
    print(f"    Mock 模式：{'是' if analyzer.use_mock else '否'}")
    
    audit_report['llm_analysis_audit']['configuration'] = {
        'base_url': analyzer.base_url,
        'model': analyzer.model,
        'api_key_configured': bool(analyzer.api_key),
        'use_mock': analyzer.use_mock,
        'status': 'PASS' if analyzer.api_key and not analyzer.use_mock else 'FAIL'
    }
    
    # 测试 LLM 分析功能
    print(f"\n3.2 LLM 分析功能测试:")
    
    test_texts = [
        "Bitcoin price surges to new all-time high!",
        "Market crash, crypto prices plummeting",
        "Ethereum upgrade scheduled for next month"
    ]
    
    analysis_results = []
    for i, text in enumerate(test_texts, 1):
        print(f"    测试 {i}: {text[:40]}...")
        result = analyzer.analyze_text(text)
        
        if result:
            print(f"      情绪：{result.get('sentiment', 'N/A')}")
            print(f"      重要性：{result.get('importance', 'N/A')}/10")
            print(f"      时间尺度：{result.get('time_horizon', 'N/A')}")
            analysis_results.append(result)
        else:
            print(f"      [FAIL] 分析失败")
    
    audit_report['llm_analysis_audit']['functionality'] = {
        'test_count': len(test_texts),
        'success_count': len(analysis_results),
        'success_rate': len(analysis_results)/len(test_texts)*100 if test_texts else 0,
        'status': 'PASS' if len(analysis_results) == len(test_texts) else 'FAIL'
    }
    
    print(f"\n    LLM 分析功能审计结果：{'[PASS]' if len(analysis_results) == len(test_texts) else '[FAIL]'}")
    
    # ==================== 4. 准确性验证 ====================
    print("\n【审计 4/4】准确性验证")
    print("-" * 70)
    
    print(f"\n4.1 数据量准确性验证:")
    
    expected_coingecko = 250
    actual_coingecko = len(coingecko_raw)
    coingecko_accuracy = (actual_coingecko / expected_coingecko) * 100 if expected_coingecko > 0 else 0
    
    print(f"    CoinGecko 期望：{expected_coingecko} 条")
    print(f"    CoinGecko 实际：{actual_coingecko} 条")
    print(f"    准确性：{coingecko_accuracy:.1f}%")
    
    audit_report['accuracy_verification']['coingecko_count'] = {
        'expected': expected_coingecko,
        'actual': actual_coingecko,
        'accuracy': coingecko_accuracy,
        'status': 'PASS' if coingecko_accuracy >= 95 else 'FAIL'
    }
    
    if twitter_raw:
        expected_twitter_min = 50
        actual_twitter = len(twitter_raw)
        twitter_accuracy = (actual_twitter / expected_twitter_min) * 100 if expected_twitter_min > 0 else 0
        
        print(f"\n    Twitter 期望：≥{expected_twitter_min} 条")
        print(f"    Twitter 实际：{actual_twitter} 条")
        print(f"    准确性：{twitter_accuracy:.1f}%")
        
        audit_report['accuracy_verification']['twitter_count'] = {
            'expected_min': expected_twitter_min,
            'actual': actual_twitter,
            'accuracy': twitter_accuracy,
            'status': 'PASS' if actual_twitter >= expected_twitter_min else 'FAIL'
        }
    
    print(f"\n4.2 数据质量准确性验证:")
    
    # 验证 CoinGecko 价格数据
    price_errors = sum(1 for item in coingecko_raw if not item.get('current_price') or item['current_price'] <= 0)
    price_accuracy = ((len(coingecko_raw) - price_errors) / len(coingecko_raw)) * 100 if coingecko_raw else 0
    
    print(f"    CoinGecko 价格准确性：{price_accuracy:.1f}% ({len(coingecko_raw) - price_errors}/{len(coingecko_raw)})")
    
    audit_report['accuracy_verification']['price_data'] = {
        'accuracy': price_accuracy,
        'errors': price_errors,
        'status': 'PASS' if price_accuracy == 100 else 'FAIL'
    }
    
    # 验证 Twitter 文本数据
    if twitter_raw:
        text_errors = sum(1 for item in twitter_raw if not item.get('tweet_text') or len(item['tweet_text']) < 5)
        text_accuracy = ((len(twitter_raw) - text_errors) / len(twitter_raw)) * 100 if twitter_raw else 0
        
        print(f"    Twitter 文本准确性：{text_accuracy:.1f}% ({len(twitter_raw) - text_errors}/{len(twitter_raw)})")
        
        audit_report['accuracy_verification']['twitter_text'] = {
            'accuracy': text_accuracy,
            'errors': text_errors,
            'status': 'PASS' if text_accuracy >= 95 else 'FAIL'
        }
    
    # ==================== 5. 综合评估 ====================
    print("\n" + "=" * 70)
    print("综合评估")
    print("-" * 70)
    
    # 统计审计结果
    all_audits = []
    
    if 'coingecko' in audit_report['data_collection_audit']:
        all_audits.append(audit_report['data_collection_audit']['coingecko']['status'])
    if 'twitter' in audit_report['data_collection_audit']:
        all_audits.append(audit_report['data_collection_audit']['twitter']['status'])
    all_audits.append(audit_report['data_cleaning_audit']['coingecko']['status'])
    if 'twitter' in audit_report['data_cleaning_audit']:
        all_audits.append(audit_report['data_cleaning_audit']['twitter']['status'])
    all_audits.append(audit_report['llm_analysis_audit']['configuration']['status'])
    all_audits.append(audit_report['llm_analysis_audit']['functionality']['status'])
    all_audits.append(audit_report['accuracy_verification']['coingecko_count']['status'])
    all_audits.append(audit_report['accuracy_verification']['price_data']['status'])
    
    pass_count = sum(1 for status in all_audits if status == 'PASS')
    total_count = len(all_audits)
    pass_rate = pass_count / total_count * 100 if total_count > 0 else 0
    
    print(f"\n审计项目总数：{total_count}")
    print(f"通过项目数：{pass_count}")
    print(f"通过率：{pass_rate:.1f}%")
    
    overall_status = 'PASS' if pass_rate >= 80 else 'FAIL'
    print(f"\n总体审计结果：[{overall_status}]")
    
    audit_report['overall_status'] = overall_status
    audit_report['pass_rate'] = pass_rate
    audit_report['pass_count'] = pass_count
    audit_report['total_count'] = total_count
    
    # 保存审计报告
    report_file = f"data/audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(audit_report, f, ensure_ascii=False, indent=2)
    
    print(f"\n详细审计报告已保存：{report_file}")
    print("=" * 70)
    
    return audit_report

if __name__ == "__main__":
    audit_report = audit_test_results()
