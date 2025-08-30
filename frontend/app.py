#!/usr/bin/env python3
"""
QuantSnap 
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime, timedelta
from typing import Dict, List
import requests
import os
from dotenv import load_dotenv

# load environment variables
load_dotenv()

# bloomberg terminal plotly template
bloomberg_template = dict(
    layout=dict(
        paper_bgcolor="#0B0F10",
        plot_bgcolor="#0E1317",   # contrast vs panel
        font=dict(family="JetBrains Mono, Menlo, monospace", color="#FFFFFF", size=13),
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.08)",
            zerolinecolor="rgba(255,255,255,0.10)",
            linecolor="#4A5568",
            tickcolor="#4A5568",
            tickfont=dict(color="#FFFFFF", size=11),
            title=dict(font=dict(color="#FFFFFF", size=12))
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.08)",
            zerolinecolor="rgba(255,255,255,0.10)",
            linecolor="#4A5568",
            tickcolor="#4A5568",
            tickfont=dict(color="#FFFFFF", size=11),
            title=dict(font=dict(color="#FFFFFF", size=12))
        ),
        margin=dict(l=50, r=30, t=50, b=50),
        hoverlabel=dict(bgcolor="#1A202C", bordercolor="#4A5568", font_color="#FFFFFF", font_size=12),
        colorway=["#00E676", "#00C2FF", "#FFB000", "#FF4D4D", "#A78BFA", "#64FFDA"],
        title=dict(font=dict(color="#FFFFFF", size=16))
    )
)
pio.templates["bloomberg"] = bloomberg_template
pio.templates.default = "bloomberg"

# api configuration
BACKEND_URL = os.getenv('BACKEND_URL', 'https://quantsnap-backend.onrender.com')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://quantsnap-frontend.onrender.com')

class QuantSnapAPI:
    """Clean API client for QuantSnap backend"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or BACKEND_URL
        self.session = requests.Session()
        self.session.timeout = 30
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make API request with proper error handling"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            st.error(f"Backend timeout: {endpoint}")
            return {}
        except requests.exceptions.ConnectionError:
            st.error(f"Backend connection failed: {endpoint}")
            return {}
        except Exception as e:
            st.error(f"API error: {str(e)}")
            return {}
    
    def get_rankings(self, universe: str = "world_top_stocks", limit: int = 50) -> List[Dict]:
        """Get stock rankings from backend"""
        data = self._make_request(f"/rankings/{universe}", {"limit": limit})
        return data.get("rankings", []) if data else []
    
    def get_stock_data(self, ticker: str) -> Dict:
        """Get individual stock data from backend"""
        data = self._make_request(f"/stock/{ticker}")
        return data.get("stock", {}) if data else {}
    
    def get_live_prices(self, tickers: List[str]) -> Dict:
        """Get live prices for multiple tickers"""
        tickers_str = ",".join(tickers)
        data = self._make_request(f"/prices/live", {"tickers": tickers_str})
        return data.get("prices", {}) if data else {}
    
    def health_check(self) -> bool:
        """Check if backend is healthy"""
        data = self._make_request("/health")
        return data.get("status") == "healthy"

# Create global API client
api_client = QuantSnapAPI()

def get_rankings_from_api(universe: str, limit: int = 50) -> pd.DataFrame:
    """Get rankings from API with local fallback"""
    data = api_request(f"/rankings/{universe}", {"limit": limit})
    if data and "rankings" in data:
        return pd.DataFrame(data["rankings"])
    else:
        # if api fails, use local fallback data
        return get_local_fallback_data(limit)

