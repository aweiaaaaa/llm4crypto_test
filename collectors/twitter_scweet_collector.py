import time
import random
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from Scweet import Scweet

from configs.config import Config
from utils.helpers import save_to_json, logger, random_delay

class TwitterScweetCollector:
    """
    Twitter/X data collector using Scweet library.
    Uses auth_token authentication instead of official API.
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

    def save_tweets(self, tweets: List[Dict[str, Any]], filename: str = None):
        """Save tweets to JSON file"""
        if not filename:
            filename = f"twitter_tweets_{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
        
        filepath = f"{Config.RAW_DATA_DIR}/{filename}"
        save_to_json(tweets, filepath)
        logger.info(f"Tweets saved to {filepath}")

    def collect_and_save(self, keywords: Optional[List[str]] = None, users: Optional[List[str]] = None):
        """Collect tweets from keywords and/or users and save to file"""
        all_tweets = []
        
        if keywords is None:
            keywords = Config.TWITTER_KEYWORDS if hasattr(Config, 'TWITTER_KEYWORDS') else ['$BTC', '$ETH']
        
        if users is None:
            users = Config.TWITTER_TARGET_ACCOUNTS if hasattr(Config, 'TWITTER_TARGET_ACCOUNTS') else []
        
        keyword_tweets = self.search_tweets(keywords, limit=20)
        all_tweets.extend(keyword_tweets)
        
        if users:
            profile_tweets = self.get_profile_tweets(users, limit=15)
            all_tweets.extend(profile_tweets)
        
        if all_tweets:
            self.save_tweets(all_tweets)
        else:
            logger.warning("No Twitter tweets were collected")

    def get_last_collection_count(self) -> int:
        return self.last_collection_count

if __name__ == "__main__":
    collector = TwitterScweetCollector()
    
    try:
        tweets = collector.search_tweets(['$BTC'], limit=5)
        print(f"Found {len(tweets)} tweets")
        for tweet in tweets[:3]:
            print(f"Text: {tweet.get('tweet_text', '')[:80]}...")
            print(f"Author: {tweet.get('author_handle', '')}")
            print(f"Likes: {tweet.get('likes', 0)}")
            print("---")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()