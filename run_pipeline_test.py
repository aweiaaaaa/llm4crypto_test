import sys
sys.path.insert(0, '.')

from configs.config import Config
from collectors.coinmarketcal_collector import CoinMarketCalCollector
from collectors.twitter_scweet_collector import TwitterScweetCollector
from cleaners.data_cleaner import DataCleaner
from analyzers.llm_analyzer import LLMAnalyzer
from utils.helpers import logger, load_from_json, save_to_json
from datetime import datetime
import json
import os

print("=" * 70)
print("FULL DATA COLLECTION AND ANALYSIS PIPELINE")
print("=" * 70)

Config.init_dirs()

# Step 1: CoinMarketCal Collection
print("\n[Step 1/4] CoinMarketCal Data Collection")
print("-" * 50)
cmc_count = 0
try:
    cmc = CoinMarketCalCollector()
    cmc.collect_and_save()
    # Count saved events
    cmc_file = f"{Config.RAW_DATA_DIR}/coinmarketcal_events_{datetime.now().strftime('%Y%m%d')}.json"
    if os.path.exists(cmc_file):
        with open(cmc_file, 'r', encoding='utf-8') as f:
            cmc_data = json.load(f)
            cmc_count = len(cmc_data) if isinstance(cmc_data, list) else 0
    print(f"  [OK] CoinMarketCal: {cmc_count} events collected")
except Exception as e:
    print(f"  [ERROR] CoinMarketCal: {e}")
    import traceback
    traceback.print_exc()

# Step 2: Twitter/X Collection
print("\n[Step 2/4] Twitter/X Data Collection")
print("-" * 50)
tw_count = 0
try:
    if Config.TWITTER_AUTH_TOKEN:
        twitter = TwitterScweetCollector()
        twitter.collect_and_save()
        tw_count = twitter.get_last_collection_count()
        print(f"  [OK] Twitter/X: {tw_count} tweets collected")
    else:
        print("  [WARN] No Twitter auth_token configured")
except Exception as e:
    print(f"  [ERROR] Twitter/X: {e}")

# Step 3: Data Cleaning
print("\n[Step 3/4] Data Cleaning")
print("-" * 50)
cleaner = DataCleaner()
cleaned_count = 0

try:
    # Clean Twitter data
    if tw_count > 0:
        twitter_file = f"{Config.RAW_DATA_DIR}/twitter_tweets_{datetime.now().strftime('%Y%m%d')}.json"
        if os.path.exists(twitter_file):
            raw_twitter = load_from_json(twitter_file)
            if raw_twitter:
                cleaned_twitter = cleaner.clean_twitter_data(raw_twitter)
                cleaned_twitter_file = f"{Config.CLEANED_DATA_DIR}/cleaned_twitter_{datetime.now().strftime('%Y%m%d')}.json"
                save_to_json(cleaned_twitter, cleaned_twitter_file)
                cleaned_count += len(cleaned_twitter)
                print(f"  [OK] Twitter cleaned: {len(cleaned_twitter)} records")

    # Clean CoinMarketCal data
    if cmc_count > 0:
        cmc_file = f"{Config.RAW_DATA_DIR}/coinmarketcal_events_{datetime.now().strftime('%Y%m%d')}.json"
        if os.path.exists(cmc_file):
            raw_cmc = load_from_json(cmc_file)
            if raw_cmc:
                cleaned_cmc = cleaner.clean_coinmarketcal_data(raw_cmc)
                cleaned_cmc_file = f"{Config.CLEANED_DATA_DIR}/cleaned_coinmarketcal_{datetime.now().strftime('%Y%m%d')}.json"
                save_to_json(cleaned_cmc, cleaned_cmc_file)
                cleaned_count += len(cleaned_cmc)
                print(f"  [OK] CoinMarketCal cleaned: {len(cleaned_cmc)} records")

    print(f"  [INFO] Total cleaned: {cleaned_count} records")
except Exception as e:
    print(f"  [ERROR] Data cleaning: {e}")
    import traceback
    traceback.print_exc()

# Step 4: LLM Analysis
print("\n[Step 4/4] LLM Analysis with Hybrid Prompt")
print("-" * 50)
all_results = []

