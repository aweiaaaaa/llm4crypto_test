import requests
import json
import time
import random
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from configs.config import Config
from utils.helpers import save_to_json, random_delay, logger

class CoinGeckoCollector:
    def __init__(self):
        self.base_url = Config.COINGECKO_BASE_URL
        self.request_delay = Config.REQUEST_DELAY
        self.max_retries = Config.MAX_RETRIES
        self.last_collection_count = 0

    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/{endpoint}"
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, params=params, timeout=30, verify=False)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    random_delay(self.request_delay, self.request_delay * 2)
        return None

    def get_coins_market_data(self, vs_currency: str = 'usd', ids: List[str] = None, 
                              order: str = 'market_cap_desc', per_page: int = 100, 
                              page: int = 1, sparkline: bool = False) -> List[Dict[str, Any]]:
        params = {
            'vs_currency': vs_currency,
            'order': order,
            'per_page': per_page,
            'page': page,
            'sparkline': sparkline
        }
        
        if ids:
            params['ids'] = ','.join(ids)

        logger.info(f"Fetching market data for {vs_currency}")
        data = self._make_request('coins/markets', params)
        
        if not data:
            return []

        market_data = []
        for coin in data:
            market_data.append({
                'id': coin.get('id', ''),
                'symbol': coin.get('symbol', '').upper(),
                'name': coin.get('name', ''),
                'current_price': coin.get('current_price', 0),
                'market_cap': coin.get('market_cap', 0),
                'market_cap_rank': coin.get('market_cap_rank', 0),
                'total_volume': coin.get('total_volume', 0),
                'high_24h': coin.get('high_24h', 0),
                'low_24h': coin.get('low_24h', 0),
                'price_change_24h': coin.get('price_change_24h', 0),
                'price_change_percentage_24h': coin.get('price_change_percentage_24h', 0),
                'market_cap_change_24h': coin.get('market_cap_change_24h', 0),
                'market_cap_change_percentage_24h': coin.get('market_cap_change_percentage_24h', 0),
                'circulating_supply': coin.get('circulating_supply', 0),
                'total_supply': coin.get('total_supply', 0),
                'max_supply': coin.get('max_supply', 0),
                'ath': coin.get('ath', 0),
                'ath_change_percentage': coin.get('ath_change_percentage', 0),
                'ath_date': coin.get('ath_date', ''),
                'data_source': 'coingecko',
                'scraped_at': datetime.now(timezone.utc).isoformat()
            })
        
        logger.info(f"Successfully fetched {len(market_data)} coins market data")
        return market_data

    def get_coin_info(self, coin_id: str) -> Dict[str, Any]:
        logger.info(f"Fetching info for coin: {coin_id}")
        data = self._make_request(f'coins/{coin_id}')
        
        if not data:
            return {}

        return {
            'id': data.get('id', ''),
            'symbol': data.get('symbol', '').upper(),
            'name': data.get('name', ''),
            'description': data.get('description', {}).get('en', ''),
            'homepage': data.get('links', {}).get('homepage', [''])[0],
            'whitepaper': data.get('links', {}).get('whitepaper', {}).get('en', ''),
            'twitter': data.get('links', {}).get('twitter_screen_name', ''),
            'reddit': data.get('links', {}).get('subreddit_url', ''),
            'market_cap_rank': data.get('market_cap_rank', 0),
            'categories': data.get('categories', []),
            'data_source': 'coingecko',
            'scraped_at': datetime.now(timezone.utc).isoformat()
        }

    def get_coin_ohlc(self, coin_id: str, vs_currency: str = 'usd', days: int = 7) -> List[Dict[str, Any]]:
        logger.info(f"Fetching OHLC data for {coin_id} ({days} days)")
        data = self._make_request(f'coins/{coin_id}/ohlc', {'vs_currency': vs_currency, 'days': days})
        
        if not data:
            return []

        ohlc_data = []
        for entry in data:
            ohlc_data.append({
                'timestamp': entry[0],
                'date': datetime.fromtimestamp(entry[0] / 1000, timezone.utc).isoformat(),
                'open': entry[1],
                'high': entry[2],
                'low': entry[3],
                'close': entry[4],
                'coin_id': coin_id,
                'vs_currency': vs_currency,
                'data_source': 'coingecko',
                'scraped_at': datetime.now(timezone.utc).isoformat()
            })
        
        return ohlc_data

    def get_coin_tickers(self, coin_id: str) -> List[Dict[str, Any]]:
        logger.info(f"Fetching tickers for {coin_id}")
        data = self._make_request(f'coins/{coin_id}/tickers')
        
        if not data or 'tickers' not in data:
            return []

        tickers = []
        for ticker in data['tickers'][:50]:
            tickers.append({
                'exchange': ticker.get('exchange', {}).get('name', ''),
                'base': ticker.get('base', ''),
                'target': ticker.get('target', ''),
                'last': ticker.get('last', 0),
                'volume': ticker.get('volume', 0),
                'coin_id': coin_id,
                'data_source': 'coingecko',
                'scraped_at': datetime.now(timezone.utc).isoformat()
            })
        
        return tickers

    def get_global_data(self) -> Dict[str, Any]:
        logger.info("Fetching global crypto data")
        data = self._make_request('global')
        
        if not data or 'data' not in data:
            return {}

        global_data = data['data']
        return {
            'total_market_cap': global_data.get('total_market_cap', {}).get('usd', 0),
            'total_volume': global_data.get('total_volume', {}).get('usd', 0),
            'bitcoin_dominance': global_data.get('bitcoin_dominance', 0),
            'ethereum_dominance': global_data.get('ethereum_dominance', 0),
            'active_cryptocurrencies': global_data.get('active_cryptocurrencies', 0),
            'active_markets': global_data.get('active_markets', 0),
            'data_source': 'coingecko',
            'scraped_at': datetime.now(timezone.utc).isoformat()
        }

    def get_trending_coins(self, vs_currency: str = 'usd', count: int = 7) -> List[Dict[str, Any]]:
        logger.info("Fetching trending coins")
        data = self._make_request('search/trending')
        
        if not data or 'coins' not in data:
            return []

        trending = []
        for item in data['coins'][:count]:
            coin = item['item']
            trending.append({
                'id': coin.get('id', ''),
                'symbol': coin.get('symbol', '').upper(),
                'name': coin.get('name', ''),
                'market_cap_rank': coin.get('market_cap_rank', 0),
                'score': item.get('score', 0),
                'data_source': 'coingecko',
                'scraped_at': datetime.now(timezone.utc).isoformat()
            })
        
        return trending

    def collect_and_save(self, output_file: Optional[str] = None, coins: List[str] = None) -> None:
        market_data = self.get_coins_market_data(ids=coins)
        self.last_collection_count = len(market_data)
        
        if not output_file:
            output_file = f"{Config.RAW_DATA_DIR}/coingecko_market_{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
        
        save_to_json(market_data, output_file)
        logger.info(f"Market data saved to {output_file}")

    def get_last_collection_count(self) -> int:
        return self.last_collection_count

if __name__ == "__main__":
    collector = CoinGeckoCollector()
    collector.collect_and_save()