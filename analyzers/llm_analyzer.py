import json
import hashlib
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple

import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from cachetools import TTLCache

from configs.config import Config
from models.data_models import NewsItem, ProcessedNewsItem, Sentiment, TimeScale, AnalysisResult, AnalysisSummary
from utils.helpers import save_to_json, logger

class LLMAnalyzer:
    def __init__(self, use_mock=False, cache_ttl=3600):
        self.api_key = Config.OPENAI_API_KEY
        self.base_url = Config.OPENAI_BASE_URL
        self.model = Config.OPENAI_MODEL
        self.cache = TTLCache(maxsize=1000, ttl=cache_ttl)
        self.cache_file = f"{Config.ANALYSIS_DIR}/analysis_cache.json"
        self._load_cache()
        self.use_mock = use_mock
        self.mock_analyzer = None

        if self.use_mock:
            from .mock_llm_analyzer import MockLLMAnalyzer
            self.mock_analyzer = MockLLMAnalyzer()
            logger.info("Using mock LLM analyzer")

    def _load_cache(self):
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                for key, value in cached_data.items():
                    if key not in self.cache:
                        self.cache[key] = value
        except FileNotFoundError:
            pass

    def _save_cache(self):
        cache_data = {k: v for k, v in self.cache.items()}
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)

    def _get_cache_key(self, text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def _extract_json_from_response(self, content: str) -> str:
        content = content.strip()
        if content.startswith('```'):
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'\s*```$', '', content)
        return content

    def _build_prompt(self, text: str) -> str:
        """
        Optimized hybrid prompt combining:
        - Simple direct sentiment approach (from old version)
        - Two-stage predictive classification (arXiv:2603.24933)
        - Chain-of-Thought reasoning (arXiv:2508.15825)
        - SenticNet fine-grained emotions
        """
        prompt = f"""Analyze this cryptocurrency text and provide structured analysis.

TEXT: {text}

## STEP 1: IS THIS POSITIVE OR NEGATIVE?
Simply determine if the overall sentiment is positive or negative for crypto markets.

## STEP 2: IS THIS PREDICTIVE?
- PREDICTIVE = Claims about FUTURE prices (e.g., "BTC will reach $100k", "ETH to drop below $2k")
- NON-PREDICTIVE = Current facts (e.g., "SEC approved ETF", "Binance listed token")

## STEP 3: IF PREDICTIVE, WHAT DIRECTION?
- INCREMENTAL = Price will GO UP (bullish words: reach, surge, rally, pump, jump, gain, climb, hit new high)
- DECREMENTAL = Price will GO DOWN (bearish words: drop, crash, dump, fall, decline, plummet, lose, below)

## STEP 4: EMOTION (SenticNet)
Choose primary emotion:
- JOY: Positive news, success, gains
- FEAR: Concerns, risks, warnings
- ANGER: Failures, rejections, losses
- ANTICIPATION: Expectations, upcoming events

## OUTPUT JSON:
{{
    "sentiment": "bullish/bearish/neutral",
    "is_positive": true/false,
    "is_predictive": true/false,
    "predictive_direction": "incremental/decremental/neutral/null",
    "tokens": ["TOKEN1"],
    "primary_emotion": "JOY/FEAR/ANGER/ANTICIPATION",
    "importance": 1-10,
    "summary": "brief summary"
}}

IMPORTANT: Output only valid JSON."""
        return prompt.strip()

    def analyze_text(self, text: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        if self.use_mock or not (self.api_key and self.base_url):
            if self.mock_analyzer:
                return self.mock_analyzer.analyze_text(text, use_cache)
            elif not (self.api_key and self.base_url):
                logger.warning("No LLM API configured, returning mock analysis")
                from .mock_llm_analyzer import MockLLMAnalyzer
                self.mock_analyzer = MockLLMAnalyzer()
                return self.mock_analyzer.analyze_text(text, use_cache)

        if use_cache:
            cache_key = self._get_cache_key(text)
            if cache_key in self.cache:
                logger.debug("Using cached analysis")
                return self.cache[cache_key]

        prompt = self._build_prompt(text)

        try:
            url = self.base_url
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            data = {
                'model': self.model,
                'messages': [
                    {"role": "system", "content": "You are a professional cryptocurrency market analyst. Use Chain-of-Thought reasoning to analyze market sentiment and impact. Always output valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                'temperature': 0.3,
                'max_tokens': 1024,
                'response_format': {"type": "json_object"}
            }

            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()

            result = response.json()
            content = result['choices'][0]['message']['content']
            content = self._extract_json_from_response(content)
            analysis = json.loads(content)

            if not isinstance(analysis, dict):
                logger.error(f"Invalid analysis format: {type(analysis)}")
                if self.mock_analyzer:
                    return self.mock_analyzer.analyze_text(text, use_cache)
                return None

            if 'reasoning_chain' not in analysis:
                analysis['reasoning_chain'] = ['Analysis completed']

            if use_cache:
                cache_key = self._get_cache_key(text)
                self.cache[cache_key] = analysis
                self._save_cache()

            logger.info(f"Analysis completed for text: {text[:50]}...")
            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            if self.mock_analyzer:
                logger.info("Falling back to mock analyzer")
                return self.mock_analyzer.analyze_text(text, use_cache)
            return None
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            if self.mock_analyzer:
                logger.info("Falling back to mock analyzer")
                return self.mock_analyzer.analyze_text(text, use_cache)
            return None

    def analyze_batch(self, texts: List[str], use_cache: bool = True) -> List[Dict[str, Any]]:
        results = []
        for i, text in enumerate(texts):
            analysis = self.analyze_text(text, use_cache)
            if analysis:
                analysis['original_text'] = text
                analysis['index'] = i
                results.append(analysis)
            if (i + 1) % 10 == 0:
                logger.info(f"Analyzed {i+1}/{len(texts)} texts")
        return results

    def analyze_dataset(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for item in data:
            text = item.get('text', '') or item.get('tweet_text', '') or item.get('title', '')
            if text:
                analysis = self.analyze_text(text)
                if analysis:
                    result = {**item, 'llm_analysis': analysis}
                    results.append(result)
        return results

    def generate_report(self, analysis_results: List[Dict[str, Any]]) -> AnalysisSummary:
        if not analysis_results:
            return AnalysisSummary()

        total = len(analysis_results)
        relevant = sum(1 for r in analysis_results if r.get('llm_analysis', {}).get('relevant', False))

        sentiment_counts = {s: 0 for s in ['bullish', 'bearish', 'neutral', 'fear', 'excited']}
        importance_scores = []
        token_counts = {}

        predictive_count = 0
        incremental_count = 0
        decremental_count = 0
        emotion_counts = {e: 0 for e in ['JOY', 'FEAR', 'ANGER', 'ANTICIPATION', 'SADNESS', 'TRUST', 'SURPRISE']}
        market_impact_counts = {'positive': 0, 'negative': 0, 'neutral': 0}

        for result in analysis_results:
            analysis = result.get('llm_analysis', {})
            sentiment = analysis.get('sentiment', 'neutral')
            if sentiment in sentiment_counts:
                sentiment_counts[sentiment] += 1

            importance = analysis.get('importance', 0)
            if isinstance(importance, int) and 1 <= importance <= 10:
                importance_scores.append(importance)

            tokens = analysis.get('tokens', [])
            for token in tokens:
                token_counts[token] = token_counts.get(token, 0) + 1

            is_predictive = analysis.get('is_predictive', False)
            if is_predictive:
                predictive_count += 1
                direction = analysis.get('predictive_direction', 'neutral')
                if direction == 'incremental':
                    incremental_count += 1
                elif direction == 'decremental':
                    decremental_count += 1

            primary_emotion = analysis.get('primary_emotion', 'TRUST')
            if primary_emotion in emotion_counts:
                emotion_counts[primary_emotion] += 1

            market_impact = analysis.get('market_impact', 'neutral')
            if market_impact in market_impact_counts:
                market_impact_counts[market_impact] += 1

        avg_importance = sum(importance_scores) / len(importance_scores) if importance_scores else 0.0
        top_tokens = sorted(token_counts.keys(), key=lambda x: token_counts[x], reverse=True)[:10]

        summary_text = f"""
        Analysis Summary:
        - Total analyzed: {total}
        - Relevant: {relevant} ({(relevant/total)*100:.1f}%)
        - Predictive statements: {predictive_count} ({predictive_count/total*100:.1f}%)
          - Incremental: {incremental_count} | Decremental: {decremental_count}
        - Bullish/Excited: {sentiment_counts['bullish'] + sentiment_counts['excited']} ({((sentiment_counts['bullish'] + sentiment_counts['excited'])/total)*100:.1f}%)
        - Bearish/Fear: {sentiment_counts['bearish'] + sentiment_counts['fear']} ({((sentiment_counts['bearish'] + sentiment_counts['fear'])/total)*100:.1f}%)
        - Neutral: {sentiment_counts['neutral']} ({(sentiment_counts['neutral']/total)*100:.1f}%)
        - Market Impact: Positive {market_impact_counts['positive']} | Negative {market_impact_counts['negative']} | Neutral {market_impact_counts['neutral']}
        - Primary Emotions: Joy {emotion_counts['JOY']} | Fear {emotion_counts['FEAR']} | Anger {emotion_counts['ANGER']} | Anticipation {emotion_counts['ANTICIPATION']}
        - Average importance: {avg_importance:.2f}/10
        - Top tokens: {', '.join(top_tokens[:5])}
        """

        summary = AnalysisSummary(
            total_analyzed=total,
            relevant_count=relevant,
            bullish_count=sentiment_counts['bullish'],
            bearish_count=sentiment_counts['bearish'],
            neutral_count=sentiment_counts['neutral'],
            fear_count=sentiment_counts['fear'],
            excited_count=sentiment_counts['excited'],
            avg_importance=round(avg_importance, 2),
            top_tokens=top_tokens,
            generated_at=datetime.now(timezone.utc),
            summary=summary_text.strip()
        )

        report_dict = summary.dict()
        report_dict['generated_at'] = summary.generated_at.isoformat()
        report_dict['predictive_analysis'] = {
            'predictive_count': predictive_count,
            'incremental_count': incremental_count,
            'decremental_count': decremental_count,
            'predictive_rate': round(predictive_count / total * 100, 2) if total > 0 else 0
        }
        report_dict['emotion_distribution'] = emotion_counts
        report_dict['market_impact_distribution'] = market_impact_counts

        report_file = f"{Config.ANALYSIS_DIR}/analysis_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        save_to_json(report_dict, report_file)
        logger.info(f"Analysis report saved to {report_file}")

        return summary

    def plot_sentiment_distribution(self, analysis_results: List[Dict[str, Any]], output_path: str) -> None:
        sentiment_counts = {
            'Bullish': 0,
            'Bearish': 0,
            'Neutral': 0,
            'Fear': 0,
            'Excited': 0
        }

        for result in analysis_results:
            sentiment = result.get('llm_analysis', {}).get('sentiment', 'neutral')
            sentiment = sentiment.lower()
            if sentiment == 'bullish':
                sentiment_counts['Bullish'] += 1
            elif sentiment == 'bearish':
                sentiment_counts['Bearish'] += 1
            elif sentiment == 'fear':
                sentiment_counts['Fear'] += 1
            elif sentiment == 'excited':
                sentiment_counts['Excited'] += 1
            else:
                sentiment_counts['Neutral'] += 1

        labels = list(sentiment_counts.keys())
        counts = list(sentiment_counts.values())
        colors = ['#22c55e', '#ef4444', '#eab308', '#f97316', '#3b82f6']

        plt.figure(figsize=(10, 6))
        bars = plt.bar(labels, counts, color=colors)
        plt.title('Sentiment Distribution of Crypto News')
        plt.xlabel('Sentiment')
        plt.ylabel('Count')
        plt.grid(axis='y', alpha=0.3)

        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height}', ha='center', va='bottom')

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Sentiment distribution plot saved to {output_path}")

    def get_coingecko_price(self, token_symbol: str, days: int = 7) -> Optional[Dict[str, Any]]:
        try:
            response = requests.get(
                f"{Config.COINGECKO_BASE_URL}/coins/markets",
                params={
                    'vs_currency': 'usd',
                    'ids': token_symbol.lower(),
                    'order': 'market_cap_desc',
                    'per_page': 1,
                    'page': 1,
                    'sparkline': False,
                    'price_change_percentage': '24h,7d,30d'
                }
            )
            if response.status_code == 200 and response.json():
                return response.json()[0]
        except Exception as e:
            logger.error(f"CoinGecko API error: {e}")
        return None