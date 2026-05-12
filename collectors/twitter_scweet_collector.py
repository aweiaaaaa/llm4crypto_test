import time
import random
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from Scweet import Scweet

from configs.config import Config
from utils.helpers import save_to_json, logger, random_delay

# 加密货币领域 Top KOL 列表（按影响力排序）
CRYPTO_KOLS = {
    'elites': [
        {'username': 'cz_binance', 'name': 'CZ', 'category': 'exchange', 'influence': 95},
        {'username': 'saylor', 'name': 'Michael Saylor', 'category': 'enterprise', 'influence': 92},
        {'username': 'VitalikButerin', 'name': 'Vitalik Buterin', 'category': 'founder', 'influence': 98},
        {'username': 'aantonop', 'name': 'Andreas Antonopoulos', 'category': 'educator', 'influence': 88},
        {'username': 'APompliano', 'name': 'Anthony Pompliano', 'category': 'influencer', 'influence': 85},
    ],
    'major_exchanges': [
        {'username': 'binance', 'name': 'Binance', 'category': 'exchange', 'influence': 90},
        {'username': 'Coinbase', 'name': 'Coinbase', 'category': 'exchange', 'influence': 88},
        {'username': 'krakenfx', 'name': 'Kraken', 'category': 'exchange', 'influence': 75},
        {'username': 'Gemini', 'name': 'Gemini', 'category': 'exchange', 'influence': 72},
    ],
    'news_media': [
        {'username': 'CryptoNews', 'name': 'CryptoNews', 'category': 'media', 'influence': 80},
        {'username': 'WuBlockchain', 'name': 'Wu Blockchain', 'category': 'media', 'influence': 78},
        {'username': 'CoinDesk', 'name': 'CoinDesk', 'category': 'media', 'influence': 82},
        {'username': 'coindaily', 'name': 'CoinDaily', 'category': 'media', 'influence': 65},
    ],
    'analysts': [
        {'username': 'CryptoCapo', 'name': 'CryptoCapo', 'category': 'analyst', 'influence': 70},
        {'username': 'PlanB', 'name': 'PlanB', 'category': 'analyst', 'influence': 85},
        {'username': 'woonomic', 'name': 'Woo', 'category': 'analyst', 'influence': 68},
    ],
    'degen_traders': [
        {'username': 'CryptoCobain', 'name': 'CryptoCobain', 'category': 'trader', 'influence': 72},
        {'username': 'SatoshiLite', 'name': 'SatoshiLite', 'category': 'trader', 'influence': 65},
    ]
}

