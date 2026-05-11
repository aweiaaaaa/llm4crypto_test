# LLM4Crypto - 加密货币信息采集与分析系统

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

基于大语言模型(LLM)的加密货币信息采集与分析系统，实现从原始数据采集、清洗处理到LLM结构化情绪分析的完整闭环流程。

## 🎯 项目概述

LLM4Crypto 是一个综合性的加密货币数据分析平台，集成多个数据源，通过大语言模型进行深度情绪分析和市场洞察。

### 核心功能
- **多源数据采集**: Twitter/X、Telegram、CoinMarketCal、CoinGecko、Reddit
- **智能数据清洗**: 广告过滤、代币提取、数据标准化
- **LLM情绪分析**: 情绪倾向、重要性评分、时间尺度分析
- **可视化报告**: 自动生成分析报告和图表

## 📁 项目结构

```
llm4crypto/
├── collectors/              # 数据采集模块
│   ├── coingecko_collector.py      # CoinGecko市场数据采集
│   ├── coinmarketcal_collector.py  # CoinMarketCal事件采集
│   ├── reddit_praw_collector.py    # Reddit数据采集
│   ├── telegram_collector.py       # Telegram数据采集
│   └── twitter_scweet_collector.py # Twitter/X数据采集(Scweet)
├── cleaners/                # 数据清洗模块
│   └── data_cleaner.py             # 数据清洗与预处理
├── analyzers/               # 分析模块
│   ├── llm_analyzer.py             # LLM情绪分析器
│   └── mock_llm_analyzer.py        # Mock分析器(测试用)
├── models/                  # 数据模型
│   └── data_models.py              # Pydantic数据模型定义
├── configs/                 # 配置文件
│   └── config.py                   # 系统配置管理
├── utils/                   # 工具模块
│   └── helpers.py                  # 辅助函数
├── data/                    # 数据存储目录
│   ├── raw/                        # 原始数据
│   ├── cleaned/                    # 清洗后数据
│   └── analysis/                   # 分析结果
├── logs/                    # 日志目录
├── .env                     # 环境变量配置(不上传)
├── .env.example             # 环境变量模板
├── .gitignore               # Git忽略配置
├── requirements.txt         # 依赖清单
├── main.py                  # 主入口
├── large_scale_test.py      # 大规模测试脚本
├── audit_test_results.py    # 审计测试脚本
├── AUDIT_REPORT.md          # 审计报告
├── FINAL_SUMMARY.md         # 最终总结报告
└── README.md                # 使用说明
```

## 🛠️ 环境要求

- **Python**: 3.9+
- **浏览器**: Microsoft Edge（用于Twitter爬虫）
- **EdgeDriver**: 与Edge浏览器版本匹配

## 📦 安装步骤

### 1. 克隆项目

```bash
git clone <your-github-repo-url>
cd llm4crypto
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env
```

编辑 `.env` 文件，填入您的API密钥：

```env
# CoinMarketCal API
COINMARKETCAL_API_KEY=your_coinmarketcal_api_key

# Telegram API (可选)
TELEGRAM_API_ID=your_telegram_api_id
TELEGRAM_API_HASH=your_telegram_api_hash
TELEGRAM_PHONE=your_telegram_phone_number

# LLM API
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=glm-4-flash
OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/chat/completions

# Twitter/X配置
TWITTER_AUTH_TOKEN=your_twitter_auth_token
TWITTER_PROXY=

# Reddit配置 (可选)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=llm4crypto/1.0 by LLM4Crypto

# 浏览器驱动
CHROMEDRIVER_PATH=/path/to/msedgedriver.exe
```

### 4. 获取API密钥

| 服务 | 获取地址 |
|------|----------|
| CoinMarketCal | https://coinmarketcal.com/en/api |
| Telegram | https://my.telegram.org |
| OpenAI/GLM | https://platform.openai.com 或 https://open.bigmodel.cn |
| Reddit | https://www.reddit.com/prefs/apps |
| Twitter Auth Token | 从浏览器Cookie获取 |

## 🚀 使用方法

### 完整流程运行

```bash
# 运行完整数据采集、清洗、分析流程
python main.py full --sources coinmarketcal twitter coingecko
```

### 单独执行各步骤

#### 数据采集
```bash
python main.py collect --sources coinmarketcal twitter coingecko
```

#### 数据清洗
```bash
python main.py clean --sources coinmarketcal twitter coingecko
```

#### LLM分析
```bash
python main.py analyze
```

### 大规模测试

```bash
# 执行完整测试流程并生成报告
python large_scale_test.py
```

### 审计测试结果

```bash
python audit_test_results.py
```

## 🔧 功能模块

### 1. 数据采集模块

| 采集器 | 数据源 | 功能描述 |
|--------|--------|----------|
| `coingecko_collector.py` | CoinGecko API | 获取250+加密货币市场数据（价格、市值、交易量） |
| `coinmarketcal_collector.py` | CoinMarketCal API | 获取加密货币事件（发布会、合作、上线等） |
| `twitter_scweet_collector.py` | Twitter/X | 使用Scweet库采集指定账号推文和关键词搜索 |
| `telegram_collector.py` | Telegram | 使用Telethon库采集频道消息 |
| `reddit_praw_collector.py` | Reddit | 使用PRAW库采集加密货币相关子版块 |

