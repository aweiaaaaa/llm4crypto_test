import os
import time
import random
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import praw

from configs.config import Config
from utils.helpers import save_to_json, logger, random_delay

class RedditPRAWCollector:
    """
    Reddit data collector using PRAW (Python Reddit API Wrapper).
    Requires Reddit API credentials for full functionality.
    """
    
    def __init__(self):
        self.reddit = None
        self.client_id = os.getenv('REDDIT_CLIENT_ID', '')
        self.client_secret = os.getenv('REDDIT_CLIENT_SECRET', '')
        self.user_agent = os.getenv('REDDIT_USER_AGENT', 'llm4crypto/1.0 by LLM4Crypto')
        self.subreddits = Config.REDDIT_SUBREDDITS if hasattr(Config, 'REDDIT_SUBREDDITS') else ['CryptoCurrency', 'Bitcoin', 'ethereum']
        self.last_collection_count = 0
        self._init_praw()

    def _init_praw(self):
        try:
            if self.client_id and self.client_secret:
                self.reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent
                )
                logger.info("PRAW initialized successfully with API credentials")
            else:
                logger.warning("No Reddit API credentials configured, using read-only mode")
                self.reddit = praw.Reddit(
                    user_agent=self.user_agent
                )
        except Exception as e:
            logger.error(f"Failed to initialize PRAW: {e}")

    def _extract_mentioned_coins(self, text: str) -> List[str]:
        common_coins = ['BTC', 'ETH', 'SOL', 'BNB', 'ADA', 'XRP', 'DOGE', 'AVAX', 'MATIC', 'DOT', 'LTC', 'LINK', 'UNI']
        coins = []
        text_upper = text.upper()
        for coin in common_coins:
            if coin in text_upper or f'${coin}' in text_upper or f' #{coin}' in text_upper:
                coins.append(coin)
        return list(set(coins))

    def fetch_subreddit_posts(self, subreddit_name: str, max_posts: int = 20, sort_by: str = 'hot') -> List[Dict[str, Any]]:
        """Fetch posts from a specific subreddit"""
        posts = []
        
        if not self.reddit:
            self._init_praw()
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Get posts based on sort type
            if sort_by == 'hot':
                submissions = subreddit.hot(limit=max_posts)
            elif sort_by == 'new':
                submissions = subreddit.new(limit=max_posts)
            elif sort_by == 'top':
                submissions = subreddit.top(limit=max_posts)
            elif sort_by == 'rising':
                submissions = subreddit.rising(limit=max_posts)
            else:
                submissions = subreddit.hot(limit=max_posts)
            
            for submission in submissions:
                full_text = submission.title + ' ' + (submission.selftext or '')
                mentioned_coins = self._extract_mentioned_coins(full_text)
                
                posts.append({
                    'post_id': submission.id,
                    'title': submission.title,
                    'author': str(submission.author) if submission.author else '[deleted]',
                    'subreddit': subreddit_name,
                    'post_text': submission.selftext[:2000] if submission.selftext else '',
                    'score': submission.score,
                    'comments': submission.num_comments,
                    'upvote_ratio': submission.upvote_ratio,
                    'url': submission.url,
                    'is_self': submission.is_self,
                    'created_utc': datetime.fromtimestamp(submission.created_utc, timezone.utc).isoformat(),
                    'mentioned_coins': mentioned_coins,
                    'data_source': 'reddit',
                    'scraped_at': datetime.now(timezone.utc).isoformat()
                })
            
            logger.info(f"Fetched {len(posts)} posts from r/{subreddit_name}")
            
        except Exception as e:
            logger.error(f"Error fetching posts from r/{subreddit_name}: {e}")
            import traceback
            traceback.print_exc()
        
        return posts

    def collect_all(self, max_posts_per_subreddit: int = 10, sort_by: str = 'hot') -> List[Dict[str, Any]]:
        """Collect posts from all configured subreddits"""
        all_posts = []
        
        try:
            for subreddit in self.subreddits:
                posts = self.fetch_subreddit_posts(subreddit, max_posts_per_subreddit, sort_by)
                all_posts.extend(posts)
                random_delay(1, 3)
            
            self.last_collection_count = len(all_posts)
            logger.info(f"Total Reddit posts collected: {len(all_posts)}")
            
        except Exception as e:
            logger.error(f"Error during Reddit collection: {e}")
        
        return all_posts

    def collect_and_save(self, max_posts_per_subreddit: int = 10):
        """Collect posts and save to file"""
        posts = self.collect_all(max_posts_per_subreddit)
        
        if posts:
            filename = f"reddit_posts_{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
            filepath = f"{Config.RAW_DATA_DIR}/{filename}"
            save_to_json(posts, filepath)
            logger.info(f"Reddit posts saved to {filepath}")
        else:
            logger.warning("No Reddit posts were collected")

    def get_last_collection_count(self) -> int:
        return self.last_collection_count

if __name__ == "__main__":
    collector = RedditPRAWCollector()
    
    try:
        posts = collector.fetch_subreddit_posts('CryptoCurrency', max_posts=5)
        print(f"Found {len(posts)} posts")
        for post in posts:
            print(f"Title: {post.get('title', '')[:60]}...")
            print(f"Author: {post.get('author', '')}")
            print(f"Score: {post.get('score', 0)}")
            print(f"Comments: {post.get('comments', 0)}")
            print(f"Coins: {post.get('mentioned_coins', [])}")
            print("---")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()