class TwitterScweetCollector:
    """
    Twitter/X data collector using Scweet library.
    Enhanced with KOL/influencer targeted collection.
    """
    
    def __init__(self):
        self.scweet = None
        self.auth_token = Config.TWITTER_AUTH_TOKEN if hasattr(Config, 'TWITTER_AUTH_TOKEN') else None
        self.proxy = Config.TWITTER_PROXY if hasattr(Config, 'TWITTER_PROXY') else None
        self.last_collection_count = 0
        self._init_scweet()

    def _init_scweet(self):
        try:
            if self.auth_token:
                self.scweet = Scweet(auth_token=self.auth_token, proxy=self.proxy)
                logger.info("Scweet initialized successfully with auth_token")
            else:
                logger.warning("No Twitter auth_token configured, will use anonymous mode")
                self.scweet = Scweet()
        except Exception as e:
            logger.error(f"Failed to initialize Scweet: {e}")

    def _parse_number(self, value: Any) -> int:
        """Safely parse a number from various types"""
        if value is None:
            return 0
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        return int(str(value).replace(',', '')) if value else 0

    def search_tweets(self, keywords: List[str], limit: int = 50) -> List[Dict[str, Any]]:
        """Search tweets by keywords"""
        all_tweets = []
        
        if not self.scweet:
            self._init_scweet()
        
        try:
            for keyword in keywords:
                logger.info(f"Searching tweets for keyword: {keyword}")
                
                try:
                    tweets = self.scweet.search(
                        keyword,
                        limit=limit,
                        save=False
                    )
                    
                    if tweets is not None and not isinstance(tweets, bool):
                        for tweet in tweets:
                            if hasattr(tweet, 'to_dict'):
                                tweet_dict = tweet.to_dict()
                            else:
                                tweet_dict = dict(tweet)
                            
                            all_tweets.append({
                                'tweet_id': tweet_dict.get('id', ''),
                                'tweet_text': tweet_dict.get('text', '') or tweet_dict.get('content', ''),
                                'author_name': tweet_dict.get('username', '') or tweet_dict.get('user_name', ''),
                                'author_handle': tweet_dict.get('user', '') or tweet_dict.get('screen_name', ''),
                                'timestamp': tweet_dict.get('date', ''),
                                'retweets': self._parse_number(tweet_dict.get('retweets', 0)),
                                'likes': self._parse_number(tweet_dict.get('likes', 0)),
                                'replies': self._parse_number(tweet_dict.get('replies', 0)),
                                'hashtags': tweet_dict.get('hashtags', []),
                                'mentions': tweet_dict.get('mentions', []),
                                'data_source': 'twitter',
                                'search_keyword': keyword,
                                'scraped_at': datetime.now(timezone.utc).isoformat()
                            })
                    
                    logger.info(f"Found {len(tweets)} tweets for {keyword}")
                except Exception as e:
                    logger.error(f"Error searching tweets for {keyword}: {e}")
                
                random_delay(2, 4)
            
            self.last_collection_count = len(all_tweets)
            logger.info(f"Total tweets collected: {len(all_tweets)}")
            
        except Exception as e:
            logger.error(f"Error during Twitter search: {e}")
        
        return all_tweets

    def get_profile_tweets(self, usernames: List[str], limit: int = 30) -> List[Dict[str, Any]]:
        """Get tweets from specific user profiles"""
        all_tweets = []
        
        if not self.scweet:
            self._init_scweet()
        
        try:
            for username in usernames:
                logger.info(f"Fetching tweets from @{username}")
                
                try:
                    tweets = self.scweet.get_profile_tweets(
                        users=[username],
                        limit=limit,
                        save=False
                    )
                    
                    if tweets is not None and not isinstance(tweets, bool):
                        for tweet in tweets:
                            if hasattr(tweet, 'to_dict'):
                                tweet_dict = tweet.to_dict()
                            else:
                                tweet_dict = dict(tweet)
                            
                            all_tweets.append({
                                'tweet_id': tweet_dict.get('id', ''),
                                'tweet_text': tweet_dict.get('text', '') or tweet_dict.get('content', ''),
                                'author_name': tweet_dict.get('username', '') or tweet_dict.get('user_name', ''),
                                'author_handle': '@' + username,
                                'timestamp': tweet_dict.get('date', ''),
                                'retweets': self._parse_number(tweet_dict.get('retweets', 0)),
                                'likes': self._parse_number(tweet_dict.get('likes', 0)),
                                'replies': self._parse_number(tweet_dict.get('replies', 0)),
                                'hashtags': tweet_dict.get('hashtags', []),
                                'mentions': tweet_dict.get('mentions', []),
                                'data_source': 'twitter',
                                'source_user': username,
                                'scraped_at': datetime.now(timezone.utc).isoformat()
                            })
                    
                    logger.info(f"Found {len(tweets)} tweets from @{username}")
                except Exception as e:
                    logger.error(f"Error fetching tweets from @{username}: {e}")
                
                random_delay(2, 4)
            
            self.last_collection_count = len(all_tweets)
            logger.info(f"Total profile tweets collected: {len(all_tweets)}")
            
        except Exception as e:
            logger.error(f"Error during profile tweet fetch: {e}")
        
        return all_tweets

    def collect_from_kols(self, categories: Optional[List[str]] = None, min_influence: int = 70, limit_per_kol: int = 15) -> List[Dict[str, Any]]:
        """
        Collect tweets from top crypto KOLs/influencers
        :param categories: List of KOL categories to target (elites, major_exchanges, news_media, analysts, degen_traders)
        :param min_influence: Minimum influence score threshold (0-100)
        :param limit_per_kol: Maximum tweets per KOL
        """
        all_tweets = []
        
        if categories is None:
            categories = list(CRYPTO_KOLS.keys())
        
        logger.info(f"Starting KOL collection targeting categories: {categories} with min_influence={min_influence}")
        
        for category in categories:
            if category not in CRYPTO_KOLS:
                logger.warning(f"Unknown category: {category}")
                continue
            
            kols = CRYPTO_KOLS[category]
            filtered_kols = [kol for kol in kols if kol['influence'] >= min_influence]
            
            logger.info(f"Category {category}: {len(filtered_kols)}/{len(kols)} KOLs meet influence threshold")
            
            for kol in filtered_kols:
                username = kol['username']
                logger.info(f"Collecting from KOL: @{username} ({kol['name']}) - Influence: {kol['influence']}")
                
                try:
                    tweets = self.get_profile_tweets([username], limit=limit_per_kol)
                    
                    # Add KOL metadata to tweets
                    for tweet in tweets:
                        tweet['kol_category'] = category
                        tweet['kol_name'] = kol['name']
                        tweet['kol_influence'] = kol['influence']
                        tweet['is_verified'] = True  # Assume top KOLs are verified
                    
                    all_tweets.extend(tweets)
                except Exception as e:
                    logger.error(f"Failed to collect from @{username}: {e}")
        
        self.last_collection_count = len(all_tweets)
        logger.info(f"KOL collection complete: {len(all_tweets)} tweets collected from {len([k for cat in categories for k in CRYPTO_KOLS[cat] if k['influence'] >= min_influence])} KOLs")
        
        return all_tweets

    def collect_trending(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Collect trending crypto-related tweets"""
        logger.info("Collecting trending crypto tweets")
        
        trending_keywords = [
            '#Bitcoin', '#BTC', '#Crypto', '#Cryptocurrency', 
            '#DeFi', '#NFT', '#Web3', '$BTC', '$ETH', '$SOL'
        ]
        
        return self.search_tweets(trending_keywords, limit=limit)

    def save_tweets(self, tweets: List[Dict[str, Any]], filename: str = None):
        """Save tweets to JSON file"""
        if not filename:
            filename = f"twitter_tweets_{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
        
        filepath = f"{Config.RAW_DATA_DIR}/{filename}"
        save_to_json(tweets, filepath)
        logger.info(f"Tweets saved to {filepath}")

    def collect_and_save(self, keywords: Optional[List[str]] = None, users: Optional[List[str]] = None, 
                        collect_kols: bool = True, collect_trending: bool = True):
        """
        Collect tweets from multiple sources and save to file
        :param keywords: List of keywords to search
        :param users: List of specific users to follow
        :param collect_kols: Whether to collect from top KOLs
        :param collect_trending: Whether to collect trending tweets
        """
        all_tweets = []
        
        # Keyword search
        if keywords is None:
            keywords = Config.TWITTER_KEYWORDS if hasattr(Config, 'TWITTER_KEYWORDS') else ['$BTC', '$ETH']
        
        keyword_tweets = self.search_tweets(keywords, limit=20)
        all_tweets.extend(keyword_tweets)
        
        # Specific user profiles
        if users is None:
            users = Config.TWITTER_TARGET_ACCOUNTS if hasattr(Config, 'TWITTER_TARGET_ACCOUNTS') else []
        
        if users:
            profile_tweets = self.get_profile_tweets(users, limit=15)
            all_tweets.extend(profile_tweets)
        
        # KOL collection
        if collect_kols:
            kol_tweets = self.collect_from_kols(categories=['elites', 'news_media'], min_influence=75, limit_per_kol=10)
            all_tweets.extend(kol_tweets)
        
        # Trending collection
        if collect_trending:
            trending_tweets = self.collect_trending(limit=30)
            all_tweets.extend(trending_tweets)
        
        if all_tweets:
            self.save_tweets(all_tweets)
        else:
            logger.warning("No Twitter tweets were collected")

    def get_last_collection_count(self) -> int:
        return self.last_collection_count

    def get_available_kol_categories(self) -> List[str]:
        """Get list of available KOL categories"""
        return list(CRYPTO_KOLS.keys())

    def get_kols_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get KOLs in a specific category"""
        return CRYPTO_KOLS.get(category, [])

if __name__ == "__main__":
    collector = TwitterScweetCollector()
    
    print("=" * 70)
    print("Twitter KOL Collector - Demo")
    print("=" * 70)
    
    # Test KOL collection
    print("\n1. Available KOL Categories:")
    categories = collector.get_available_kol_categories()
    for cat in categories:
        kols = collector.get_kols_by_category(cat)
        print(f"   - {cat}: {len(kols)} KOLs")
    
    # Test collecting from elites
    print("\n2. Collecting from top elites...")
    kol_tweets = collector.collect_from_kols(categories=['elites'], min_influence=90, limit_per_kol=5)
    print(f"   Collected {len(kol_tweets)} tweets from elite KOLs")
    
    if kol_tweets:
        print("\n3. Sample KOL Tweets:")
        for tweet in kol_tweets[:3]:
            print(f"   Author: @{tweet.get('author_handle', '')} ({tweet.get('kol_name', '')})")
            print(f"   Text: {tweet.get('tweet_text', '')[:60]}...")
            print(f"   Influence: {tweet.get('kol_influence', 'N/A')}")
            print("   ---")