### 2. 数据清洗模块 (`data_cleaner.py`)

- **广告检测**: 分级关键词策略，精准过滤垃圾信息
- **代币提取**: 基于CoinGecko代币列表自动识别
- **数据标准化**: 统一时间格式、来源标识
- **去重处理**: 去除重复内容
- **质量评估**: 输出清洗统计报告

### 3. LLM分析模块 (`llm_analyzer.py`)

**分析维度**:
- ✅ **相关性**: 判断内容与加密货币市场的相关程度
- ✅ **代币列表**: 提取提到的加密货币符号
- ✅ **情绪倾向**: 看涨/看跌/中性/恐慌/兴奋
- ✅ **时间尺度**: 短期/中期/长期影响
- ✅ **重要性评分**: 1-10分重要性评估

**输出格式**:
```json
{
  "sentiment": "bullish",
  "importance": 8,
  "time_scale": "short",
  "tokens": ["BTC", "ETH"],
  "confidence": 0.85,
  "summary": "分析摘要..."
}
```

## 📊 输出文件

```
data/
├── raw/                     # 原始采集数据
│   ├── coingecko_market_*.json
│   ├── twitter_tweets_*.json
│   └── coinmarketcal_events_*.json
├── cleaned/                 # 清洗后数据
│   ├── cleaned_coingecko_*.json
│   └── cleaned_twitter_*.json
├── analysis/                # LLM分析结果
├── audit_report_*.json      # 审计报告
├── test_results_*.json      # 测试结果
└── visualization_*.png      # 可视化图表
```

## 📝 配置说明

### 支持的数据源

```bash
# 可用数据源
coinmarketcal    # 加密货币事件
twitter          # Twitter/X推文
coingecko        # 市场数据
telegram         # Telegram频道(需配置)
reddit           # Reddit论坛(需配置)
```

### 环境变量详解

| 变量名 | 必填 | 说明 |
|--------|------|------|
| COINMARKETCAL_API_KEY | 是 | CoinMarketCal API密钥 |
| OPENAI_API_KEY | 是 | LLM API密钥 |
| OPENAI_MODEL | 否 | 模型名称(默认: glm-4-flash) |
| OPENAI_BASE_URL | 否 | API基础URL |
| TWITTER_AUTH_TOKEN | 否 | Twitter认证令牌 |
| TELEGRAM_API_ID | 否 | Telegram API ID |
| TELEGRAM_API_HASH | 否 | Telegram API Hash |
| REDDIT_CLIENT_ID | 否 | Reddit客户端ID |
| REDDIT_CLIENT_SECRET | 否 | Reddit客户端密钥 |
| CHROMEDRIVER_PATH | 是 | EdgeDriver路径 |

## 🔒 安全注意事项

1. **敏感信息**: `.env` 文件包含敏感API密钥，已加入 `.gitignore`，不会上传到GitHub
2. **API调用频率**: 请合理控制调用频率，避免触发API限制
3. **数据隐私**: 采集的数据仅供学习研究使用，遵守平台使用条款
4. **Token安全**: Twitter Auth Token应妥善保管，避免泄露

## 📈 性能优化

- **缓存机制**: 使用TTLCache避免重复分析相同内容
- **异步处理**: Telegram采集支持异步获取
- **批量处理**: 数据清洗支持批量操作
- **降级策略**: LLM API失败时自动切换到Mock分析器

## 🧪 测试与审计

### 运行测试

```bash
# 大规模测试
python large_scale_test.py

# 审计测试结果
python audit_test_results.py
```

### 生成报告

运行测试后自动生成：
- `AUDIT_REPORT.md` - 详细审计报告
- `FINAL_SUMMARY.md` - 最终总结报告
- `data/test_results_*.json` - 测试结果数据

## 🛡️ 错误处理

系统包含完善的错误处理机制：

| 错误类型 | 处理方式 |
|----------|----------|
| API调用失败 | 自动重试(最多3次) |
| LLM API不可用 | 自动切换到Mock分析器 |
| 爬虫驱动失败 | 提供手动配置路径方案 |
| 网络超时 | 延迟重试 |

## 🛠️ 技术栈

| 分类 | 技术 | 版本 |
|------|------|------|
| 数据采集 | requests | 2.31+ |
| 数据采集 | selenium | 4.15+ |
| 数据采集 | Scweet | 1.5+ |
| 数据采集 | telethon | 1.34+ |
| 数据采集 | praw | 7.7+ |
| LLM集成 | openai | 1.3+ |
| 数据模型 | pydantic | 2.5+ |
| 配置管理 | python-dotenv | 1.0+ |
| 缓存 | cachetools | 5.3+ |
| 可视化 | matplotlib | 3.8+ |

## 📄 License

MIT License - 详见 LICENSE 文件

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📧 联系方式

如有问题或建议，欢迎通过Issue联系。

---

**⚠️ 重要提醒**: 请确保 `.env` 文件中的敏感信息已正确配置，且不会被上传到GitHub。本项目仅供学习研究使用，请遵守各平台的使用条款。