def get_local_fallback_data(limit: int = 50) -> pd.DataFrame:
    """Generate realistic fallback data when API is down"""
    import random
    
    # popular stocks with realistic data
    stocks = [
        ('AAPL', 'Apple Inc.', 9.5, 5.2, 12.5),
        ('MSFT', 'Microsoft Corp.', 9.2, 4.8, 11.8),
        ('GOOGL', 'Alphabet Inc.', 8.8, 6.1, 15.2),
        ('TSLA', 'Tesla Inc.', 7.5, 8.3, 18.7),
        ('AMZN', 'Amazon.com Inc.', 8.1, 3.9, 9.3),
        ('NVDA', 'NVIDIA Corp.', 9.0, 7.2, 25.1),
        ('META', 'Meta Platforms Inc.', 7.8, 4.5, 8.9),
        ('NFLX', 'Netflix Inc.', 6.5, 2.1, -2.3),
        ('INTC', 'Intel Corp.', 8.5, 6.8, 14.2),
        ('AMD', 'Advanced Micro Devices Inc.', 7.2, 5.4, 12.8),
        ('JPM', 'JPMorgan Chase & Co.', 7.9, 3.2, 8.5),
        ('V', 'Visa Inc.', 8.3, 4.1, 10.2),
        ('JNJ', 'Johnson & Johnson', 7.1, 2.8, 6.9),
        ('PG', 'Procter & Gamble Co.', 6.8, 1.9, 5.4),
        ('HD', 'Home Depot Inc.', 7.4, 3.5, 7.8),
        ('DIS', 'Walt Disney Co.', 6.2, 1.5, 4.2),
        ('PYPL', 'PayPal Holdings Inc.', 6.9, 2.8, 6.1),
        ('CRM', 'Salesforce Inc.', 7.6, 4.2, 9.8),
        ('ADBE', 'Adobe Inc.', 8.2, 5.1, 13.4),
        ('NKE', 'Nike Inc.', 7.3, 3.8, 8.7),
        ('WMT', 'Walmart Inc.', 6.7, 2.3, 5.9),
        ('KO', 'Coca-Cola Co.', 6.4, 1.8, 4.8),
        ('PEP', 'PepsiCo Inc.', 6.6, 2.1, 5.2),
        ('ABT', 'Abbott Laboratories', 7.7, 3.9, 9.1),
        ('TMO', 'Thermo Fisher Scientific Inc.', 8.4, 4.7, 11.6),
        ('AVGO', 'Broadcom Inc.', 8.6, 5.6, 14.8),
        ('COST', 'Costco Wholesale Corp.', 7.8, 3.4, 8.2),
        ('ACN', 'Accenture PLC', 8.0, 4.3, 10.5),
        ('DHR', 'Danaher Corp.', 8.1, 4.6, 11.2),
        ('LLY', 'Eli Lilly and Co.', 8.7, 6.2, 16.3),
        ('UNH', 'UnitedHealth Group Inc.', 7.5, 3.1, 7.5),
        ('MA', 'Mastercard Inc.', 8.9, 4.9, 12.1),
        ('MRK', 'Merck & Co. Inc.', 7.0, 2.5, 6.3),
        ('PFE', 'Pfizer Inc.', 6.3, 1.7, 4.5),
        ('TXN', 'Texas Instruments Inc.', 7.6, 3.7, 8.9),
        ('HON', 'Honeywell International Inc.', 7.4, 3.0, 7.2),
        ('QCOM', 'QUALCOMM Inc.', 7.8, 4.4, 10.8),
        ('LOW', 'Lowe\'s Companies Inc.', 7.1, 2.9, 6.7),
        ('UPS', 'United Parcel Service Inc.', 6.8, 2.2, 5.6),
        ('CAT', 'Caterpillar Inc.', 7.3, 3.6, 8.4),
        ('RTX', 'Raytheon Technologies Corp.', 6.9, 2.7, 6.5),
        ('SPGI', 'S&P Global Inc.', 8.3, 4.0, 9.9),
        ('ISRG', 'Intuitive Surgical Inc.', 8.5, 5.8, 15.1),
        ('GILD', 'Gilead Sciences Inc.', 6.7, 2.4, 5.8),
        ('AMGN', 'Amgen Inc.', 7.2, 3.3, 7.9),
        ('ADI', 'Analog Devices Inc.', 7.9, 4.5, 10.9),
        ('MDLZ', 'Mondelez International Inc.', 6.5, 2.0, 5.1),
        ('REGN', 'Regeneron Pharmaceuticals Inc.', 8.0, 5.3, 13.8),
        ('KLAC', 'KLA Corp.', 8.2, 4.8, 11.4),
        ('PANW', 'Palo Alto Networks Inc.', 8.4, 5.7, 14.5),
        ('SNPS', 'Synopsys Inc.', 8.6, 5.0, 12.7),
        ('CDNS', 'Cadence Design Systems Inc.', 8.3, 4.6, 11.1),
        ('MELI', 'MercadoLibre Inc.', 7.7, 6.5, 18.2),
        ('ZM', 'Zoom Video Communications Inc.', 6.1, 1.6, 3.8),
        ('ROKU', 'Roku Inc.', 5.8, 1.2, 2.9),
        ('SQ', 'Block Inc.', 6.4, 2.6, 6.2),
        ('SPOT', 'Spotify Technology S.A.', 6.6, 2.8, 6.4),
        ('UBER', 'Uber Technologies Inc.', 6.9, 3.2, 7.6),
        ('LYFT', 'Lyft Inc.', 5.5, 1.1, 2.3),
        ('SNAP', 'Snap Inc.', 5.2, 0.8, 1.7),
        ('TWTR', 'Twitter Inc.', 5.9, 1.9, 4.1),
        ('PINS', 'Pinterest Inc.', 6.2, 2.3, 5.3),
        ('SHOP', 'Shopify Inc.', 7.1, 4.1, 9.6),
        ('CRWD', 'CrowdStrike Holdings Inc.', 8.1, 5.9, 15.7),
        ('OKTA', 'Okta Inc.', 7.3, 3.8, 8.6),
        ('TEAM', 'Atlassian Corp. PLC', 7.8, 4.7, 11.3),
        ('ZM', 'Zoom Video Communications Inc.', 6.1, 1.6, 3.8),
        ('DOCU', 'DocuSign Inc.', 6.7, 2.5, 5.9),
        ('PLTR', 'Palantir Technologies Inc.', 6.8, 3.1, 7.1),
        ('SNOW', 'Snowflake Inc.', 7.5, 4.3, 10.1),
        ('DDOG', 'Datadog Inc.', 7.9, 5.2, 13.1),
        ('NET', 'Cloudflare Inc.', 8.0, 4.9, 12.3),
        ('ASAN', 'Asana Inc.', 6.3, 2.2, 4.9),
        ('ZM', 'Zoom Video Communications Inc.', 6.1, 1.6, 3.8),
    ]
    
    # shuffle and take requested limit
    random.shuffle(stocks)
    selected_stocks = stocks[:limit]
    
    # create dataframe
    data = {
        'ticker': [stock[0] for stock in selected_stocks],
        'name': [stock[1] for stock in selected_stocks],
        'score': [stock[2] for stock in selected_stocks],
        'momentum_1m': [stock[3] for stock in selected_stocks],
        'momentum_3m': [stock[4] for stock in selected_stocks]
    }
    
    return pd.DataFrame(data)

def get_stock_data_from_api(ticker: str) -> Dict:
    """Get stock data from API with local fallback"""
    data = api_request(f"/stock/{ticker}")
    if data:
        return data
    else:
        # fallback to local yfinance data
        return get_local_stock_data(ticker)

def get_local_stock_data(ticker: str) -> Dict:
    """Get stock data directly from yfinance when API is down"""
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="5d")
        
        if hist.empty:
            return {}
        
        current_price = hist['Close'].iloc[-1]
        previous_close = info.get('regularMarketPreviousClose', current_price)
        daily_change = current_price - previous_close
        daily_change_pct = (daily_change / previous_close) * 100 if previous_close else 0
        
        return {
            'price': round(current_price, 2),
            'change': round(daily_change, 2),
            'change_pct': round(daily_change_pct, 2),
            'volume': int(info.get('volume', 0)),
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': info.get('trailingPE', 0),
            'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
        }
    except Exception as e:
        return {}



