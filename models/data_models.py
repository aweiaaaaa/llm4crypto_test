from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator

class Sentiment(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    FEAR = "fear"
    EXCITED = "excited"

class TimeScale(str, Enum):
    SHORT_TERM = "short-term"
    MEDIUM_TERM = "medium-term"
    LONG_TERM = "long-term"

class NewsItem(BaseModel):
    id: str = Field(description="Unique identifier for the news item")
    title: str = Field(description="Title of the news/article")
    text: str = Field(description="Content/text of the news")
    source_name: str = Field(description="Source name")
    news_url: Optional[str] = Field(None, description="URL to the original news")
    image_url: Optional[str] = Field(None, description="URL to the image")
    timestamp: datetime = Field(description="Timestamp of the news")
    data_source: str = Field(description="Data source (twitter, telegram, coingecko, etc.)")
    tokens: List[str] = Field(default_factory=list, description="List of mentioned crypto tokens")
    
    @validator('timestamp')
    def ensure_utc(cls, v):
        if v.tzinfo is None:
            raise ValueError("Timestamp must include timezone info")
        return v

class ProcessedNewsItem(NewsItem):
    sentiment: Sentiment = Field(description="Sentiment classification")
    importance: int = Field(ge=1, le=10, description="Importance score (1-10)")
    importance_reason: str = Field(description="Reason for importance score")
    is_market_relevant: bool = Field(description="Whether the news is market relevant")
    time_scale: TimeScale = Field(description="Expected impact duration")
    summary: str = Field(description="Concise summary of the news impact")

class AnalysisResult(BaseModel):
    processed_news: List[ProcessedNewsItem] = Field(default_factory=list)
    total_analyzed: int = 0
    relevant_count: int = 0
    sentiment_distribution: Dict[str, int] = Field(default_factory=dict)
    importance_distribution: Dict[str, int] = Field(default_factory=dict)
    token_analysis: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=lambda: datetime.now())

class TwitterTweet(BaseModel):
    author_name: str = Field(description="Author display name")
    author_handle: str = Field(description="Author Twitter handle")
    tweet_text: str = Field(description="Tweet content")
    timestamp: datetime = Field(description="Tweet timestamp")
    retweets: int = Field(default=0, description="Number of retweets")
    likes: int = Field(default=0, description="Number of likes")
    replies: int = Field(default=0, description="Number of replies")
    mentioned_coins: List[str] = Field(default_factory=list, description="Mentioned crypto tokens")
    data_source: str = Field("twitter")
    scraped_at: datetime = Field(default_factory=lambda: datetime.now())

class TelegramMessage(BaseModel):
    sender_name: Optional[str] = Field(None, description="Sender name")
    sender_id: Optional[int] = Field(None, description="Sender ID")
    channel: str = Field(description="Channel name")
    text: str = Field(description="Message content")
    date: datetime = Field(description="Message timestamp")
    views: int = Field(default=0, description="Number of views")
    forwards: int = Field(default=0, description="Number of forwards")
    has_media: bool = Field(default=False, description="Whether message has media")
    data_source: str = Field("telegram")
    scraped_at: datetime = Field(default_factory=lambda: datetime.now())

class CoinGeckoMarketData(BaseModel):
    id: str = Field(description="CoinGecko coin ID")
    symbol: str = Field(description="Token symbol")
    name: str = Field(description="Coin name")
    current_price: float = Field(description="Current price in USD")
    market_cap: Optional[float] = Field(None, description="Market capitalization")
    market_cap_rank: Optional[int] = Field(None, description="Market cap rank")
    total_volume: Optional[float] = Field(None, description="24h trading volume")
    price_change_percentage_24h: Optional[float] = Field(None, description="24h price change %")
    high_24h: Optional[float] = Field(None, description="24h high")
    low_24h: Optional[float] = Field(None, description="24h low")
    data_source: str = Field("coingecko")
    scraped_at: datetime = Field(default_factory=lambda: datetime.now())

class CoinMarketCalEvent(BaseModel):
    event_id: str = Field(description="Event ID")
    event_name: str = Field(description="Event name")
    description: Optional[str] = Field(None, description="Event description")
    coins: List[str] = Field(default_factory=list, description="Related coins")
    coin_symbols: List[str] = Field(default_factory=list, description="Coin symbols")
    categories: List[str] = Field(default_factory=list, description="Event categories")
    date: datetime = Field(description="Event date")
    importance: str = Field(description="Importance level")
    source_url: Optional[str] = Field(None, description="Source URL")
    is_hot: bool = Field(default=False, description="Whether event is hot")
    data_source: str = Field("coinmarketcal")
    scraped_at: datetime = Field(default_factory=lambda: datetime.now())

class AnalysisSummary(BaseModel):
    total_analyzed: int = 0
    relevant_count: int = 0
    bullish_count: int = 0
    bearish_count: int = 0
    neutral_count: int = 0
    fear_count: int = 0
    excited_count: int = 0
    avg_importance: float = 0.0
    top_tokens: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now())
    summary: str = Field("", description="Human-readable summary of the analysis")