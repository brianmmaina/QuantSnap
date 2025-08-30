# QuantSnap - Stock Analysis Platform

A professional stock analysis application built with Streamlit and yfinance, featuring real-time market data and quantitative analysis.

## Overview

QuantSnap provides comprehensive stock analysis using a proprietary scoring algorithm that evaluates stocks based on traditional financial metrics and quality factors. The application analyzes 500+ stocks and ranks the top performers using real-time data from Yahoo Finance.

## Features

- **Real-Time Stock Data**: Direct integration with Yahoo Finance API
- **Quantitative Analysis**: Proprietary 67/33 weighted scoring algorithm
- **Interactive Charts**: Plotly charts with multiple time periods
- **Live Market Data**: Real-time price tracking and performance metrics
- **Stock Rankings**: Top 10 ranked stocks based on comprehensive analysis
- **News Integration**: Real-time financial news with sentiment analysis
- **Professional UI**: Bloomberg Terminal-inspired dark theme interface

## Architecture

### Frontend Application
- **Streamlit**: Web application framework for rapid development
- **yfinance**: Direct Yahoo Finance data integration
- **Plotly**: Interactive data visualization
- **Pandas/NumPy**: Data manipulation and numerical analysis

### Data Flow
1. **Data Fetching**: Direct yfinance calls for real-time stock data
2. **Metrics Calculation**: 1-month/3-month growth, volatility, Sharpe ratio
3. **Scoring Algorithm**: Weighted analysis of traditional and quality factors
4. **Ranking**: Top 10 stocks displayed with detailed metrics

## Installation

### Prerequisites
- Python 3.8+
- pip package manager
- Google Gemini API key (optional, for AI analysis)
- News API key (optional, for news features)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-daily-draft
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp env.template .env
   # Edit .env and add your API keys
   ```

### Running the Application

```bash
streamlit run frontend/app.py
```

The application will be available at `http://localhost:8501`

## Scoring Algorithm

### Traditional Factors (67% Weight)
- **1-Month Stock Price Growth** (40%): Recent price performance over 30 calendar days
- **3-Month Stock Price Growth** (25%): Medium-term price performance over 90 calendar days
- **Sharpe Ratio** (15%): Risk-adjusted returns relative to volatility
- **Volume Factor** (10%): Trading activity and liquidity
- **Market Cap Factor** (10%): Company size and stability

### Quality Factors (33% Weight)
- **Volatility Quality**: Lower volatility receives higher quality scores
- **Consistency**: Stable performance patterns are rewarded
- **Risk Management**: Balanced risk-return profiles are preferred

### Performance Filters
Stocks with poor recent performance receive penalties to ensure quality:
- **-90% penalty**: 1-month growth below -5%
- **-70% penalty**: 1-month growth below 0%
- **-30% penalty**: 1-month growth below 2%

## Stock Universe

The application analyzes approximately 500 stocks including:
- **S&P 500 components**: Large-cap US stocks
- **Technology leaders**: AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA
- **Financial sector**: JPM, BAC, WFC, GS, MS
- **Healthcare**: JNJ, PFE, UNH, ABBV, MRK
- **Consumer goods**: PG, KO, PEP, WMT, HD
- **Energy**: XOM, CVX, COP, EOG, SLB
- **And many more**: Comprehensive coverage across all sectors

## Metrics Calculated

### Price Performance
- **Current Price**: Latest closing price
- **1-Month Change**: Percentage change over 30 days
- **3-Month Change**: Percentage change over 90 days
- **Price Change**: Absolute and percentage change from previous close

### Risk Metrics
- **Volatility**: Standard deviation of returns (annualized)
- **Sharpe Ratio**: Risk-adjusted returns (assuming 0% risk-free rate)
- **Beta**: Market correlation (calculated from price data)

### Volume Analysis
- **Volume Factor**: Trading activity relative to average
- **Liquidity Assessment**: Based on average daily volume

## User Interface

