# QuantSnap - Professional Stock Rankings

A professional quantitative stock ranking application with dark terminal-style UI. Built with Python, FastAPI, and Streamlit featuring real-time data, AI analysis, and a comprehensive multi-factor scoring model.

## Features

### **Core Functionality**
- **Multi-Factor Quantitative Model**: Stock Price Growth (1M, 3M), Volatility (30d), Sharpe Ratio (3M), Volume Factor, Market Cap, P/E Ratio
- **World's Top 500+ Stocks**: Comprehensive database including US mega-caps, international stocks, and emerging markets
- **Real-Time Data**: Daily updates using Yahoo Finance API with optimized accuracy
- **Professional Dark Terminal UI**: Dark theme with neon green accents and professional typography

### **AI-Powered Analysis**
- **Google Gemini AI Integration**: Intelligent stock analysis and recommendations
- **Risk Assessment**: AI-powered risk evaluation and investment recommendations
- **Quota Management**: Optimized API usage with free tier limits (45 requests/day buffer)
- **Fallback Analysis**: Works even without API key using quantitative factors
- **Sentiment Analysis**: AI-powered news sentiment classification
- **Natural Language Processing**: AI-generated investment insights and recommendations

### **Real-Time News Integration**
- **Market News**: Latest financial and business headlines
- **Stock-Specific News**: Relevant news for individual stocks (top 4 stocks)
- **Sentiment Analysis**: Color-coded news sentiment (positive/negative/neutral)
- **NewsAPI Integration**: Real-time news when API key is provided
- **Clickable News**: Direct links to external news sources

### **Professional Dark Terminal Design**
- **Dark Mode First**: Deep black panels with neon green accents
- **Professional Typography**: JetBrains Mono font family
- **Interactive Charts**: Plotly charts with dark terminal template
- **Live Ticker Tape**: Rotating stock price updates
- **Professional Cards**: Clean, organized layout with proper spacing

### **Stock Analysis Features**
- **Universal Chart Search**: Search any stock for price charts
- **Live Stock Prices**: Real-time price updates in 2 rows of 5
- **Portfolio Analysis**: Comprehensive performance metrics
- **Clickable Stocks**: Direct links to Yahoo Finance
- **Professional Metrics**: Clean KPI displays with proper formatting

## How It Works

1. **Data Collection**: Fetches historical price data from Yahoo Finance with auto-adjustment
2. **Factor Calculation**: Computes stock price growth, volatility, Sharpe ratio, and other metrics
3. **Composite Scoring**: Weighted algorithm combining all factors with specific multipliers
4. **AI Analysis**: Uses Gemini AI for intelligent insights and recommendations
5. **Real-Time Updates**: Live data population on backend startup
6. **Professional Display**: Dark terminal-style UI with professional theme

## Tech Stack

- **Python 3.11+**: Core application logic
- **FastAPI**: RESTful API backend
- **Streamlit**: Web interface and deployment
- **Pandas & NumPy**: Data manipulation and analysis
- **yfinance**: Real-time stock data (optimized)
- **scikit-learn**: Statistical calculations and ML algorithms
- **Plotly**: Interactive charts with dark terminal template
- **Google Gemini AI**: Advanced AI analysis and recommendations
- **Natural Language Processing**: News sentiment analysis and text processing
- **Machine Learning**: Pattern recognition and risk modeling
- **In-Memory Processing**: Simple, fast data management
- **CSV Storage**: Lightweight data persistence

## Project Structure

```
ai-daily-draft/
├── app/                 # Backend application
│   ├── main.py         # FastAPI backend
│   ├── database.py     # Data fetching and processing
│   ├── models.py       # Data models
│   ├── gemini.py       # AI integration
│   └── scraper.py      # News scraping
├── frontend/           # Frontend application
│   └── app.py          # Streamlit frontend (dark terminal theme)
├── data/               # Static data files
│   └── universes/      # Stock universe CSV files
├── requirements.txt    # Python dependencies
├── render.yaml         # Render deployment configuration
├── env.template        # Environment template
├── .gitignore         # Git ignore rules
└── README.md          # Documentation
```

