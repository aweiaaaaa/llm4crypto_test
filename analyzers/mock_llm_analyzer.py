import json
import hashlib
import random
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from configs.config import Config
from utils.helpers import save_to_json, logger

class MockLLMAnalyzer:
    def __init__(self):
        self.cache = {}
        self.cache_file = f"{Config.ANALYSIS_DIR}/analysis_cache.json"
        self._load_cache()

    def _load_cache(self):
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                self.cache = json.load(f)
        except FileNotFoundError:
            self.cache = {}

    def _save_cache(self):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2)

    def _get_cache_key(self, text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def _extract_tokens(self, text: str) -> List[str]:
        common_tokens = ['BTC', 'ETH', 'SOL', 'BNB', 'USDT', 'ADA', 'XRP', 'DOGE']
        tokens = []
        text_upper = text.upper()
        for token in common_tokens:
            if token in text_upper or f'${token}' in text_upper:
                tokens.append(token)
        return tokens if tokens else ['BTC']

    def _analyze_sentiment(self, text: str) -> Tuple[str, str, str]:
        bullish_words = ['approve', 'launch', 'increase', 'rise', 'bullish', 'up', 'positive', 'good', 'great', 'excellent', 'success', 'win', 'profit', 'gain', 'surge', 'rally', 'breakout']
        bearish_words = ['reject', 'fail', 'decline', 'drop', 'bearish', 'down', 'negative', 'bad', 'loss', 'crash', 'sell', 'dump', 'plunge', 'collapse']
        fear_words = ['fear', 'panic', 'risk', 'danger', 'warning', 'alert', 'concern', 'uncertainty', 'crisis']
        excited_words = ['excited', 'amazing', 'huge', 'massive', 'big', 'breakthrough', 'historic', 'explosive']
        anticipation_words = ['expect', 'will', 'going', '预测', '预期', '可能']

        text_lower = text.lower()

        predictive = any(word in text_lower for word in anticipation_words + ['will', 'going', 'expect', 'predict', 'forecast'])

        if any(word in text_lower for word in excited_words):
            sentiment = 'excited'
            emotion = 'JOY'
        elif any(word in text_lower for word in fear_words):
            sentiment = 'fear'
            emotion = 'FEAR'
        elif any(word in text_lower for word in bullish_words):
            sentiment = 'bullish'
            emotion = 'JOY'
        elif any(word in text_lower for word in bearish_words):
            sentiment = 'bearish'
            emotion = 'ANGER'
        else:
            sentiment = random.choice(['neutral', 'bullish', 'bearish'])
            emotion = random.choice(['TRUST', 'ANTICIPATION', 'SURPRISE'])

        if predictive:
            if sentiment in ['bullish', 'excited']:
                direction = 'incremental'
            elif sentiment in ['bearish', 'fear']:
                direction = 'decremental'
            else:
                direction = 'neutral'
        else:
            direction = 'neutral'

        return sentiment, emotion, direction

    def analyze_text(self, text: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        if use_cache:
            cache_key = self._get_cache_key(text)
            if cache_key in self.cache:
                logger.debug("Using cached analysis")
                return self.cache[cache_key]

        tokens = self._extract_tokens(text)
        sentiment, primary_emotion, predictive_direction = self._analyze_sentiment(text)

        is_predictive = predictive_direction != 'neutral'

        importance = random.randint(3, 8)
        importance_reasons = [
            '涉及主流代币，市场关注度高',
            '信息来源可靠，影响较大',
            '可能引发短期市场波动',
            '涉及监管政策变化',
            '与重大事件相关',
            '包含价格预测成分',
            '涉及技术突破或创新'
        ]

        emotion_explanations = {
            'JOY': '表达积极情绪，对市场前景乐观',
            'FEAR': '表达担忧和不确定性',
            'ANGER': '表达对负面事件的不满',
            'ANTICIPATION': '对即将发生的事件有预期',
            'SADNESS': '表达失望或损失情绪',
            'TRUST': '表达对信息源的信任',
            'SURPRISE': '表达对意外事件的惊讶'
        }

        is_relevant = True if tokens else False

        reasoning_chain = [
            f"主要话题: 加密货币市场相关，提到 {', '.join(tokens) if tokens else '通用市场'}",
            f"预测性判断: {'是' if is_predictive else '否'}，{'方向性预测' if predictive_direction != 'neutral' else '事实性陈述'}",
            f"情绪分析: {primary_emotion} -> 市场情绪 {sentiment}",
            f"综合评估: 重要性 {importance}/10，时间尺度 {random.choice(['short-term', 'medium-term', 'long-term'])}"
        ]

        if is_predictive:
            market_impact = 'positive' if predictive_direction == 'incremental' else 'negative' if predictive_direction == 'decremental' else 'neutral'
        else:
            market_impact = 'neutral' if sentiment == 'neutral' else 'positive' if sentiment in ['bullish', 'excited'] else 'negative'

        analysis = {
            'reasoning_chain': reasoning_chain,
            'is_predictive': is_predictive,
            'predictive_direction': predictive_direction if is_predictive else None,
            'relevant': is_relevant,
            'tokens': tokens,
            'sentiment': sentiment,
            'primary_emotion': primary_emotion,
            'emotion_explanation': emotion_explanations.get(primary_emotion, '市场情绪中性'),
            'time_scale': random.choice(['short-term', 'medium-term', 'long-term']),
            'importance': importance,
            'importance_reason': random.choice(importance_reasons),
            'is_market_relevant': is_relevant,
            'market_impact': market_impact,
            'summary': f"分析文本涉及{', '.join(tokens) if tokens else '市场整体'}，情绪倾向为{sentiment}，{'包含预测性陈述' if is_predictive else '属于事实性陈述'}，重要性评分为{importance}分。"
        }

        if use_cache:
            cache_key = self._get_cache_key(text)
            self.cache[cache_key] = analysis
            self._save_cache()

        logger.info(f"Mock analysis completed for text: {text[:30]}...")
        return analysis

    def analyze_batch(self, texts: List[str], use_cache: bool = True) -> List[Dict[str, Any]]:
        results = []
        for i, text in enumerate(texts):
            analysis = self.analyze_text(text, use_cache)
            if analysis:
                analysis['original_text'] = text
                analysis['index'] = i
                results.append(analysis)
            logger.info(f"Analyzed {i+1}/{len(text)} texts")
        return results

    def analyze_dataset(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for item in data:
            text = item.get('text', '')
            if text:
                analysis = self.analyze_text(text)
                if analysis:
                    result = {**item, 'llm_analysis': analysis}
                    results.append(result)
        return results

    def get_coingecko_price(self, token_symbol: str, days: int = 7) -> Optional[Dict[str, Any]]:
        return {
            'id': token_symbol.lower(),
            'symbol': token_symbol.lower(),
            'name': token_symbol,
            'current_price': random.uniform(10000, 70000),
            'price_change_percentage_24h': random.uniform(-5, 5),
            'price_change_percentage_7d': random.uniform(-10, 10)
        }

    def get_price_history(self, token_id: str, days: int = 30) -> Optional[List[Dict[str, Any]]]:
        prices = []
        base_price = random.uniform(10000, 70000)
        for i in range(days * 24):
            prices.append({
                'timestamp': (datetime.now(timezone.utc) - timedelta(hours=i)).isoformat(),
                'price': base_price * (1 + random.uniform(-0.02, 0.02))
            })
        return prices[::-1]

    def calculate_correlation(self, analysis_results: List[Dict[str, Any]], 
                              price_data: List[Dict[str, Any]]) -> float:
        if not analysis_results or not price_data:
            return 0.0
        return random.uniform(-0.5, 0.5)

    def _sentiment_to_score(self, sentiment: str) -> float:
        sentiment_map = {
            'bullish': 1.0,
            'excited': 0.8,
            'neutral': 0.0,
            'fear': -0.8,
            'bearish': -1.0
        }
        return sentiment_map.get(sentiment, 0.0)

    def generate_report(self, analysis_results: List[Dict[str, Any]], 
                        output_file: Optional[str] = None) -> str:
        if not analysis_results:
            return "No analysis results to generate report."
        
        report = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'total_analyzed': len(analysis_results),
            'relevant_count': sum(1 for r in analysis_results if r['llm_analysis'].get('relevant')),
            'sentiment_distribution': {},
            'importance_distribution': {},
            'token_analysis': {},
            'summary': ''
        }
        
        for result in analysis_results:
            analysis = result['llm_analysis']
            sentiment = analysis.get('sentiment', 'neutral')
            importance = analysis.get('importance', 0)
            tokens = analysis.get('tokens', [])
            
            report['sentiment_distribution'][sentiment] = report['sentiment_distribution'].get(sentiment, 0) + 1
            report['importance_distribution'][importance] = report['importance_distribution'].get(importance, 0) + 1
            
            for token in tokens:
                if token not in report['token_analysis']:
                    report['token_analysis'][token] = {'count': 0, 'sentiments': []}
                report['token_analysis'][token]['count'] += 1
                report['token_analysis'][token]['sentiments'].append(sentiment)
        
        bullish = report['sentiment_distribution'].get('bullish', 0) + report['sentiment_distribution'].get('excited', 0)
        bearish = report['sentiment_distribution'].get('bearish', 0) + report['sentiment_distribution'].get('fear', 0)
        neutral = report['sentiment_distribution'].get('neutral', 0)
        
        report['summary'] = f"""
        Analysis Summary:
        - Total analyzed: {report['total_analyzed']}
        - Relevant: {report['relevant_count']} ({(report['relevant_count']/report['total_analyzed']*100):.1f}%)
        - Bullish/Excited: {bullish} ({(bullish/report['total_analyzed']*100):.1f}%)
        - Bearish/Fear: {bearish} ({(bearish/report['total_analyzed']*100):.1f}%)
        - Neutral: {neutral} ({(neutral/report['total_analyzed']*100):.1f}%)
        """
        
        if not output_file:
            output_file = f"{Config.ANALYSIS_DIR}/analysis_report_{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
        
        save_to_json(report, output_file)
        logger.info(f"Analysis report saved to {output_file}")
        
        return report['summary']

    def plot_sentiment_distribution(self, analysis_results: List[Dict[str, Any]], 
                                    output_file: str = None):
        sentiments = [r['llm_analysis'].get('sentiment', 'neutral') for r in analysis_results if 'llm_analysis' in r]
        sentiment_counts = pd.Series(sentiments).value_counts()
        
        plt.figure(figsize=(10, 6))
        sentiment_counts.plot(kind='bar', color=['green', 'red', 'gray', 'orange', 'blue'])
        plt.title('Sentiment Distribution')
        plt.xlabel('Sentiment')
        plt.ylabel('Count')
        plt.xticks(rotation=45)
        
        if output_file:
            plt.savefig(output_file, bbox_inches='tight')
            logger.info(f"Sentiment distribution plot saved to {output_file}")
        else:
            plt.show()

if __name__ == "__main__":
    analyzer = MockLLMAnalyzer()
    test_text = "Bitcoin ETF approval expected next week, analysts predict significant price increase."
    result = analyzer.analyze_text(test_text)
    print(json.dumps(result, indent=2, ensure_ascii=False))