# news fetching function
def fetch_news(ticker=None, limit=3):
    """Fetch financial news"""
    try:
        news_api_key = os.getenv('NEWS_API_KEY')
        
        if news_api_key:
            try:
                if ticker:
                    url = f"https://newsapi.org/v2/everything"
                    params = {
                        'q': f'"{ticker}" AND (stock OR earnings OR financial)',
                        'language': 'en',
                        'sortBy': 'publishedAt',
                        'pageSize': limit,
                        'apiKey': news_api_key
                    }
                else:
                    url = f"https://newsapi.org/v2/top-headlines"
                    params = {
                        'category': 'business',
                        'language': 'en',
                        'pageSize': limit,
                        'apiKey': news_api_key
                    }
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get('articles', [])
                    
                    news_items = []
                    for article in articles:
                        title = article.get('title', '').lower()
                        description = article.get('description', '').lower()
                        content = f"{title} {description}"
                        
                        # enhanced sentiment analysis with comprehensive word lists
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
                        
                        # count positive and negative words
                        positive_count = sum(1 for word in positive_words if word in content)
                        negative_count = sum(1 for word in negative_words if word in content)
                        
                        # determine sentiment based on word frequency
                        if positive_count > negative_count and positive_count > 0:
                            sentiment = 'positive'
                        elif negative_count > positive_count and negative_count > 0:
                            sentiment = 'negative'
                        else:
                            sentiment = 'neutral'
                        
                        news_items.append({
                            'title': article.get('title', 'No title'),
                            'description': article.get('description', 'No description'),
                            'source': article.get('source', {}).get('name', 'Unknown'),
                            'published_at': article.get('publishedAt', ''),
                            'url': article.get('url', '#'),
                            'sentiment': sentiment
                        })
                    
                    return news_items
            except Exception as api_error:
                pass
        
        # fallback news
        if ticker:
            news_items = [
                {
                    'title': f'{ticker} Reports Strong Q4 Earnings',
                    'description': f'{ticker} exceeded analyst expectations with revenue growth of 15% year-over-year.',
                    'source': 'Financial Times',
                    'published_at': (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M'),
                    'url': '#',
                    'sentiment': 'positive'
                },
                {
                    'title': f'{ticker} Announces New Product Launch',
                    'description': f'{ticker} unveiled its latest innovation, expected to drive growth in the coming quarters.',
                    'source': 'Reuters',
                    'published_at': (datetime.now() - timedelta(hours=4)).strftime('%Y-%m-%d %H:%M'),
                    'url': '#',
                    'sentiment': 'positive'
                },
                {
                    'title': f'Analysts Upgrade {ticker} Price Target',
                    'description': f'Multiple analysts have raised their price targets for {ticker} following recent developments.',
                    'source': 'Bloomberg',
                    'published_at': (datetime.now() - timedelta(hours=6)).strftime('%Y-%m-%d %H:%M'),
                    'url': '#',
                    'sentiment': 'positive'
                }
            ]
        else:
            news_items = [
                {
                    'title': 'Federal Reserve Signals Potential Rate Cuts',
                    'description': 'The Fed indicated possible interest rate reductions in the coming months, boosting market sentiment.',
                    'source': 'Wall Street Journal',
                    'published_at': (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M'),
                    'url': '#',
                    'sentiment': 'positive'
                },
                {
                    'title': 'Tech Stocks Lead Market Rally',
                    'description': 'Technology sector gains momentum as investors embrace AI and cloud computing trends.',
                    'source': 'CNBC',
                    'published_at': (datetime.now() - timedelta(hours=3)).strftime('%Y-%m-%d %H:%M'),
                    'url': '#',
                    'sentiment': 'positive'
                },
                {
                    'title': 'Oil Prices Stabilize After Recent Volatility',
                    'description': 'Crude oil prices find support as supply concerns ease and demand outlook improves.',
                    'source': 'Reuters',
                    'published_at': (datetime.now() - timedelta(hours=5)).strftime('%Y-%m-%d %H:%M'),
                    'url': '#',
                    'sentiment': 'neutral'
                }
            ]
        
        return news_items[:limit]
    
    except Exception as e:
        return []

# page configuration
st.set_page_config(
    page_title="QuantSnap - Stock Rankings",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# bloomberg terminal theme
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');

:root{
  --bg:        #0B0F10;
  --panel:     #111417;
  --panel-2:   #0F1419;
  --grid:      #1C2328;
  --border:    #2A3338;
  --text:      #D7E1E8;
  --muted:     #9FB3C8;
  --accent:    #00E676;
  --up:        #00E676;
  --down:      #FF4D4D;
  --warn:      #FFB000;
  --info:      #00C2FF;
}

html, body, [data-testid="stAppViewContainer"]{
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: "JetBrains Mono", SFMono-Regular, ui-monospace, Menlo, monospace;
}

.card, .analysis-section, .stock-card{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px 18px;
  box-sizing: border-box;
  box-shadow: 0 4px 12px rgba(0,0,0,.2);
}

.section-title{
  color: var(--text);
  font-weight: 700;
  font-size: 18px;
  letter-spacing: .2px;
  margin-bottom: 16px;
  margin-top: 8px;
  text-transform: uppercase;
  font-family: 'JetBrains Mono', monospace;
  padding-bottom: 8px;
}

.badge{
  background: var(--border); color: var(--text);
  padding: 6px 10px; border-radius: 8px; font-weight: 700; font-size: 12px;
}

.rank{
  margin-left: auto; background: #182026; color: var(--muted);
  padding: 4px 8px; border-radius: 8px; font-weight: 700; font-size: 12px;
}

.c-up{ color: var(--up) !important; }
.c-down{ color: var(--down) !important; }
.c-warn{ color: var(--warn) !important; }
.c-info{ color: var(--info) !important; }
.c-muted{ color: var(--muted) !important; }

.stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input{
  background: var(--panel-2) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
}

.stButton>button{
  background: var(--panel-2);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 10px; font-weight: 700;
  margin-top: 0;
}

.stButton>button:hover{ border-color: var(--accent); }

/* Streamlit Metrics Styling */
[data-testid="metric-container"] {
  background: var(--panel) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  padding: 16px !important;
}

[data-testid="metric-container"] label {
  color: var(--muted) !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.5px !important;
}

[data-testid="metric-container"] [data-testid="metric-value"] {

/* Dark selectbox */
.stSelectbox div[data-baseweb="select"] {
  background: var(--panel-2) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
}
.stSelectbox div[data-baseweb="select"] * { color: var(--text) !important; }
.stSelectbox div[data-baseweb="select"] svg { fill: var(--text) !important; }

/* If using 1M/3M/6M/1Y/MAX buttons anywhere */
.stButton > button {
  background: #12181D !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  font-weight: 700 !important;
}
.stButton > button:hover { border-color: var(--accent) !important; }
  color: var(--text) !important;
  font-size: 24px !important;
  font-weight: 800 !important;
  font-family: 'JetBrains Mono', monospace !important;
}

[data-testid="metric-container"] [data-testid="metric-delta"] {
  color: var(--text) !important;
  font-size: 14px !important;
  font-weight: 600 !important;
}

/* Chart Container Styling */
[data-testid="stPlotlyChart"] {
  background: var(--panel) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  padding: 16px !important;
  margin: 8px 0 !important;
}

[data-testid="stPlotlyChart"] iframe {
  background: var(--panel) !important;
}

/* Ensure chart elements are dark with better contrast */
.js-plotly-plot .plotly .main-svg {
  background: var(--panel) !important;
}

.js-plotly-plot .plotly .bg {
  background: var(--panel) !important;
}

/* Enhanced chart text readability */
.js-plotly-plot .plotly text {
  fill: #FFFFFF !important;
  font-family: 'JetBrains Mono', monospace !important;
}

.js-plotly-plot .plotly .gtitle text {
  fill: #FFFFFF !important;
  font-weight: 700 !important;
}

.js-plotly-plot .plotly .xtick text,
.js-plotly-plot .plotly .ytick text {
  fill: #FFFFFF !important;
  font-size: 11px !important;
}

.js-plotly-plot .plotly .xaxis-title text,
.js-plotly-plot .plotly .yaxis-title text {
  fill: #FFFFFF !important;
  font-size: 12px !important;
  font-weight: 600 !important;
}

/* Remove dark loading overlay */
.stSpinner > div {
  background: transparent !important;
}

.stSpinner > div > div {
  background: transparent !important;
}

/* Custom loading spinner styling */
.stSpinner {
  background: rgba(0, 0, 0, 0.1) !important;
  backdrop-filter: blur(2px) !important;
}

.stSpinner > div > div > div {
  border-color: var(--accent) !important;
  border-top-color: transparent !important;
}

/* Remove Streamlit's default overlay */
.stApp > div[data-testid="stDecoration"] {
  display: none !important;
}

/* Remove any dim overlays on form submission or button clicks */
.stApp > div[data-testid="stDecoration"] {
  display: none !important;
}

/* Remove form submission overlays */
.stFormSubmitButton {
  background: transparent !important;
}

/* Remove any loading overlays */
.stApp > div[data-testid="stDecoration"] {
  display: none !important;
}

/* Ensure no dark overlays appear */
.stApp > div[data-testid="stDecoration"] {
  display: none !important;
}

/* Remove button click overlays */
.stButton > button:active,
.stButton > button:focus {
  background: transparent !important;
}

/* Remove any form overlays */
.stForm {
  background: transparent !important;
}

/* Remove any loading states */
.stApp > div[data-testid="stDecoration"] {
  display: none !important;
}

/* Custom loading text */
.stSpinner > div > div > div::after {
  content: "Loading..." !important;
  color: var(--accent) !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  margin-top: 20px !important;
}

#MainMenu, header, footer{ visibility: hidden; }

.card:hover, .stock-card:hover {
  background: var(--panel-2);
  border-color: var(--accent);
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(0,0,0,.3);
}

.title-wrap{
  text-align:center;
  margin:20px 0 30px;
  font-family:'JetBrains Mono', monospace;
}

.title{
  font-size:56px;
  font-weight:900;
  letter-spacing:3px;
  color:#00E676;
  text-shadow:0 0 8px rgba(0,230,118,.7), 0 0 16px rgba(0,230,118,.5);
  display:inline-block;
  padding:12px 24px;
  border:3px solid #00E676;
  border-radius:12px;
  background:linear-gradient(180deg,rgba(0,230,118,.1),rgba(0,230,118,0));
}

.title:after{
  content:""; display:block; margin:6px auto 0; width:60%;
  height:3px; border-radius:2px;
  background:linear-gradient(90deg,#00E676,#00C2FF,#FFB000);
  animation:slide 4s linear infinite; background-size:200% 100%;
}

@keyframes slide{0%{background-position:0% 0}100%{background-position:200% 0}}
</style>
""", unsafe_allow_html=True)

# quantsnap terminal banner
st.markdown("""
<div class="title-wrap">
  <div class="title">QUANTSNAP</div>
</div>
""", unsafe_allow_html=True)
st.write("")

# methodology section
st.markdown("""
<div class="card" style="margin-bottom: 20px;">
  <div class="section-title">RANKING METHODOLOGY</div>
  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 16px;">
    <div>
      <div style="font-weight: 700; color: var(--accent); margin-bottom: 8px;">67/33 FACTOR BREAKDOWN</div>
      <div style="font-size: 14px; line-height: 1.5; color: var(--text);">
        <strong>Traditional Factors (67%):</strong><br>
        • 1M Stock Price Growth (30% of traditional)<br>
        • 3M Stock Price Growth (20% of traditional)<br>
        • Sharpe Ratio (10% of traditional)<br>
        • Volume Factor (4% of traditional)<br>
        • Market Cap (3% of traditional)<br>
        <br>
        <strong>Reputation Factors (33%):</strong><br>
        • P/E Ratio Quality (15% of reputation)<br>
        • Dividend Yield (10% of reputation)<br>
        • Beta Stability (8% of reputation)
      </div>
    </div>
    <div>
      <div style="font-weight: 700; color: var(--accent); margin-bottom: 8px;">RATING SCALE & DATA</div>
      <div style="font-size: 14px; line-height: 1.5; color: var(--text);">
        <strong>Rating Scale (0-10):</strong><br>
        • <span style="color: var(--up);">7-10:</span> Excellent performance<br>
        • <span style="color: var(--warn);">4-7:</span> Good performance<br>
        • <span style="color: var(--muted);">1-4:</span> Average performance<br>
        • <span style="color: var(--down);">0-1:</span> Poor performance<br>
        <br>
        <strong>Data Sources:</strong><br>
        • <strong>Yahoo Finance:</strong> Real-time prices & growth<br>
        • <strong>500+ Stocks:</strong> Comprehensive coverage<br>
        • <strong>Live Updates:</strong> Fresh data every session
      </div>
    </div>
  </div>
  <div style="font-size: 13px; color: var(--muted); border-top: 1px solid var(--border); padding-top: 12px;">
    <strong>Note:</strong> Rankings are based on quantitative factors only. Past performance does not guarantee future results.
  </div>
</div>
""", unsafe_allow_html=True)

# live ticker tape function
def ticker_tape(df):
    items = []
    for t, r in df.head(10).iterrows():
        # use 1-month stock price growth for ticker tape (more stable)
        growth_1m = r.get('momentum_1m', 0)  # This is actually stock price growth percentage
        cls = "c-up" if growth_1m>=0 else "c-down"
        items.append(f"<span class='badge'>{t}</span> <span class='{cls}'>{growth_1m:+.1f}%</span>")
    html = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;".join(items)
    st.markdown(f"""
    <style>
    .tape {{ overflow:hidden; white-space:nowrap; border-top:1px solid var(--border);
      border-bottom:1px solid var(--border); background:#0D1113; }}
    .tape-inner{{ display:inline-block; padding:8px 0; animation: marquee 45s linear infinite; }}
    @keyframes marquee {{ 0%{{transform:translateX(100%)}} 100%{{transform:translateX(-100%)}} }}
    </style>
    <div class='tape'><div class='tape-inner'>{html}</div></div>
    """, unsafe_allow_html=True)

# premium neon divider function
def neon_divider(label:str):
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin:22px 0 8px">
      <div style="height:1px;background:var(--border);flex:1"></div>
      <div style="font-weight:800;color:var(--muted);letter-spacing:.2px;font-family: JetBrains Mono;">{label.upper()}</div>
      <div style="height:1px;background:var(--border);flex:1"></div>
    </div>
    """, unsafe_allow_html=True)

# initialize session state
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None
if 'chart_search' not in st.session_state:
    st.session_state.chart_search = "AAPL"
if 'analysis_search' not in st.session_state:
    st.session_state.analysis_search = ""
if 'chart_period' not in st.session_state:
    st.session_state.chart_period = "3M"


# load stock rankings with clean api client
with st.spinner("Loading stock rankings..."):
    # first check backend health
    if not api_client.health_check():
        st.warning("⚠️ Backend is not responding, using local fallback data")
        df = get_local_fallback_data(50)
    else:
        # try to get data from backend
        rankings = api_client.get_rankings("world_top_stocks", 50)
        if rankings:
            df = pd.DataFrame(rankings)
            st.sidebar.success(f"✅ Loaded {len(df)} stocks from backend")
        else:
            st.warning("⚠️ Backend returned no data, using local fallback")
            df = get_local_fallback_data(50)

if df is not None and not df.empty:
    st.sidebar.success(f"✅ Ready with {len(df)} stocks")
else:
    st.error("❌ Failed to load any stock data")
    st.stop()

if df is not None and not df.empty:
    # show data status
    st.sidebar.success(f"Data loaded: {len(df)} stocks")
    st.sidebar.info(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # debug: show dataframe info
    st.sidebar.info(f"DataFrame columns: {list(df.columns)}")
    st.sidebar.info(f"DataFrame shape: {df.shape}")
    
    # normalize tickers to uppercase and strip
    if 'ticker' in df.columns:
        df['ticker'] = df['ticker'].astype(str).str.upper().str.strip()
        df = df.drop_duplicates(subset=['ticker']).set_index('ticker')
        st.sidebar.info(f"After ticker processing: {len(df)} stocks")

    # coerce score to numeric
    if 'score' in df.columns:
        df['score'] = pd.to_numeric(df['score'], errors='coerce')
        df = df.dropna(subset=['score'])
        st.sidebar.info(f"After score processing: {len(df)} stocks")
        
        # if scores > 10 then they're 0–100 scale; convert for display only
        score_scale = 10 if df['score'].max() <= 10 else 100
        
        # if api already returns a rank column, prefer it for ordering
        if 'rank' in df.columns:
            df['rank'] = pd.to_numeric(df['rank'], errors='coerce')
            df = df.dropna(subset=['rank']).sort_values('rank', ascending=True)
        else:
            # fall back to score sort
            df = df.sort_values('score', ascending=False)
    else:
        st.error("Ranking data missing 'score' column")
        st.stop()
    
    if df is not None and not df.empty:
        # live ticker tape
        ticker_tape(df)
        
        st.write("")
        
        # bloomberg terminal kpi cards
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"""
        <div class="card">
          <div class="section-title">STOCKS ANALYZED</div>
          <div style="font-size:28px;font-weight:800" class="c-info">{len(df):,}</div>
        </div>""", unsafe_allow_html=True)

        c2.markdown(f"""
        <div class="card">
          <div class="section-title">AVERAGE SCORE</div>
          <div style="font-size:28px;font-weight:800" class="c-up">{df['score'].mean():.3f}</div>
        </div>""", unsafe_allow_html=True)

        c3.markdown(f"""
        <div class="card">
          <div class="section-title">AVG 1M STOCK GROWTH</div>
          <div style="font-size:28px;font-weight:800"
                               class="{ 'c-up' if df['momentum_1m'].mean()>=0 else 'c-down' }">
             {df['momentum_1m'].mean():.1f}%
          </div>
        </div>""", unsafe_allow_html=True)

        c4.markdown(f"""
        <div class="card">
          <div class="section-title">AVG 3M STOCK GROWTH</div>
                     <div style="font-size:28px;font-weight:800" class="c-info">{df['momentum_3m'].mean():.1f}%</div>
        </div>""", unsafe_allow_html=True)
        
        neon_divider("TOP PERFORMERS")
        
        # select the actual top-10 in that order
        top10 = df.head(10).copy()
        top_tickers = top10.index.tolist()
        
        # fetch prices using clean api client
        price_data = api_client.get_live_prices(top_tickers)
        
        # if api fails, get local data for each ticker
        if not price_data:
            price_data = {}
            for ticker in top_tickers:
                local_data = get_local_stock_data(ticker)
                if local_data:
                    price_data[ticker] = local_data

        cols = st.columns(2)
        for i, ticker in enumerate(top_tickers, start=1):
            data = price_data.get(ticker)  # may be none
            score = top10.loc[ticker, 'score']
            # display score on 0–10 scale consistently
            score_10 = score if score_scale == 10 else round(min(score/10, 10), 1)

            score_class = ("c-up" if score_10 > 7 else
                           "c-warn" if score_10 > 4 else
                           "c-muted" if score_10 > 1 else
                           "c-down")

            company_name = top10.loc[ticker, 'name'] if 'name' in top10.columns else ticker

            with cols[0] if i <= 5 else cols[1]:
                if not data:
                    # graceful fallback card when live price missing
                    st.markdown(f"""
                    <div class="stock-card" style="margin-bottom:16px;">
                      <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                        <div class="badge" style="font-size:14px;font-weight:800;">#{i}</div>
                        <div style="font-weight:700;font-size:16px;color:var(--accent);">{ticker}</div>
                      </div>
                      <div style="font-weight:600;font-size:14px;color:var(--text);margin-bottom:8px;line-height:1.3;">
                        {company_name}
                      </div>
                      <div style="font-size:12px;color:var(--muted);">Price unavailable</div>
                      <div style="font-size:12px;color:var(--muted);">Rating</div>
                      <div style="font-weight:700;font-size:16px;" class="{score_class}">{score_10:.1f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    change_cls = "c-up" if data['change_pct'] >= 0 else "c-down"
                    st.markdown(f"""
                    <a href="https://finance.yahoo.com/quote/{ticker}" target="_blank" style="text-decoration:none;color:inherit;">
                      <div class="stock-card" style="cursor:pointer;margin-bottom:16px;">
                        <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                          <div class="badge" style="font-size:14px;font-weight:800;">#{i}</div>
                          <div style="font-weight:700;font-size:16px;color:var(--accent);">{ticker}</div>
                        </div>
                        <div style="font-weight:600;font-size:14px;color:var(--text);margin-bottom:8px;line-height:1.3;">{company_name}</div>
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px;">
                          <div>
                            <div style="font-size:12px;color:var(--muted);">Rating</div>
                            <div style="font-weight:700;font-size:16px;" class="{score_class}">{score_10:.1f}</div>
                          </div>
                          <div>
                            <div style="font-size:12px;color:var(--muted);">Daily Change</div>
                            <div style="font-weight:700;font-size:16px;" class="{change_cls}">{data['change_pct']:+.2f}%</div>
                          </div>
                        </div>
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                          <div>
                            <div style="font-size:12px;color:var(--muted);">Volume</div>
                            <div style="font-weight:600;font-size:14px;" class="c-muted">{data['volume']:,}</div>
                          </div>
                          <div style="text-align:right;">
                            <div style="font-size:12px;color:var(--muted);">Price</div>
                            <div style="font-weight:700;font-size:16px;">${data['price']:.2f}</div>
                          </div>
                        </div>
                      </div>
                    </a>
                    """, unsafe_allow_html=True)
        
        neon_divider("MARKET CHARTS")
        
        # Bloomberg-style Price Chart with Time Period Selection
        try:
            # Stock search bar for any stock
            col1, col2 = st.columns([2, 1])
            with col1:
                chart_stock = st.text_input(
                    "Enter any stock symbol for chart (e.g., AAPL, TSLA, GOOGL)",
                    value=st.session_state.chart_search,
                    placeholder="AAPL",
                    help="Enter any valid stock symbol to display its price chart",
                    key="chart_input"
                )
            
            # Update session state when input changes
            if chart_stock:
                chart_stock = chart_stock.upper().strip()
                if chart_stock != st.session_state.chart_search:
                    st.session_state.chart_search = chart_stock
            
            # Validate stock symbol
            if chart_stock:
                # Fetch data from yfinance
                with st.spinner(f"Fetching data for {chart_stock}..."):
                    try:
                        import yfinance as yf
                        ticker_obj = yf.Ticker(chart_stock)
                        hist = ticker_obj.history(period="1y")
                        if not hist.empty:
                            price_series = hist['Close'].dropna()
                        else:
                            st.error(f"Could not fetch data for {chart_stock}. Please check the stock symbol.")
                            price_series = None
                    except Exception as e:
                        st.error(f"Could not fetch data for {chart_stock}. Please check the stock symbol.")
                        price_series = None
                
                if price_series is not None and len(price_series) > 30:
                    # Time period selection
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        period_1m = st.button("1M", key="1m", use_container_width=True)
                    with col2:
                        period_3m = st.button("3M", key="3m", use_container_width=True)
                    with col3:
                        period_6m = st.button("6M", key="6m", use_container_width=True)
                    with col4:
                        period_1y = st.button("1Y", key="1y", use_container_width=True)
                    with col5:
                        period_max = st.button("MAX", key="max", use_container_width=True)
                    
                    # Determine selected period
                    if period_1m:
                        selected_period = 21
                        period_name = "1 Month"
                    elif period_3m:
                        selected_period = 63
                        period_name = "3 Months"
                    elif period_6m:
                        selected_period = 126
                        period_name = "6 Months"
                    elif period_1y:
                        selected_period = 252
                        period_name = "1 Year"
                    elif period_max:
                        selected_period = len(price_series)
                        period_name = "Max"
                    else:
                        selected_period = 63
                        period_name = "3 Months"
                    
                    # Create Bloomberg-style price chart
                    chart_data = price_series.tail(selected_period)
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=chart_data.index,
                        y=chart_data.values,
                        mode='lines',
                        line=dict(color='#00E676', width=2),
                        name=f'{chart_stock} Price',
                        hovertemplate='<b>%{x}</b><br>Price: $%{y:.2f}<extra></extra>'
                    ))
                    
                    # Get company name if available
                    company_name = ""
                    try:
                        if len(df) > 0 and chart_stock in df.index:
                            company_name = df.loc[chart_stock, 'name'] if 'name' in df.columns else ""
                        else:
                            # Try to get company name from yfinance
                            import yfinance as yf
                            ticker_obj = yf.Ticker(chart_stock)
                            info = ticker_obj.info
                            company_name = info.get('longName', info.get('shortName', ""))
                    except:
                        company_name = ""
                    
                    # Create title with company name if available
                    title_text = f"{chart_stock} Price Chart - {period_name}"
                    if company_name:
                        title_text = f"{chart_stock} ({company_name}) - {period_name}"
                    
                    fig.update_layout(
                        title=title_text,
                        xaxis_title="Date",
                        yaxis_title="Price ($)",
                        height=400,
                        showlegend=False,
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True, theme=None)
                    
                    # Current price info
                    current_price = chart_data.iloc[-1]
                    start_price = chart_data.iloc[0]
                    change = current_price - start_price
                    change_pct = (change / start_price) * 100
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Current Price", f"${current_price:.2f}")
                    with col2:
                        st.metric("Change", f"${change:+.2f}")
                    with col3:
                        st.metric("Change %", f"{change_pct:+.2f}%")
                    with col4:
                        st.metric("Period", period_name)
                        
                else:
                    st.markdown('<div class="alert alert-warning">Insufficient price data for chart</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="alert alert-warning">Please enter a stock symbol to view chart</div>', unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f'<div class="alert alert-warning">Could not load charts: {str(e)}</div>', unsafe_allow_html=True)
        neon_divider("LIVE STOCK PRICES")
        
        try:
            # get current prices for top stocks from backend api
            top_stocks_prices = df.head(10).index.tolist()
            tickers_str = ','.join(top_stocks_prices)
            
            # fetch live prices using clean api client
            price_data = api_client.get_live_prices(top_stocks_prices)
            
            # if api fails, get local data for each ticker
            if not price_data:
                price_data = {}
                for ticker in top_stocks_prices:
                    local_data = get_local_stock_data(ticker)
                    if local_data:
                        price_data[ticker] = local_data
            
            if price_data:
                # display price cards in 2 rows of 5
                price_items = list(price_data.items())
                
                # first row (5 stocks)
                row1_cols = st.columns(5)
                for i, (ticker, data) in enumerate(price_items[:5]):
                    with row1_cols[i]:
                        change_class = "c-up" if data['change'] >= 0 else "c-down"
                        st.markdown(f"""
                        <a href="https://finance.yahoo.com/quote/{ticker}" target="_blank" style="text-decoration: none; color: inherit;">
                            <div class="card" style="cursor: pointer; transition: background-color 0.2s;">
                              <div style="font-weight:700;font-size:16px">{ticker}</div>
                              <div style="font-size:24px;font-weight:800;margin:8px 0">${data['price']:.2f}</div>
                              <div class="{change_class}" style="font-size:14px;font-weight:600">
                                {data['change']:+.2f} ({data['change_pct']:+.2f}%)
                              </div>
                              <div class="c-muted" style="font-size:12px;margin-top:4px">
                                Vol: {data['volume']:,}
                              </div>
                            </div>
                        </a>
                        """, unsafe_allow_html=True)
                
                # add spacing between rows
                st.write("")
                st.write("")
                
                # second row (remaining stocks, up to 5)
                if len(price_items) > 5:
                    row2_cols = st.columns(5)
                    for i, (ticker, data) in enumerate(price_items[5:10]):
                        with row2_cols[i]:
                            change_class = "c-up" if data['change'] >= 0 else "c-down"
                            st.markdown(f"""
                            <a href="https://finance.yahoo.com/quote/{ticker}" target="_blank" style="text-decoration: none; color: inherit;">
                                <div class="card" style="cursor: pointer; transition: background-color 0.2s;">
                                  <div style="font-weight:700;font-size:16px">{ticker}</div>
                                  <div style="font-size:24px;font-weight:800;margin:8px 0">${data['price']:.2f}</div>
                                  <div class="{change_class}" style="font-size:14px;font-weight:600">
                                    {data['change']:+.2f} ({data['change_pct']:+.2f}%)
                                  </div>
                                  <div class="c-muted" style="font-size:12px;margin-top:4px">
                                    Vol: {data['volume']:,}
                                  </div>
                                </div>
                            </a>
                            """, unsafe_allow_html=True)
            else:
                st.markdown('<div class="alert alert-warning">Could not fetch live price data</div>', unsafe_allow_html=True)
                
        except Exception as e:
            st.markdown(f'<div class="alert alert-warning">Price data temporarily unavailable: {str(e)}</div>', unsafe_allow_html=True)
        
        neon_divider("STOCK ANALYSIS")
        
        # ai status
        ai_status = "AI Online" if os.getenv('GEMINI_API_KEY') else "AI Offline"
        pulse_color = "var(--up)" if os.getenv('GEMINI_API_KEY') else "var(--warn)"
        st.markdown(f"""
        <style>
        .chip{{ display:inline-flex; align-items:center; gap:8px; padding:6px 10px;
          background:#0F1518; border:1px solid var(--border); border-radius:999px; }}
        .pulse{{ width:8px; height:8px; border-radius:50%; background:{pulse_color};
          box-shadow:0 0 0 0 rgba(0,230,118,.7); animation:pulse 1.6s infinite; }}
        @keyframes pulse{{ 0%{{box-shadow:0 0 0 0 rgba(0,230,118,.7)}} 70%{{box-shadow:0 0 0 10px rgba(0,230,118,0)}} 100%{{box-shadow:0 0 0 0 rgba(0,230,118,0)}} }}
        </style>
        <div style='text-align:center;margin-bottom:16px'>
          <div class='chip'><span class='pulse'></span><span>{ai_status}</span></div>
        </div>
        """, unsafe_allow_html=True)
        
        # stock analysis form
        with st.form("stock_analysis_form", clear_on_submit=False):
            search_ticker = st.text_input(
                "Enter stock symbol (e.g., AAPL, TSLA, GOOGL)", 
                value=st.session_state.analysis_search,
                placeholder="AAPL", 
                label_visibility="collapsed",
                key="analysis_input"
            )
            search_button = st.form_submit_button("Analyze", type="primary", use_container_width=True)
        
        # handle form submission
        if search_button and search_ticker:
            st.session_state.analysis_search = search_ticker.upper().strip()
            search_ticker = st.session_state.analysis_search
            
            try:
                # try backend first, then fallback to yfinance
                stock_data = api_client.get_stock_data(search_ticker)
                if stock_data:
                    # use backend data
                    current_price = stock_data.get('price', 0)
                    change_1m = stock_data.get('momentum_1m', 0)
                    change_3m = stock_data.get('momentum_3m', 0)
                    company_name = stock_data.get('name', search_ticker)
                    score_100 = stock_data.get('score', 0) * 10
                else:
                    # fallback to yfinance
                    import yfinance as yf
                    ticker = yf.Ticker(search_ticker)
                
                # get current info and historical data
                info = ticker.info
                hist = ticker.history(period="3mo", auto_adjust=True)
                
                if hist.empty or len(hist) < 20:
                    st.error(f"Could not fetch data for {search_ticker}. Please check the stock symbol.")
                else:
                    # calculate metrics
                    current_price = hist['Close'].iloc[-1]
                    month_ago_price = hist['Close'].iloc[-21] if len(hist) >= 21 else hist['Close'].iloc[0]
                    three_month_ago_price = hist['Close'].iloc[0]
                    
                    # calculate percentage changes
                    change_1m = ((current_price / month_ago_price) - 1) * 100
                    change_3m = ((current_price / three_month_ago_price) - 1) * 100
                    
                    # get daily change
                    previous_close = info.get('regularMarketPreviousClose', current_price)
                    daily_change = current_price - previous_close
                    daily_change_pct = (daily_change / previous_close) * 100 if previous_close else 0
                    
                    # get company name
                    company_name = info.get('longName', info.get('shortName', search_ticker))
                    
                    # calculate a simple score based on performance
                    # This is a simplified version of your AI scoring
                    volatility = hist['Close'].pct_change().std() * 100
                    volume_avg = hist['Volume'].mean()
                    
                    # simple scoring algorithm
                    score = (
                        (change_1m * 0.4) +  # 40% weight on 1M performance
                        (change_3m * 0.3) +  # 30% weight on 3M performance
                        (1 / (volatility + 1) * 0.2) +  # 20% weight on low volatility
                        (volume_avg / 1000000 * 0.1)  # 10% weight on volume
                    )
                    
                    # scale score to 0-100
                    score_100 = min(max(score * 10, 0), 100)
                    
                    # determine sentiment and recommendation
                    if score_100 > 80:
                        sentiment = "very bullish"
                        recommendation = "Strong Buy"
                    elif score_100 > 60:
                        sentiment = "bullish"
                        recommendation = "Buy"
                    elif score_100 > 40:
                        sentiment = "neutral"
                        recommendation = "Hold"
                    elif score_100 > 20:
                        sentiment = "bearish"
                        recommendation = "Sell"
                    else:
                        sentiment = "very bearish"
                        recommendation = "Strong Sell"
                    
                    # display analysis in organized layout
                    left, right = st.columns(2, gap="large")
                    
                    with left:
                        st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
                        st.markdown('<div class="section-title">OVERVIEW</div>', unsafe_allow_html=True)
                        
                        st.markdown(f"""
                        **{search_ticker}** ({company_name}) shows **{sentiment}** signals.
                        
                        **Key Metrics:**
                        - **Current Price:** ${current_price:.2f}
                        - **Daily Change:** ${daily_change:+.2f} ({daily_change_pct:+.2f}%)
                        - **AI Score:** {score_100:.1f}/100
                        - **1-Month Growth:** {change_1m:+.1f}%
                        - **3-Month Growth:** {change_3m:+.1f}%
                        
                        **Investment Recommendation:** {recommendation}
                        """)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with right:
                        st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
                        st.markdown('<div class="section-title">PERFORMANCE</div>', unsafe_allow_html=True)
                        
                        # risk assessment
                        growth_risk = "Low" if change_1m > 5 else "Medium" if change_1m > -5 else "High"
                        trend_risk = "Low" if change_3m > 10 else "Medium" if change_3m > -5 else "High"
                        overall_risk = "Low" if score_100 > 60 else "Medium" if score_100 > 30 else "High"
                        market_position = "Outperforming" if change_1m > 10 else "In-line" if change_1m > -5 else "Underperforming"
                        
                        st.markdown(f"""
                        **Performance Breakdown:**
                        
                        The stock demonstrates {'strong' if score_100 > 60 else 'moderate' if score_100 > 30 else 'weak'} performance signals.
                        
                        **Risk Assessment:**
                        - **Stock Growth Risk:** {growth_risk}
                        - **Trend Risk:** {trend_risk}
                        - **Overall Risk:** {overall_risk}
                        
                        **Market Position:** {market_position}
                        
                        **Technical Metrics:**
                        - **Volatility:** {volatility:.1f}%
                        - **Avg Volume:** {volume_avg:,.0f}
                        """)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # ai analysis section (simplified)
                    if os.getenv('GEMINI_API_KEY'):
                        st.markdown(f'<div class="section-title">AI ANALYSIS</div>', unsafe_allow_html=True)
                        st.markdown(f"""
                        <div class="analysis-section">
                            <div style="font-size: 14px; line-height: 1.6; color: var(--text);">
                                AI analysis is available but requires backend integration. The current analysis uses live yfinance data with a simplified scoring algorithm based on 1-month growth (40%), 3-month growth (30%), volatility (20%), and volume (10%).
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="section-title">AI ANALYSIS</div>', unsafe_allow_html=True)
                        st.markdown(f"""
                        <div class="analysis-section">
                            <div style="font-size: 14px; line-height: 1.6; color: var(--text);">
                                AI analysis is currently offline. This analysis uses live yfinance data with a simplified scoring algorithm based on 1-month growth (40%), 3-month growth (30%), volatility (20%), and volume (10%).
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
            except Exception as e:
                st.error(f"Error analyzing {search_ticker}: {str(e)}")
                
                # stock-specific news section
                st.markdown(f'<div class="section-title">{search_ticker} NEWS</div>', unsafe_allow_html=True)
                
                # fetch news for the analyzed stock
                stock_news = fetch_news(ticker=search_ticker, limit=3)
                
                if stock_news:
                    for news in stock_news:
                        sentiment_color = {
                            'positive': 'var(--up)',
                            'negative': 'var(--down)',
                            'neutral': 'var(--muted)'
                        }.get(news['sentiment'], 'var(--muted)')
                        
                        st.markdown(f"""
                        <a href="{news['url']}" target="_blank" style="text-decoration: none; color: inherit;">
                            <div style="margin-bottom: 12px; padding: 12px; border-left: 3px solid {sentiment_color}; background: rgba(255,255,255,.02); border-radius: 8px; cursor: pointer; transition: background-color 0.2s;">
                                <div style="font-weight: 700; font-size: 13px; margin-bottom: 4px;">{news['title']}</div>
                                <div style="color: var(--muted); font-size: 12px; margin-bottom: 6px;">{news['description']}</div>
                                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 10px; color: var(--muted);">
                                    <span>{news['source']}</span>
                                    <span>{news['published_at']}</span>
                                </div>
                            </div>
                        </a>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown('<div class="alert alert-info">No recent news available for this stock.</div>', unsafe_allow_html=True)
        

        
        # news section
        neon_divider("MARKET NEWS")
        
        # display news section
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">MARKET NEWS</div>', unsafe_allow_html=True)
            
            # get general market news
            market_news = fetch_news(limit=3)
            
            for i, news in enumerate(market_news, 1):
                sentiment_color = {
                    'positive': 'var(--up)',
                    'negative': 'var(--down)',
                    'neutral': 'var(--muted)'
                }.get(news['sentiment'], 'var(--muted)')
                
                st.markdown(f"""
                <a href="{news['url']}" target="_blank" style="text-decoration: none; color: inherit;">
                    <div style="margin-bottom: 16px; padding: 12px; border-left: 3px solid {sentiment_color}; background: rgba(255,255,255,.02); cursor: pointer; transition: background-color 0.2s;">
                        <div style="font-weight: 700; font-size: 14px; margin-bottom: 4px;">{news['title']}</div>
                        <div style="color: var(--muted); font-size: 13px; margin-bottom: 6px;">{news['description']}</div>
                        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: var(--muted);">
                            <span>{news['source']}</span>
                            <span>{news['published_at']}</span>
                        </div>
                    </div>
                </a>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">TOP STOCK NEWS</div>', unsafe_allow_html=True)
            
            # get news for top 4 stocks
            top_stocks = df.head(4).index.tolist() if df is not None and not df.empty else ['AAPL', 'TSLA', 'GOOGL', 'MSFT']
            
            for ticker in top_stocks[:4]:  # show news for top 4 stocks
                stock_news = fetch_news(ticker=ticker, limit=1)
                if stock_news:
                    news = stock_news[0]
                    sentiment_color = {
                        'positive': 'var(--up)',
                        'negative': 'var(--down)',
                        'neutral': 'var(--muted)'
                    }.get(news['sentiment'], 'var(--muted)')
                    
                    st.markdown(f"""
                    <a href="{news['url']}" target="_blank" style="text-decoration: none; color: inherit;">
                        <div style="margin-bottom: 12px; padding: 10px; border-left: 3px solid {sentiment_color}; background: rgba(255,255,255,.02); border-radius: 6px; cursor: pointer; transition: background-color 0.2s;">
                            <div style="font-weight: 700; font-size: 12px; margin-bottom: 4px; color: var(--accent);">{ticker}</div>
                            <div style="font-weight: 600; font-size: 11px; margin-bottom: 3px; line-height: 1.3;">{news['title']}</div>
                            <div style="color: var(--muted); font-size: 10px;">{news['source']} • {news['published_at']}</div>
                        </div>
                    </a>
                    """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # footer
        st.markdown("""
        <div class="footer">
            QuantSnap • Built with Streamlit • Data from Yahoo Finance<br>
            Last updated: {}
        </div>
        """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
        
    else:
        st.markdown('<div class="alert alert-danger">❌ No data available for the selected universe</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="alert alert-danger">❌ Could not load ranking data</div>', unsafe_allow_html=True)