## Quick Start

### **Local Development**

1. **Clone and Setup**
   ```bash
   git clone <your-repo>
   cd ai-daily-draft
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp env.template .env
   # Add your API keys to .env file:
   # GEMINI_API_KEY=your_gemini_api_key_here
   # NEWS_API_KEY=your_newsapi_key_here (optional)
   # API_BASE_URL=https://quantsnap-backend.onrender.com
   ```

3. **Run the Application**
   ```bash
   # Backend
   python3 app/main.py
   
   # Frontend
   streamlit run frontend/app.py
   ```

### **Deploy to Render**

1. **Prepare Repository**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Deploy on Render**
   - Connect your GitHub repository
   - Use the `render.yaml` blueprint
   - Set environment variables in Render dashboard
   - Deploy!

## Usage

### **View Rankings**
- See top-ranked stocks with professional dark terminal styling
- View quantitative scores and performance metrics
- Understand factor breakdowns with clear methodology

### **Search Any Stock**
- Enter any ticker symbol to analyze
- Get instant factor calculations and AI insights
- Compare with universe rankings

### **Interactive Charts**
- Search any stock for price charts
- Multiple time periods (1M, 3M, 6M, 1Y, MAX)
- Dark terminal-style charts

### **Live Data**
- Real-time stock prices for top 10 stocks
- Live ticker tape with rotating updates
- Professional metrics display

## Configuration

### **Environment Variables**
```bash
# Required for AI features
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
NEWS_API_KEY=your_news_api_key_here
API_BASE_URL=https://quantsnap-backend.onrender.com
```

## Factor Model

### **Quantitative Factors**
- **1M Stock Price Growth**: 1-month price growth (30% weight)
- **3M Stock Price Growth**: 3-month price growth (25% weight)
- **Sharpe Ratio**: Risk-adjusted returns (20% weight) - multiplied by 2.0
- **Volume Factor**: Trading activity (10% weight) - volume/1M * 0.1
- **Market Cap**: Company size (10% weight) - market cap/1T * 0.1
- **P/E Ratio**: Valuation metric (5% weight) - 1/(P/E + 1) * 0.05

### **Scoring Process**
1. **Data Collection**: Historical price data from Yahoo Finance with auto-adjustment
2. **Factor Calculation**: Compute all quantitative metrics
3. **Composite Scoring**: Combine factors with optimized weights
4. **Ranking**: Sort by composite score
5. **Real-Time Updates**: Fresh data on every session

## AI/ML Integration

### **Google Gemini AI Implementation**
- **Intelligent Stock Analysis**: AI-powered analysis of individual stocks with comprehensive insights
- **Risk Assessment**: Machine learning-based risk evaluation using multiple factors
- **Investment Recommendations**: AI-generated buy/hold/sell recommendations based on quantitative and qualitative factors
- **Market Context**: AI analysis of broader market conditions and sector trends

### **Natural Language Processing**
- **News Sentiment Analysis**: AI classification of news articles into positive, negative, or neutral sentiment
- **Keyword Analysis**: Automatic detection of market-moving keywords in news content
- **Contextual Understanding**: AI comprehension of financial news context and implications
- **Automated Summaries**: AI-generated summaries of complex financial information

### **Machine Learning Features**
- **Pattern Recognition**: AI identification of historical patterns and trends
- **Anomaly Detection**: Machine learning detection of unusual market behavior
- **Predictive Analytics**: AI-powered forecasting based on historical data patterns
- **Risk Modeling**: ML-based risk assessment using multiple quantitative factors

### **AI-Powered Insights**
- **Performance Breakdown**: AI analysis of stock performance across multiple timeframes
- **Sector Analysis**: Machine learning insights into sector-specific trends and opportunities
- **Market Position Assessment**: AI evaluation of stock performance relative to market benchmarks
- **Investment Thesis Generation**: AI-generated investment rationales and recommendations

