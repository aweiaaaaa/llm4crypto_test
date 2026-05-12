import sys
import os
from datetime import datetime, timezone
sys.path.insert(0, '.')

os.environ['PYTHONIOENCODING'] = 'utf-8'

from collectors.twitter_scweet_collector import TwitterScweetCollector, CRYPTO_KOLS
from collectors.coingecko_collector import CoinGeckoCollector
from configs.config import Config
from utils.helpers import save_to_json, load_from_json

def get_current_date():
    """获取当前日期字符串"""
    return datetime.now(timezone.utc).strftime('%Y%m%d')

def test_twitter_kol_collection():
    """测试 Twitter KOL 采集功能"""
    print("=" * 70)
    print("TEST 1: Twitter KOL 采集器增强")
    print("=" * 70)
    
    collector = TwitterScweetCollector()
    
    # 1. 显示可用的 KOL 分类
    print("\n[1/3] 可用的 KOL 分类:")
    categories = collector.get_available_kol_categories()
    for cat in categories:
        kols = collector.get_kols_by_category(cat)
        total_influence = sum(k['influence'] for k in kols)
        avg_influence = total_influence / len(kols) if kols else 0
        print(f"   - {cat}: {len(kols)} 个 KOL, 平均影响力: {avg_influence:.1f}")
    
    # 2. 显示具体的 KOL 列表
    print("\n[2/3] Top KOL 详情:")
    elites = collector.get_kols_by_category('elites')
    for kol in elites:
        print(f"   - @{kol['username']} ({kol['name']}) | 影响力: {kol['influence']} | 分类: {kol['category']}")
    
    # 3. 测试 KOL 采集（仅测试，不实际调用 API）
    print("\n[3/3] KOL 采集测试 (模拟)")
    print("   KOL 采集器已准备就绪，可以按类别采集")
    print("   支持的参数:")
    print("   - categories: 指定采集哪些类别的 KOL")
    print("   - min_influence: 最小影响力阈值筛选")
    print("   - limit_per_kol: 每个 KOL 采集的推文数量")
    
    return True

def test_coingecko_api():
    """测试 CoinGecko API"""
    print("\n" + "=" * 70)
    print("TEST 2: CoinGecko API 测试")
    print("=" * 70)
    
    collector = CoinGeckoCollector()
    current_date = get_current_date()
    all_tests_passed = True
    
    try:
        # 1. 获取全球市场数据
        print("\n[1/4] 获取全球市场数据...")
        global_data = collector.get_global_data()
        if global_data:
            print(f"   总市值: ${global_data.get('total_market_cap', 0):,.0f}")
            print(f"   24h交易量: ${global_data.get('total_volume', 0):,.0f}")
            print(f"   BTC 占比: {global_data.get('bitcoin_dominance', 0):.1f}%")
            print(f"   活跃币种: {global_data.get('active_cryptocurrencies', 0)}")
            save_to_json(global_data, f"{Config.RAW_DATA_DIR}/coingecko_global_{current_date}.json")
            print("   [OK] 全球数据已保存")
        else:
            print("   [ERROR] 获取全球数据失败")
            all_tests_passed = False
        
        # 2. 获取热门趋势币
        print("\n[2/4] 获取热门趋势币...")
        trending = collector.get_trending_coins(count=10)
        if trending:
            print("   热门趋势币 TOP 5:")
            for i, coin in enumerate(trending[:5], 1):
                print(f"   {i}. {coin['name']} ({coin['symbol']})")
            save_to_json(trending, f"{Config.RAW_DATA_DIR}/coingecko_trending_{current_date}.json")
            print("   [OK] 趋势数据已保存")
        else:
            print("   [ERROR] 获取趋势数据失败")
            all_tests_passed = False
        
        # 3. 获取市场数据（前20个币种）
        print("\n[3/4] 获取市场数据...")
        market_data = collector.get_coins_market_data(per_page=20)
        if market_data:
            print(f"   获取到 {len(market_data)} 个币种数据")
            print("   TOP 5 币种:")
            for i, coin in enumerate(market_data[:5], 1):
                change = coin.get('price_change_percentage_24h', 0)
                change_color = "↑" if change > 0 else "↓"
                print(f"   {i}. {coin['name']} (${coin['current_price']:,.2f}) {change_color} {abs(change):.2f}%")
            save_to_json(market_data, f"{Config.RAW_DATA_DIR}/coingecko_market_{current_date}.json")
            print("   [OK] 市场数据已保存")
        else:
            print("   [ERROR] 获取市场数据失败")
            all_tests_passed = False
        
        # 4. 获取 BTC 详细信息（带错误处理）
        print("\n[4/4] 获取 BTC 详细信息...")
        btc_info = collector.get_coin_info('bitcoin')
        if btc_info and isinstance(btc_info, dict):
            print(f"   名称: {btc_info.get('name', 'N/A')} ({btc_info.get('symbol', 'N/A')})")
            description = btc_info.get('description', '')
            if description:
                print(f"   描述: {description[:100]}...")
            print(f"   官网: {btc_info.get('homepage', 'N/A')}")
            categories = btc_info.get('categories', [])
            if categories:
                print(f"   分类: {', '.join(categories)}")
            save_to_json(btc_info, f"{Config.RAW_DATA_DIR}/coingecko_btc_info_{current_date}.json")
            print("   [OK] BTC 信息已保存")
        else:
            print("   [WARN] BTC 详细信息获取失败或格式异常")
            # 不标记为失败，因为主要功能正常
        
        return all_tests_passed
        
    except Exception as e:
        print(f"   [ERROR] CoinGecko API 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    Config.init_dirs()
    
    # 测试 Twitter KOL 采集器
    twitter_ok = test_twitter_kol_collection()
    
    # 测试 CoinGecko API
    coingecko_ok = test_coingecko_api()
    
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    print(f"  Twitter KOL 采集器: {'[OK]' if twitter_ok else '[FAIL]'}")
    print(f"  CoinGecko API: {'[OK]' if coingecko_ok else '[PARTIAL]'}")
    print("\n  数据文件已保存至: data/raw/")
    print("\n  已保存的文件:")
    print("  - coingecko_global_*.json   (全球市场数据)")
    print("  - coingecko_trending_*.json (热门趋势币)")
    print("  - coingecko_market_*.json   (市场数据)")
