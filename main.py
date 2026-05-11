import argparse
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any

from configs.config import Config
from collectors.coinmarketcal_collector import CoinMarketCalCollector
from collectors.coingecko_collector import CoinGeckoCollector
from collectors.twitter_collector import TwitterCollector
from collectors.twitter_scweet_collector import TwitterScweetCollector
from collectors.reddit_collector import RedditCollector
from collectors.reddit_praw_collector import RedditPRAWCollector
from collectors.telegram_collector import TelegramCollector, run_telegram_collector
from cleaners.data_cleaner import DataCleaner
from analyzers.llm_analyzer import LLMAnalyzer
from utils.helpers import load_from_json, logger

def collect_data(sources: list):
    """
    Collect data from specified sources
    Based on crypto_news_pipeline pattern
    """
    Config.init_dirs()
    collected_counts: Dict[str, int] = {}
    
    if 'coingecko' in sources:
        try:
            logger.info("Starting CoinGecko collection...")
            cg_collector = CoinGeckoCollector()
            cg_collector.collect_and_save()
            collected_counts['coingecko'] = cg_collector.get_last_collection_count()
        except Exception as e:
            logger.error(f"CoinGecko collection failed: {e}")
            collected_counts['coingecko'] = 0
    
    if 'coinmarketcal' in sources:
        try:
            logger.info("Starting CoinMarketCal collection...")
            cmc_collector = CoinMarketCalCollector()
            cmc_collector.collect_and_save()
            collected_counts['coinmarketcal'] = cmc_collector.get_last_collection_count()
        except Exception as e:
            logger.error(f"CoinMarketCal collection failed: {e}")
            collected_counts['coinmarketcal'] = 0
    
    if 'twitter' in sources:
        try:
            logger.info("Starting Twitter collection...")
            #优先使用Scweet（需要auth_token），否则回退到Selenium
            if Config.TWITTER_AUTH_TOKEN:
                logger.info("Using Scweet collector")
                twitter_collector = TwitterScweetCollector()
                twitter_collector.collect_and_save()
                collected_counts['twitter'] = twitter_collector.get_last_collection_count()
            else:
                logger.info("Using Selenium collector (no auth_token configured)")
                twitter_collector = TwitterCollector(headless=True)
                twitter_collector.collect_and_save()
                collected_counts['twitter'] = twitter_collector.get_last_collection_count()
                twitter_collector.close()
        except Exception as e:
            logger.error(f"Twitter collection failed: {e}")
            collected_counts['twitter'] = 0
    
    if 'telegram' in sources:
        try:
            logger.info("Starting Telegram collection...")
            run_telegram_collector()
        except Exception as e:
            logger.error(f"Telegram collection failed: {e}")
    
    if 'reddit' in sources:
        try:
            logger.info("Starting Reddit collection...")
            #优先使用PRAW（需要API凭证），否则回退到Selenium
            if Config.REDDIT_CLIENT_ID and Config.REDDIT_CLIENT_SECRET:
                logger.info("Using PRAW collector")
                reddit_collector = RedditPRAWCollector()
                reddit_collector.collect_and_save()
                collected_counts['reddit'] = reddit_collector.get_last_collection_count()
            else:
                logger.info("Using Selenium collector (no Reddit API credentials)")
                reddit_collector = RedditCollector(headless=True)
                reddit_collector.collect_and_save()
                collected_counts['reddit'] = reddit_collector.get_last_collection_count()
                reddit_collector.close()
        except Exception as e:
            logger.error(f"Reddit collection failed: {e}")
            collected_counts['reddit'] = 0
    
    logger.info(f"Collection complete. Results: {collected_counts}")

def clean_data(sources: list):
    """
    Clean collected data from specified sources
    """
    logger.info("Starting data cleaning...")
    cleaner = DataCleaner()
    results = cleaner.clean_all(sources)
    
    for source, cleaned_data in results.items():
        logger.info(f"Cleaned {len(cleaned_data)} records from {source}")
        
        quality_report = cleaner.get_data_quality_report(cleaned_data)
        logger.info(f"Data quality report for {source}: {quality_report}")

def analyze_data(source_files: list = None):
    """
    Analyze cleaned data using LLM
    Enhanced prompt engineering based on crypto-sentiment-with-llms
    """
    logger.info("Starting LLM analysis...")
    analyzer = LLMAnalyzer()
    
    if source_files is None:
        source_files = ['cleaned_coingecko_', 'cleaned_twitter_', 'cleaned_telegram_', 'cleaned_coinmarketcal_']
    
    all_results = []
    for file_pattern in source_files:
        try:
            cleaned_data = load_from_json(f"{Config.CLEANED_DATA_DIR}/{file_pattern}*.json")
            if cleaned_data:
                results = analyzer.analyze_dataset(cleaned_data)
                all_results.extend(results)
                logger.info(f"Analyzed {len(results)} records from {file_pattern}")
        except Exception as e:
            logger.warning(f"Failed to load {file_pattern}: {e}")
    
    if all_results:
        report = analyzer.generate_report(all_results)
        logger.info(f"Analysis complete. Summary:\n{report.summary}")
        
        analyzer.plot_sentiment_distribution(all_results, f"{Config.ANALYSIS_DIR}/sentiment_distribution.png")
    else:
        logger.warning("No data to analyze")

def run_full_pipeline(sources: list):
    """
    Run complete pipeline: collect -> clean -> analyze
    Inspired by crypto_news_pipeline's workflow design
    """
    start_time = datetime.now(timezone.utc)
    logger.info(f"Starting full pipeline at {start_time}")
    
    try:
        # Collect data
        collect_data(sources)
        
        # Clean data
        clean_data(sources)
        
        # Analyze data
        analyze_data()
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Full pipeline completed in {duration:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='LLM4Crypto - Cryptocurrency Data Analysis System')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    collect_parser = subparsers.add_parser('collect', help='Collect data from sources')
    collect_parser.add_argument('--sources', nargs='+', default=['coingecko', 'twitter'],
                                choices=['coingecko', 'coinmarketcal', 'twitter', 'telegram', 'reddit'],
                                help='Data sources to collect from')
    
    clean_parser = subparsers.add_parser('clean', help='Clean collected data')
    clean_parser.add_argument('--sources', nargs='+', default=['coingecko', 'twitter'],
                              choices=['coingecko', 'coinmarketcal', 'twitter', 'telegram', 'reddit'],
                              help='Data sources to clean')
    
    analyze_parser = subparsers.add_parser('analyze', help='Analyze cleaned data with LLM')
    analyze_parser.add_argument('--files', nargs='+', help='Specific files to analyze')
    analyze_parser.add_argument('--use-real', action='store_true', help='Use real LLM instead of mock')
    
    full_parser = subparsers.add_parser('full', help='Run complete pipeline: collect -> clean -> analyze')
    full_parser.add_argument('--sources', nargs='+', default=['coingecko', 'twitter'],
                             choices=['coingecko', 'coinmarketcal', 'twitter', 'telegram', 'reddit'],
                             help='Data sources to process')
    
    args = parser.parse_args()
    
    Config.init_dirs()
    
    if args.command == 'collect':
        collect_data(args.sources)
    elif args.command == 'clean':
        clean_data(args.sources)
    elif args.command == 'analyze':
        analyze_data(args.files)
    elif args.command == 'full':
        run_full_pipeline(args.sources)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()