### **Technical Implementation**
- **API Integration**: Seamless integration with Google Gemini AI API
- **Rate Limiting**: Intelligent quota management to optimize API usage
- **Error Handling**: Robust fallback mechanisms when AI services are unavailable
- **Real-Time Processing**: Fast AI analysis with minimal latency
- **Scalable Architecture**: AI services designed to handle multiple concurrent requests

### **Data Processing Pipeline**
1. **Data Collection**: Real-time market data from Yahoo Finance
2. **Feature Engineering**: Quantitative factor calculation and normalization
3. **AI Analysis**: Gemini AI processing of stock data and market context
4. **Sentiment Analysis**: AI classification of news sentiment
5. **Recommendation Generation**: AI-powered investment insights
6. **Risk Assessment**: ML-based risk evaluation and scoring

### **Code Implementation Examples**

#### **67/33 Factor Breakdown Algorithm**
```python
# 67/33 Factor Breakdown: Traditional vs Reputation Factors

# Traditional Factors (67% weight) - Quantitative metrics
traditional_score = (
    (momentum_1m * 0.3) +      # 1M stock price growth (30% of traditional)
    (momentum_3m * 0.2) +      # 3M stock price growth (20% of traditional)
    (sharpe_ratio * 0.1) +     # Sharpe ratio (10% of traditional)
    (volume_avg_20d / 1000000 * 0.04) + # Volume factor (4% of traditional)
    (market_cap / 1e12 * 0.03) + # Market cap factor (3% of traditional)
)

# Reputation Factors (33% weight) - Qualitative metrics
reputation_score = (
    (1 / (pe_ratio + 1) * 0.15) + # P/E ratio quality (15% of reputation)
    (dividend_yield * 0.1) +      # Dividend yield (10% of reputation)
    (1 / (beta + 0.1) * 0.08)     # Beta stability (8% of reputation)
)

# Combine with 67/33 weighting
score = (traditional_score * 0.67) + (reputation_score * 0.33)
```

# Performance penalty for poor recent performance
if momentum_1m < -10:  # If 1M growth is less than -10%
    score *= 0.5  # Reduce score by 50%
elif momentum_1m < 0:  # If 1M growth is negative but not too bad
    score *= 0.8  # Reduce score by 20%

# Convert to 0-100 scale for display
score_100 = min(max(score * 10, 0), 100)
```

#### **Enhanced News Sentiment Analysis**
```python
# Comprehensive AI-powered sentiment classification
def classify_sentiment(content):
    content = content.lower()
    
    # Extensive positive word dictionary
    positive_words = [
        'up', 'gain', 'rise', 'positive', 'strong', 'beat', 'surge', 'jump', 'climb', 'soar',
        'rally', 'boost', 'increase', 'growth', 'profit', 'earnings', 'revenue', 'success',
        'exceed', 'outperform', 'bullish', 'optimistic', 'favorable', 'promising', 'robust',
        'solid', 'excellent', 'outstanding', 'impressive', 'record', 'high', 'peak', 'breakthrough',
        'innovation', 'expansion', 'acquisition', 'merger', 'partnership', 'launch', 'upgrade',
        'improve', 'enhance', 'strengthen', 'accelerate', 'momentum', 'recovery', 'rebound',
        'turnaround', 'revival', 'resurgence', 'thrive', 'flourish', 'prosper', 'excel',
        'dominate', 'lead', 'outpace', 'overtake', 'surpass', 'outstrip', 'outshine'
    ]
    
    # Comprehensive negative word dictionary
    negative_words = [
        'down', 'fall', 'drop', 'negative', 'weak', 'miss', 'decline', 'plunge', 'crash',
        'tumble', 'slump', 'dip', 'slide', 'sink', 'collapse', 'downturn', 'recession',
        'loss', 'deficit', 'debt', 'bankruptcy', 'default', 'failure', 'struggle', 'challenge',
        'risk', 'volatility', 'uncertainty', 'concern', 'worry', 'fear', 'anxiety', 'stress',
        'pressure', 'tension', 'conflict', 'dispute', 'litigation', 'investigation', 'probe',
        'scandal', 'controversy', 'criticism', 'backlash', 'boycott', 'protest', 'strike',
        'layoff', 'firing', 'resignation', 'exit', 'departure', 'replacement', 'restructure',
        'cut', 'reduce', 'decrease', 'shrink', 'contract', 'retreat', 'withdraw', 'abandon',
        'cancel', 'delay', 'postpone', 'suspend', 'halt', 'stop', 'end', 'terminate'
    ]
    
    # Count word frequency for sentiment analysis
    positive_count = sum(1 for word in positive_words if word in content)
    negative_count = sum(1 for word in negative_words if word in content)
    
    # Determine sentiment based on word frequency
    if positive_count > negative_count and positive_count > 0:
        return 'positive'
    elif negative_count > positive_count and negative_count > 0:
        return 'negative'
    else:
        return 'neutral'