### Main Dashboard
- **Stock Rankings**: Top 10 stocks with scores and key metrics
- **Performance Cards**: Average scores and returns across the universe
- **Market Overview**: Summary statistics and trends

### Interactive Features
- **Stock Search**: Analyze any stock with custom ticker input
- **Price Charts**: Interactive Plotly charts with multiple time periods
- **News Section**: Real-time financial news with sentiment analysis
- **Methodology**: Detailed explanation of the scoring algorithm

### Visual Design
- **Dark Theme**: Professional terminal-style interface
- **Bloomberg-inspired**: Clean, financial-focused design
- **Responsive Layout**: Optimized for desktop and mobile viewing
- **Custom Styling**: Monochrome section titles and professional typography

## Data Sources

### Primary Data
- **Yahoo Finance**: Real-time stock prices, volume, and historical data
- **Automatic Adjustments**: Dividends and stock splits handled automatically
- **Real-time Updates**: Data refreshed on each application session

### News Integration
- **News API**: Real-time financial news articles
- **Sentiment Analysis**: Automated sentiment classification
- **Stock-specific News**: Filtered news for individual tickers

## Technical Implementation

### Dependencies
```
streamlit>=1.36
pandas>=2.2
yfinance>=0.2.18
plotly>=5.19
numpy>=1.24.3
python-dotenv>=1.0
requests>=2.32
```

### Key Functions
- **fetch_stock_data()**: Retrieves historical price data from yfinance
- **calculate_metrics()**: Computes performance and risk metrics
- **calculate_score()**: Applies the weighted scoring algorithm
- **fetch_news()**: Retrieves and processes financial news
- **ticker_tape()**: Displays live stock performance ticker

### Scoring Algorithm Implementation

```python
def calculate_metrics(ticker_data):
    """Calculate comprehensive stock metrics"""
    returns = ticker_data['Close'].pct_change().dropna()
    
    # Price performance metrics
    month_return = ((ticker_data['Close'].iloc[-1] / ticker_data['Close'].iloc[-30]) - 1) * 100
    three_month_return = ((ticker_data['Close'].iloc[-1] / ticker_data['Close'].iloc[-90]) - 1) * 100
    
    # Risk metrics
    volatility = returns.std() * np.sqrt(252) * 100
    
    # Sharpe ratio (assuming 0% risk-free rate)
    if returns.std() > 0:
        sharpe_ratio = (returns.mean() * 252) / (returns.std() * np.sqrt(252))
    else:
        sharpe_ratio = 0
    
    return {
        'current_price': ticker_data['Close'].iloc[-1],
        'pct_change_1m': month_return,
        'pct_change_3m': three_month_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe_ratio,
        'price_change': ticker_data['Close'].iloc[-1] - ticker_data['Close'].iloc[-2],
        'price_change_pct': ((ticker_data['Close'].iloc[-1] / ticker_data['Close'].iloc[-2]) - 1) * 100
    }

def calculate_score(metrics):
    """Applied weighted scoring algorithm (0-10 scale)"""
    pct_change_1m = metrics.get('pct_change_1m', 0)
    pct_change_3m = metrics.get('pct_change_3m', 0)
    sharpe_ratio = metrics.get('sharpe_ratio', 0)
    
    # Apply performance filters
    if pct_change_1m < -5:
        pct_change_1m *= 0.1  # 90% penalty
    elif pct_change_1m < 0:
        pct_change_1m *= 0.3  # 70% penalty
    elif pct_change_1m < 2:
        pct_change_1m *= 0.7  # 30% penalty
    
    # Weighted scoring (67% traditional factors)
    traditional_score = (
        (pct_change_1m * 0.4) +      # 40% of traditional
        (pct_change_3m * 0.25) +     # 25% of traditional
        (sharpe_ratio * 0.15) +      # 15% of traditional
        (volume_factor * 0.1) +      # 10% of traditional
        (market_cap_factor * 0.1)    # 10% of traditional
    )
    
    # Quality factors (33% weight)
    quality_score = calculate_quality_score(metrics)
    
    # Final weighted score
    final_score = (traditional_score * 0.67) + (quality_score * 0.33)
    
    return max(0, min(10, final_score))  # Clamp to 0-10 range
```

