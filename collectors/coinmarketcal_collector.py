import requests
import json
import time
import random
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from configs.config import Config
from utils.helpers import save_to_json, random_delay, logger

class CoinMarketCalCollector:
    def __init__(self):
        self.api_key = Config.COINMARKETCAL_API_KEY
        self.base_url = Config.COINMARKETCAL_BASE_URL
        self.headers = {
            'x-api-key': self.api_key,
            'Accept': 'application/json'
        }
        self.request_delay = Config.REQUEST_DELAY
        self.max_retries = Config.MAX_RETRIES

    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/{endpoint}"
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=30, verify=False)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    random_delay(self.request_delay, self.request_delay * 2)
        return None

    def get_events(self, start_date: Optional[str] = None, end_date: Optional[str] = None, 
                   coins: List[str] = None, categories: List[str] = None, page: int = 1, 
                   max_pages: int = 5, sort_by: str = 'date') -> List[Dict[str, Any]]:
        if start_date is None:
            start_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        if end_date is None:
            end_date = (datetime.now(timezone.utc) + timedelta(days=30)).strftime('%Y-%m-%d')

        params = {
            'dateRangeStart': start_date,
            'dateRangeEnd': end_date,
            'sortBy': sort_by,
            'page': page
        }
        
        if coins:
            params['coins'] = ','.join(coins)
        if categories:
            params['categories'] = ','.join(categories)

        all_events = []
        current_page = page
        
        while current_page <= max_pages:
            params['page'] = current_page
            logger.info(f"Fetching CoinMarketCal events (page {current_page}) from {start_date} to {end_date}")
            data = self._make_request('events', params)
            
            if not data or 'data' not in data:
                logger.warning("No events found or API response error")
                break

            events = []
            for event in data['data']:
                event_info = {
                    'event_id': event.get('id', ''),
                    'event_name': event.get('title', ''),
                    'coins': [coin.get('name', '') for coin in event.get('coins', [])],
                    'coin_symbols': [coin.get('symbol', '') for coin in event.get('coins', [])],
                    'coin_slugs': [coin.get('slug', '') for coin in event.get('coins', [])],
                    'categories': [cat.get('name', '') for cat in event.get('categories', [])],
                    'category_slugs': [cat.get('slug', '') for cat in event.get('categories', [])],
                    'date': event.get('date', ''),
                    'date_to': event.get('date_to', ''),
                    'description': event.get('description', ''),
                    'importance': event.get('importance', ''),
                    'source': event.get('source', ''),
                    'source_url': event.get('source_url', ''),
                    'created_at': event.get('created_at', ''),
                    'updated_at': event.get('updated_at', ''),
                    'is_hot': event.get('is_hot', False),
                    'data_source': 'coinmarketcal',
                    'scraped_at': datetime.now(timezone.utc).isoformat()
                }
                events.append(event_info)
            
            if not events:
                break
                
            all_events.extend(events)
            current_page += 1
            random_delay(self.request_delay, self.request_delay * 2)

        logger.info(f"Successfully fetched {len(all_events)} events")
        return all_events

    def get_categories(self) -> List[Dict[str, Any]]:
        logger.info("Fetching CoinMarketCal categories")
        data = self._make_request('categories')
        if not data or 'data' not in data:
            return []
        
        categories = []
        for cat in data['data']:
            categories.append({
                'id': cat.get('id'),
                'name': cat.get('name'),
                'slug': cat.get('slug'),
                'icon': cat.get('icon')
            })
        return categories

    def get_coins(self, page: int = 1, max_pages: int = 10) -> List[Dict[str, Any]]:
        logger.info("Fetching CoinMarketCal coins list")
        all_coins = []
        current_page = page
        
        while current_page <= max_pages:
            data = self._make_request('coins', {'page': current_page})
            if not data or 'data' not in data:
                break
                
            for coin in data['data']:
                all_coins.append({
                    'id': coin.get('id'),
                    'name': coin.get('name'),
                    'symbol': coin.get('symbol'),
                    'slug': coin.get('slug'),
                    'rank': coin.get('rank'),
                    'is_active': coin.get('is_active')
                })
            
            if len(data['data']) < 100:
                break
            current_page += 1
            random_delay(self.request_delay)
        
        return all_coins

    def get_coin_events(self, coin_slug: str, start_date: Optional[str] = None, 
                        end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        if start_date is None:
            start_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        if end_date is None:
            end_date = (datetime.now(timezone.utc) + timedelta(days=30)).strftime('%Y-%m-%d')

        params = {
            'dateRangeStart': start_date,
            'dateRangeEnd': end_date,
            'coins': coin_slug
        }

        logger.info(f"Fetching events for coin: {coin_slug}")
        data = self._make_request('events', params)
        
        if not data or 'data' not in data:
            return []

        events = []
        for event in data['data']:
            event_info = {
                'event_id': event.get('id', ''),
                'event_name': event.get('title', ''),
                'coins': [coin.get('name', '') for coin in event.get('coins', [])],
                'coin_symbols': [coin.get('symbol', '') for coin in event.get('coins', [])],
                'date': event.get('date', ''),
                'description': event.get('description', ''),
                'importance': event.get('importance', ''),
                'data_source': 'coinmarketcal',
                'scraped_at': datetime.now(timezone.utc).isoformat()
            }
            events.append(event_info)
        
        return events

    def collect_and_save(self, output_file: Optional[str] = None, coins: List[str] = None) -> None:
        events = self.get_events(coins=coins)
        if not output_file:
            output_file = f"{Config.RAW_DATA_DIR}/coinmarketcal_events_{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
        
        save_to_json(events, output_file)
        logger.info(f"Events saved to {output_file}")

if __name__ == "__main__":
    collector = CoinMarketCalCollector()
    collector.collect_and_save()