try:
    analyzer = LLMAnalyzer()

    # Load and analyze cleaned data
    if cleaned_count > 0:
        # Twitter analysis
        twitter_cleaned = f"{Config.CLEANED_DATA_DIR}/cleaned_twitter_{datetime.now().strftime('%Y%m%d')}.json"
        if os.path.exists(twitter_cleaned):
            twitter_data = load_from_json(twitter_cleaned)
            if twitter_data:
                # Extract text from tweets for analysis
                texts = []
                for item in twitter_data:
                    if isinstance(item, dict) and 'text' in item:
                        texts.append(item['text'])
                    elif isinstance(item, dict) and 'full_text' in item:
                        texts.append(item['full_text'])

                if texts:
                    print(f"  [INFO] Analyzing {len(texts)} Twitter texts...")
                    # Convert strings to dict format for analyze_dataset
                    twitter_texts = [{'text': t} for t in texts]
                    results = analyzer.analyze_dataset(twitter_texts)
                    all_results.extend(results)
                    print(f"  [OK] Twitter analyzed: {len(results)} records")

        # CoinMarketCal analysis
        cmc_cleaned = f"{Config.CLEANED_DATA_DIR}/cleaned_coinmarketcal_{datetime.now().strftime('%Y%m%d')}.json"
        if os.path.exists(cmc_cleaned):
            cmc_data = load_from_json(cmc_cleaned)
            if cmc_data:
                texts = []
                for item in cmc_data:
                    if isinstance(item, dict):
                        desc = item.get('description', '')
                        title = item.get('title', '')
                        text = f"{title}. {desc}".strip()
                        if text:
                            texts.append(text)

                if texts:
                    print(f"  [INFO] Analyzing {len(texts)} CoinMarketCal texts...")
                    results = analyzer.analyze_dataset(texts)
                    all_results.extend(results)
                    print(f"  [OK] CoinMarketCal analyzed: {len(results)} records")
    else:
        print("  [WARN] No cleaned data to analyze")

    # Generate summary
    if all_results:
        sentiments = {}
        emotions = {}
        directions = {'incremental': 0, 'decremental': 0, 'neutral': 0, 'null': 0}
        predictive_count = 0

        for r in all_results:
            sent = r.get('sentiment', 'unknown')
            emo = r.get('primary_emotion', 'UNKNOWN')
            direction = r.get('predictive_direction', 'null')
            is_pred = r.get('is_predictive', False)

            sentiments[sent] = sentiments.get(sent, 0) + 1
            emotions[emo] = emotions.get(emo, 0) + 1
            if direction in directions:
                directions[direction] += 1
            if is_pred:
                predictive_count += 1

        print("\n" + "=" * 70)
        print("ANALYSIS RESULTS SUMMARY")
        print("=" * 70)
        print(f"\nTotal Analyzed: {len(all_results)}")

        print(f"\nSentiment Distribution:")
        for s, c in sorted(sentiments.items()):
            pct = 100 * c / len(all_results)
            bar = "█" * int(pct / 5)
            print(f"  {s:10}: {c:3} ({pct:5.1f}%) {bar}")

        print(f"\nEmotion Distribution:")
        for e, c in sorted(emotions.items()):
            print(f"  {e}: {c}")

        print(f"\nPredictive Analysis:")
        print(f"  Predictive statements: {predictive_count}/{len(all_results)} ({100*predictive_count/len(all_results):.1f}%)")
        print(f"  Direction breakdown:")
        for d, c in directions.items():
            print(f"    {d}: {c}")

        # Sample results
        print(f"\nSample Results (first 3):")
        for i, r in enumerate(all_results[:3]):
            print(f"  [{i+1}] {r.get('summary', 'N/A')[:50]}...")
            print(f"      sentiment={r.get('sentiment')}, direction={r.get('predictive_direction')}, emotion={r.get('primary_emotion')}")
    else:
        print("  [WARN] No analysis results")

except Exception as e:
    print(f"  [ERROR] LLM Analysis: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("PIPELINE COMPLETED")
print("=" * 70)
