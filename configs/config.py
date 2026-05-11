import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    COINMARKETCAL_API_KEY = os.getenv('COINMARKETCAL_API_KEY', '')
    TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID', '')
    TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH', '')
    TELEGRAM_PHONE = os.getenv('TELEGRAM_PHONE', '')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    
    COINMARKETCAL_BASE_URL = 'https://api.coinmarketcal.com/v1'
    COINGECKO_BASE_URL = 'https://api.coingecko.com/api/v3'
    
    REQUEST_DELAY = 2
    MAX_RETRIES = 3
    
    TWITTER_TARGET_ACCOUNTS = [
        'binance',
        'WuBlockchain',
        'cz_binance',
        'Coinbase',
        'CryptoNews'
    ]
    
    TWITTER_KEYWORDS = ['$BTC', '$ETH', '$SOL']
    
    # Scweet configuration for Twitter/X scraping
    TWITTER_AUTH_TOKEN = os.getenv('TWITTER_AUTH_TOKEN', '')
    TWITTER_PROXY = os.getenv('TWITTER_PROXY', '')
    
    REDDIT_SUBREDDITS = ['CryptoCurrency', 'Bitcoin', 'ethereum', 'solana', 'cryptomarkets']
    
    # Reddit PRAW configuration
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID', '')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET', '')
    REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'llm4crypto/1.0 by LLM4Crypto')
    
    TELEGRAM_CHANNELS = [
        'https://t.me/CryptoCurrencyNews',
        'https://t.me/btc',
        'https://t.me/CryptoGeneral'
    ]
    
    OUTPUT_DIR = 'data'
    RAW_DATA_DIR = os.path.join(OUTPUT_DIR, 'raw')
    CLEANED_DATA_DIR = os.path.join(OUTPUT_DIR, 'cleaned')
    ANALYSIS_DIR = os.path.join(OUTPUT_DIR, 'analysis')
    
    LOG_FILE = 'logs/llm4crypto.log'
    
    CHROMEDRIVER_PATH = os.getenv('CHROMEDRIVER_PATH', '')
    CHROME_BINARY_PATH = os.getenv('CHROME_BINARY_PATH', '')
    
    @classmethod
    def init_dirs(cls):
        os.makedirs(cls.RAW_DATA_DIR, exist_ok=True)
        os.makedirs(cls.CLEANED_DATA_DIR, exist_ok=True)
        os.makedirs(cls.ANALYSIS_DIR, exist_ok=True)
        os.makedirs('logs', exist_ok=True)