# Apply enhanced sentiment analysis to news articles
for article in articles:
    title = article.get('title', '').lower()
    description = article.get('description', '').lower()
    content = f"{title} {description}"
    sentiment = classify_sentiment(content)
```

#### **Gemini AI Integration**
```python
class GeminiAI:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def analyze_stock(self, stock_data: Dict) -> str:
        context = f"""
        Stock: {stock_data.get('ticker')} - {stock_data.get('name')}
        Price: ${stock_data.get('price'):.2f}
        1M Growth: {stock_data.get('momentum_1m'):.2f}%
        3M Growth: {stock_data.get('momentum_3m'):.2f}%
        Sharpe Ratio: {stock_data.get('sharpe_ratio'):.2f}
        """
        
        prompt = f"Analyze this stock data: {context}"
        response = self.model.generate_content(prompt)
        return response.text
```

#### **Quota Management**
```python
class QuotaManager:
    def __init__(self, daily_limit: int = 45):
        self.daily_limit = daily_limit
        self.requests_today = 0
    
    def can_make_request(self) -> bool:
        return self.requests_today < self.daily_limit
    
    def record_request(self):
        self.requests_today += 1
```

## Investment Strategy

### **Score Interpretation (0-100 Scale)**
- **Strong Buy (80-100)**: Excellent performance across all factors
- **Buy (60-80)**: Good performance, worth considering
- **Hold (40-60)**: Average performance, monitor closely
- **Sell (20-40)**: Poor performance, avoid for now
- **Strong Sell (0-20)**: Very poor performance, strong avoid

### **Risk Management**
- **Diversification**: Spread across multiple sectors
- **Risk-Adjusted Returns**: Prioritize Sharpe ratio
- **Volume Analysis**: Ensure sufficient liquidity
- **AI Validation**: Use AI insights for confirmation

## Professional Design

### **Dark Terminal Theme**
- **Dark Mode**: Deep black backgrounds (#0B0F10)
- **Neon Accents**: Green highlights (#00E676)
- **Professional Typography**: JetBrains Mono font
- **Clean Layout**: Organized cards with proper spacing
- **Interactive Elements**: Hover effects and smooth transitions

### **Chart Styling**
- **Dark Charts**: Dark terminal template
- **White Text**: High contrast for readability
- **Professional Colors**: Consistent color palette
- **Smooth Animations**: Professional interactions

## Security & Privacy

- **No Personal Data**: App doesn't collect or store personal information
- **API Key Security**: Environment variables for sensitive data
- **Public Data**: Uses only publicly available market data
- **No Trading**: Educational tool only, no actual trading

**Disclaimer**: This application is for educational purposes only. It does not constitute financial advice. Always do your own research and consult with financial professionals before making investment decisions.
 
