import re
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set

import requests

from configs.config import Config
from utils.helpers import save_to_json, load_from_json, remove_duplicates, logger

class DataCleaner:
    def __init__(self):
        self.token_keywords = set()
        self.token_aliases = {}
        self._load_token_list()

    def _load_token_list(self):
        try:
            response = requests.get(f"{Config.COINGECKO_BASE_URL}/coins/list")
            if response.status_code == 200:
                coins = response.json()
                for coin in coins:
                    self.token_keywords.add(coin['symbol'].upper())
                    self.token_keywords.add(coin['name'].lower())
                    self.token_aliases[coin['symbol'].upper()] = coin['name']
                    self.token_aliases[coin['name'].lower()] = coin['symbol'].upper()
                logger.info(f"Loaded {len(self.token_keywords)} token keywords")
        except Exception as e:
            logger.warning(f"Failed to load token list from CoinGecko: {e}")
            self.token_keywords = {'BTC', 'ETH', 'SOL', 'BNB', 'USDT', 'USD'}

    def _is_emoji_only(self, text: str) -> bool:
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"
            u"\U0001F300-\U0001F5FF"
            u"\U0001F680-\U0001F6FF"
            u"\U0001F1E0-\U0001F1FF"
            u"\U00002500-\U00002BEF"
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        cleaned = emoji_pattern.sub(r'', text)
        return len(cleaned.strip()) == 0

    def _is_advertisement(self, text: str) -> bool:
        # 更精确的广告检测规则 - 需要多个广告特征同时出现
        ad_keywords_strong = ['giveaway', 'airdrop', 'promo', 'discount', 'guaranteed profit', 'guaranteed']
        ad_keywords_medium = ['free', 'claim now', 'click here', 'join now', 'limited offer', 'earn money', 'invest now']
        
        text_lower = text.lower()
        
        # 强广告特征：出现任意一个即判定为广告
        for keyword in ad_keywords_strong:
            if keyword in text_lower:
                return True
        
        # 中等广告特征：需要至少 2 个不同特征才判定为广告
        medium_count = sum(1 for keyword in ad_keywords_medium if keyword in text_lower)
        if medium_count >= 2:
            return True
        
        # 特殊情况：包含链接 + 强诱导性词汇
        if ('http' in text_lower or 't.co' in text_lower) and any(word in text_lower for word in ['free', 'win', 'claim']):
            return True
        
        return False

    def _extract_tokens(self, text: str) -> List[str]:
        tokens = []
        text_upper = text.upper()
        
        for keyword in self.token_keywords:
            if keyword in text_upper:
                tokens.append(keyword)
        
        symbol_pattern = re.compile(r'\$[A-Za-z]{2,10}')
        symbols = symbol_pattern.findall(text)
        for symbol in symbols:
            tokens.append(symbol[1:].upper())
        
        return list(set(tokens))

    def _normalize_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'http[s]?://\S+', '', text)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#\w+', '', text)
        return text

    def _convert_to_utc(self, timestamp: str) -> str:
        try:
            if isinstance(timestamp, str):
                if 'Z' in timestamp:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                elif '+' in timestamp:
                    dt = datetime.fromisoformat(timestamp)
                else:
                    try:
                        dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                        dt = dt.replace(tzinfo=timezone.utc)
                    except:
                        return timestamp
                return dt.isoformat()
        except Exception as e:
            logger.warning(f"Failed to parse timestamp {timestamp}: {e}")
        return timestamp

    def clean_twitter_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cleaned = []
        for item in raw_data:
            text = item.get('tweet_text', '')
            
            if not text or len(text.strip()) < 10:
                continue
            
            if self._is_emoji_only(text):
                continue
            
            if self._is_advertisement(text):
                continue
            
            cleaned_text = self._normalize_text(text)
            tokens = self._extract_tokens(text)
            
            cleaned.append({
                'source': 'twitter',
                'author': item.get('author_name', '') or item.get('author_handle', ''),
                'author_handle': item.get('author_handle', ''),
                'text': cleaned_text,
                'timestamp': self._convert_to_utc(item.get('timestamp', '')),
                'tokens': tokens,
                'retweets': int(item.get('retweets', 0)) if isinstance(item.get('retweets'), int) else int(str(item.get('retweets', '0')).replace(',', '')),
                'likes': int(item.get('likes', 0)) if isinstance(item.get('likes'), int) else int(str(item.get('likes', '0')).replace(',', '')),
                'replies': int(item.get('replies', 0)) if isinstance(item.get('replies'), int) else int(str(item.get('replies', '0')).replace(',', '')),
                'original_data': item
            })
        
        return remove_duplicates(cleaned, key='text')

    def clean_telegram_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cleaned = []
        for item in raw_data:
            text = item.get('text', '')
            
            if not text or len(text.strip()) < 10:
                continue
            
            if self._is_emoji_only(text):
                continue
            
            cleaned_text = self._normalize_text(text)
            tokens = self._extract_tokens(text)
            
            cleaned.append({
                'source': 'telegram',
                'author': item.get('sender_name', '') or str(item.get('sender_id', '')),
                'channel': item.get('channel_name', ''),
                'text': cleaned_text,
                'timestamp': self._convert_to_utc(item.get('date', '')),
                'tokens': tokens,
                'views': item.get('views', 0),
                'forwards': item.get('forwards', 0),
                'has_media': bool(item.get('media_info', {})),
                'original_data': item
            })
        
        return remove_duplicates(cleaned, key='text')

    def clean_coingecko_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cleaned = []
        for item in raw_data:
            symbol = item.get('symbol', '')
            if symbol:
                symbol = symbol.upper()
            name = item.get('name', '')
            
            if not symbol:
                continue
            
            price_change = item.get('price_change_percentage_24h')
            if price_change is None:
                price_change = 0
            
            if price_change > 5:
                sentiment_text = f"{name} ({symbol}) price increased by {price_change:.2f}% in the last 24 hours."
            elif price_change < -5:
                sentiment_text = f"{name} ({symbol}) price decreased by {abs(price_change):.2f}% in the last 24 hours."
            else:
                sentiment_text = f"{name} ({symbol}) price is stable with {price_change:.2f}% change in the last 24 hours."
            
            current_price = item.get('current_price') or 0
            market_cap = item.get('market_cap') or 0
            total_volume = item.get('total_volume') or 0
            
            cleaned.append({
                'source': 'coingecko',
                'coin_id': item.get('id', ''),
                'symbol': symbol,
                'name': name,
                'text': sentiment_text,
                'timestamp': item.get('scraped_at', ''),
                'tokens': [symbol],
                'price': current_price,
                'market_cap': market_cap,
                'price_change_24h': price_change,
                'volume': total_volume,
                'original_data': item
            })
        
        return remove_duplicates(cleaned, key='coin_id')

    def clean_coinmarketcal_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cleaned = []
        for item in raw_data:
            description = item.get('description', '') or item.get('event_name', '')
            
            if not description:
                continue
            
            cleaned_text = self._normalize_text(description)
            tokens = item.get('coin_symbols', []) or self._extract_tokens(description)
            
            cleaned.append({
                'source': 'coinmarketcal',
                'event_id': item.get('event_id', ''),
                'event_name': item.get('event_name', ''),
                'text': cleaned_text,
                'timestamp': self._convert_to_utc(item.get('date', '')),
                'tokens': tokens,
                'categories': item.get('categories', []),
                'importance': item.get('importance', ''),
                'source_url': item.get('source_url', ''),
                'original_data': item
            })
        
        return remove_duplicates(cleaned, key='event_id')

    def clean_reddit_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cleaned = []
        for item in raw_data:
            title = item.get('title', '')
            post_text = item.get('post_text', '')
            
            full_text = title + ' ' + post_text
            
            if not full_text or len(full_text.strip()) < 10:
                continue
            
            if self._is_emoji_only(full_text):
                continue
            
            if self._is_advertisement(full_text):
                continue
            
            cleaned_text = self._normalize_text(full_text)
            tokens = item.get('mentioned_coins', []) or self._extract_tokens(full_text)
            
            try:
                score = int(item.get('score', '0').replace(',', ''))
            except:
                score = 0
            
            try:
                comments = int(item.get('comments', '0').replace(',', ''))
            except:
                comments = 0
            
            cleaned.append({
                'source': 'reddit',
                'post_id': item.get('post_id', ''),
                'subreddit': item.get('subreddit', ''),
                'title': title,
                'author': item.get('author', ''),
                'text': cleaned_text,
                'timestamp': item.get('scraped_at', ''),
                'tokens': tokens,
                'score': score,
                'comments': comments,
                'original_data': item
            })
        
        return remove_duplicates(cleaned, key='post_id')

    def clean_all(self, data_sources: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        if data_sources is None:
            data_sources = ['coingecko', 'twitter', 'telegram', 'coinmarketcal', 'reddit']
        
        results = {}
        file_patterns = {
            'coingecko': 'coingecko_market_',
            'twitter': 'twitter_tweets_',
            'telegram': 'telegram_messages_',
            'coinmarketcal': 'coinmarketcal_events_',
            'reddit': 'reddit_posts_'
        }
        
        for source in data_sources:
            file_pattern = file_patterns.get(source)
            if not file_pattern:
                continue
                
            try:
                raw_data = load_from_json(f"{Config.RAW_DATA_DIR}/{file_pattern}*.json")
                if raw_data:
                    if source == 'coingecko':
                        cleaned = self.clean_coingecko_data(raw_data)
                    elif source == 'twitter':
                        cleaned = self.clean_twitter_data(raw_data)
                    elif source == 'telegram':
                        cleaned = self.clean_telegram_data(raw_data)
                    elif source == 'coinmarketcal':
                        cleaned = self.clean_coinmarketcal_data(raw_data)
                    elif source == 'reddit':
                        cleaned = self.clean_reddit_data(raw_data)
                    else:
                        continue
                    
                    results[source] = cleaned
                    output_file = f"{Config.CLEANED_DATA_DIR}/cleaned_{source}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
                    save_to_json(cleaned, output_file)
                    logger.info(f"Cleaned {len(cleaned)} {source} records saved to {output_file}")
            except Exception as e:
                logger.warning(f"Failed to clean {source} data: {e}")
        
        return results

    def get_data_quality_report(self, cleaned_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not cleaned_data:
            return {'total_records': 0}
        
        total = len(cleaned_data)
        has_tokens = sum(1 for item in cleaned_data if item.get('tokens'))
        avg_text_length = sum(len(item.get('text', '')) for item in cleaned_data) / total
        
        sources = {}
        for item in cleaned_data:
            source = item.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        
        return {
            'total_records': total,
            'records_with_tokens': has_tokens,
            'percentage_with_tokens': (has_tokens / total) * 100,
            'avg_text_length': avg_text_length,
            'source_distribution': sources
        }

if __name__ == "__main__":
    cleaner = DataCleaner()
    cleaner.clean_all()