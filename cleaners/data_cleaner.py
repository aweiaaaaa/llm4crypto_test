import re
import json
import math
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Set, Tuple

import requests
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.utils import check_random_state

from configs.config import Config
from utils.helpers import save_to_json, load_from_json, remove_duplicates, logger

class DataCleaner:
    def __init__(self):
        self.token_keywords = set()
        self.token_aliases = {}
        self._load_token_list()
        self.scaler = StandardScaler()
        self.pca = None
        self.price_kmeans = None

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
        ad_keywords_strong = ['giveaway', 'airdrop', 'promo', 'discount', 'guaranteed profit', 'guaranteed']
        ad_keywords_medium = ['free', 'claim now', 'click here', 'join now', 'limited offer', 'earn money', 'invest now']
        
        text_lower = text.lower()
        
        for keyword in ad_keywords_strong:
            if keyword in text_lower:
                return True
        
        medium_count = sum(1 for keyword in ad_keywords_medium if keyword in text_lower)
        if medium_count >= 2:
            return True
        
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

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """解析时间戳为 datetime 对象"""
        try:
            if isinstance(timestamp_str, datetime):
                return timestamp_str.replace(tzinfo=timezone.utc)
            
            if 'Z' in timestamp_str:
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            elif '+' in timestamp_str:
                return datetime.fromisoformat(timestamp_str)
            else:
                try:
                    dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    return dt.replace(tzinfo=timezone.utc)
                except:
                    try:
                        dt = datetime.strptime(timestamp_str, '%Y-%m-%d')
                        return dt.replace(tzinfo=timezone.utc)
                    except:
                        return datetime.now(timezone.utc)
        except:
            return datetime.now(timezone.utc)

    def _time_decay_weight(self, timestamp: datetime, reference_time: datetime = None, half_life_hours: float = 24.0) -> float:
        """
        计算时间衰减权重（参考 Nature Scientific Reports 2026）
        使用指数衰减：weight = exp(-λ * Δt)
        其中 λ = ln(2) / half_life，确保半衰期后权重为 0.5
        """
        if reference_time is None:
            reference_time = datetime.now(timezone.utc)
        
        delta_hours = (reference_time - timestamp).total_seconds() / 3600
        
        if delta_hours < 0:
            return 1.0
        
        lambda_decay = math.log(2) / half_life_hours
        weight = math.exp(-lambda_decay * delta_hours)
        
        return max(0.01, weight)

    def _calculate_user_influence_score(self, followers: int = 0, engagement_rate: float = 0.0, retweets: int = 0, likes: int = 0) -> float:
        """
        计算用户影响力分数（参考 Nature Scientific Reports 2026）
        影响力 = 粉丝数 × 互动率 × 内容质量因子
        """
        base_score = max(1, followers) * (1 + engagement_rate)
        interaction_factor = math.log1p(retweets + likes)
        
        return base_score * interaction_factor

    def _gaussian_noise_augmentation(self, features: np.ndarray, noise_std: float = 0.01, random_state: int = 42) -> np.ndarray:
        """
        添加高斯噪声增强鲁棒性（参考 Nature Scientific Reports 2026）
        """
        rng = check_random_state(random_state)
        noise = rng.normal(0, noise_std, features.shape)
        return features + noise

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

    def advanced_feature_engineering(self, 
                                     cleaned_data: List[Dict[str, Any]],
                                     sentiment_probabilities: Optional[List[Dict[str, float]]] = None,
                                     price_returns: Optional[List[float]] = None,
                                     time_window_hours: int = 1,
                                     half_life_hours: float = 24.0,
                                     n_pca_components: int = 5,
                                     n_clusters: int = 3) -> Tuple[List[Dict[str, Any]], np.ndarray, List[int]]:
        """
        高级特征工程（参考 Nature Scientific Reports 2026）
        
        核心方法：
        1. 时间衰减加权情绪分数（时衰减）
        2. 用户影响力加权（粉丝数 × 互动量）
        3. PCA 降维聚合多特征
        4. K-means 聚类定义价格剧烈波动标签
        
        Args:
            cleaned_data: 清洗后的数据列表
            sentiment_probabilities: 可选，RoBERTa 情绪概率列表 [{'positive': 0.8, 'negative': 0.2, 'neutral': 0.0}]
            price_returns: 可选，后续回报率列表用于聚类
            time_window_hours: 时间窗口大小（小时）
            half_life_hours: 时间衰减半衰期（小时）
            n_pca_components: PCA 组件数量
            n_clusters: K-means 聚类数量
            
        Returns:
            增强特征后的数据、PCA特征、价格标签
        """
        if not cleaned_data:
            return [], np.array([]), []
        
        logger.info(f"Starting advanced feature engineering on {len(cleaned_data)} records")
        
        # 1. 准备特征矩阵
        features = []
        enhanced_data = []
        
        for i, item in enumerate(cleaned_data):
            timestamp = self._parse_timestamp(item.get('timestamp', ''))
            reference_time = timestamp  # 使用每条消息的时间作为参考
            
            # 基础特征
            retweets = item.get('retweets', 0)
            likes = item.get('likes', 0)
            replies = item.get('replies', 0)
            views = item.get('views', 0)
            score = item.get('score', 0)
            comments = item.get('comments', 0)
            
            # 计算互动指标
            total_interaction = retweets + likes + replies + comments + views
            engagement_rate = total_interaction / max(1, item.get('followers', 1)) if item.get('followers') else 0.0
            
            # 用户影响力分数
            influence_score = self._calculate_user_influence_score(
                followers=item.get('followers', 0),
                engagement_rate=engagement_rate,
                retweets=retweets,
                likes=likes
            )
            
            # 时间衰减权重
            time_weight = self._time_decay_weight(timestamp, reference_time, half_life_hours)
            
            # 情绪概率（如果提供）
            pos_prob = 0.5
            neg_prob = 0.5
            neu_prob = 0.0
            if sentiment_probabilities and i < len(sentiment_probabilities):
                pos_prob = sentiment_probabilities[i].get('positive', 0.5)
                neg_prob = sentiment_probabilities[i].get('negative', 0.5)
                neu_prob = sentiment_probabilities[i].get('neutral', 0.0)
            
            # 计算加权情绪分数
            weighted_sentiment = (pos_prob - neg_prob) * time_weight * (1 + influence_score / 1000)
            
            # 构建特征向量
            feature_vec = [
                pos_prob,
                neg_prob,
                neu_prob,
                influence_score,
                time_weight,
                weighted_sentiment,
                retweets,
                likes,
                replies,
                views,
                score,
                comments,
                len(item.get('tokens', []))
            ]
            
            features.append(feature_vec)
            
            # 增强数据记录
            enhanced_data.append({
                **item,
                'influence_score': influence_score,
                'time_weight': time_weight,
                'sentiment_probabilities': {
                    'positive': pos_prob,
                    'negative': neg_prob,
                    'neutral': neu_prob
                },
                'weighted_sentiment': weighted_sentiment,
                'total_interaction': total_interaction,
                'engagement_rate': engagement_rate
            })
        
        # 2. 标准化特征
        features_array = np.array(features)
        features_scaled = self.scaler.fit_transform(features_array)
        
        # 3. 添加高斯噪声增强鲁棒性
        features_noisy = self._gaussian_noise_augmentation(features_scaled, noise_std=0.01)
        
        # 4. PCA 降维
        n_components = min(n_pca_components, features_noisy.shape[1])
        self.pca = PCA(n_components=n_components, random_state=42)
        pca_features = self.pca.fit_transform(features_noisy)
        
        logger.info(f"PCA explained variance ratio: {self.pca.explained_variance_ratio_}")
        
        # 5. K-means 聚类价格标签（如果提供了价格数据）
        price_labels = []
        if price_returns and len(price_returns) == len(cleaned_data):
            returns_array = np.array(price_returns).reshape(-1, 1)
            
            # 添加高斯噪声到回报率数据
            returns_noisy = self._gaussian_noise_augmentation(returns_array, noise_std=0.001)
            
            # K-means 聚类
            self.price_kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            price_labels = self.price_kmeans.fit_predict(returns_noisy)
            
            # 获取聚类中心并排序
            cluster_centers = self.price_kmeans.cluster_centers_.flatten()
            sorted_indices = np.argsort(cluster_centers)
            
            # 重新映射标签：0=下跌, 1=中性, 2=上涨（或更多类别）
            label_mapping = {sorted_indices[i]: i for i in range(n_clusters)}
            price_labels = [label_mapping[label] for label in price_labels]
            
            # 将价格标签添加到增强数据
            for i, label in enumerate(price_labels):
                if i < len(enhanced_data):
                    enhanced_data[i]['price_movement_label'] = label
            
            logger.info(f"K-means price clusters: {np.bincount(price_labels)}")
        else:
            price_labels = [-1] * len(cleaned_data)
        
        # 将 PCA 特征添加到增强数据
        for i, pca_vec in enumerate(pca_features):
            if i < len(enhanced_data):
                enhanced_data[i]['pca_features'] = pca_vec.tolist()
        
        logger.info(f"Advanced feature engineering completed")
        
        return enhanced_data, pca_features, price_labels

    def calculate_time_weighted_sentiment(self, 
                                          data: List[Dict[str, Any]],
                                          time_window: str = 'hour',
                                          half_life_hours: float = 24.0) -> Dict[str, float]:
        """
        计算时间加权情绪分数（按时间窗口聚合）
        
        Args:
            data: 包含 sentiment_probabilities 和 timestamp 的数据
            time_window: 'hour' 或 'day'
            half_life_hours: 时间衰减半衰期
            
        Returns:
            按时间窗口聚合的情绪分数
        """
        time_bins = {}
        
        for item in data:
            timestamp = self._parse_timestamp(item.get('timestamp', ''))
            sentiment_prob = item.get('sentiment_probabilities', {})
            pos_prob = sentiment_prob.get('positive', 0.5)
            neg_prob = sentiment_prob.get('negative', 0.5)
            
            # 确定时间窗口键
            if time_window == 'hour':
                window_key = timestamp.strftime('%Y-%m-%d %H:00:00')
            else:  # day
                window_key = timestamp.strftime('%Y-%m-%d')
            
            # 计算时间衰减权重（以当前时间为参考）
            weight = self._time_decay_weight(timestamp, datetime.now(timezone.utc), half_life_hours)
            
            # 加权情绪值
            sentiment_value = (pos_prob - neg_prob) * weight
            influence = item.get('influence_score', 1.0)
            
            if window_key not in time_bins:
                time_bins[window_key] = {'sum': 0.0, 'weight_sum': 0.0}
            
            time_bins[window_key]['sum'] += sentiment_value * influence
            time_bins[window_key]['weight_sum'] += influence
        
        # 归一化
        result = {}
        for window, values in time_bins.items():
            if values['weight_sum'] > 0:
                result[window] = values['sum'] / values['weight_sum']
            else:
                result[window] = 0.0
        
        return result

    def get_feature_importance_report(self) -> Dict[str, Any]:
        """获取特征重要性报告（基于 PCA 方差解释）"""
        if self.pca is None:
            return {'error': 'PCA not fitted yet'}
        
        return {
            'n_components': self.pca.n_components,
            'explained_variance_ratio': self.pca.explained_variance_ratio_.tolist(),
            'cumulative_explained_variance': np.cumsum(self.pca.explained_variance_ratio_).tolist(),
            'components': self.pca.components_.tolist()
        }

if __name__ == "__main__":
    cleaner = DataCleaner()
    cleaner.clean_all()
    
    # 示例：高级特征工程
    twitter_data = load_from_json(f"{Config.RAW_DATA_DIR}/twitter_tweets_*.json")
    if twitter_data:
        cleaned = cleaner.clean_twitter_data(twitter_data)
        enhanced, pca_features, price_labels = cleaner.advanced_feature_engineering(cleaned)
        save_to_json(enhanced, f"{Config.CLEANED_DATA_DIR}/enhanced_twitter_{datetime.now(timezone.utc).strftime('%Y%m%d')}.json")
        logger.info(f"Advanced feature engineering completed: {len(enhanced)} records")