### AI Analysis Implementation

```python
def get_ai_analysis(ticker, metrics):
    """Generate AI analysis using Gemini API"""
    if not GEMINI_API_KEY:
        return None
    
    analysis_prompt = f"""
    Analyze the stock {ticker} with the following metrics:
    - 1-Month Growth: {metrics.get('momentum_1m', 0):.2f}%
    - 3-Month Growth: {metrics.get('momentum_3m', 0):.2f}%
    - Volatility: {metrics.get('volatility', 0):.2f}%
    - Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}
    - Current Price: ${metrics.get('current_price', 0):.2f}
    
    Provide a concise analysis including:
    1. Overall sentiment (bullish/bearish/neutral)
    2. Key strengths and weaknesses
    3. Risk assessment
    4. Investment recommendation
    
    Keep it professional and under 200 words.
    """
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{
            "parts": [{"text": analysis_prompt}]
        }]
    }
    
    response = requests.post(
        f"{url}?key={GEMINI_API_KEY}",
        headers=headers,
        json=data,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        if 'candidates' in result and len(result['candidates']) > 0:
            return result['candidates'][0]['content']['parts'][0]['text']
    
    return None
```

### News Integration

```python
def fetch_news(ticker=None, category="business"):
    """Fetching real news using News API"""
    if not NEWS_API_KEY:
        return []
    
    try:
        if ticker:
            query = f"{ticker} stock"
            url = "https://newsapi.org/v2/everything"
        else:
            url = "https://newsapi.org/v2/top-headlines"
        
        params = {
            'apiKey': NEWS_API_KEY,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 5
        }
        
        if ticker:
            params['q'] = query
        else:
            params['category'] = category
            params['country'] = 'us'
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            
            processed_news = []
            for article in articles[:5]:
                # Simple sentiment analysis
                title = article.get('title', '').lower()
                sentiment = 'neutral'
                if any(word in title for word in ['surge', 'jump', 'rise', 'gain', 'positive']):
                    sentiment = 'positive'
                elif any(word in title for word in ['fall', 'drop', 'decline', 'negative']):
                    sentiment = 'negative'
                
                processed_news.append({
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'source': article.get('source', {}).get('name', 'Unknown'),
                    'published_at': article.get('publishedAt', ''),
                    'url': article.get('url', ''),
                    'sentiment': sentiment
                })
            
            return processed_news
        
        return []
    except Exception as e:
        return []
```

## Deployment

### Streamlit Cloud
1. Push code to GitHub repository
2. Connect repository to Streamlit Cloud
3. Configure environment variables in Streamlit Cloud settings
4. Deploy with path: `frontend/app.py`

### Environment Variables
```toml
GEMINI_API_KEY = "your_gemini_api_key_here"
NEWS_API_KEY = "your_news_api_key_here"
```

## Performance Considerations

### Data Loading
- **Efficient Fetching**: Optimized yfinance calls for minimal latency
- **Caching**: Streamlit session state for improved performance
- **Error Handling**: Graceful fallbacks for network issues

### Scalability
- **Lightweight Architecture**: No database dependencies
- **Direct API Integration**: Minimal processing overhead
- **Streamlit Optimization**: Efficient rendering and updates

## Future Enhancements

- **Portfolio Tracking**: User portfolio management and analysis
- **Technical Indicators**: Advanced charting with technical analysis
- **Sector Analysis**: Industry-specific rankings and comparisons
- **Export Functionality**: Data export to CSV/Excel formats
- **Mobile Optimization**: Enhanced mobile user experience

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For questions or support, please open an issue on GitHub.

---

Built with Streamlit, yfinance, and modern Python data science tools.
 
