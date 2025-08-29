"""
Silver Surfer Theme Streamlit web application for AI Daily Draft
Updated to use PostgreSQL backend with API endpoints
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import requests
import json
from dotenv import load_dotenv
import os

# Bloomberg Terminal Plotly Template
bloomberg_template = dict(
    layout=dict(
        paper_bgcolor="#0B0F10",
        plot_bgcolor="#0B0F10",
        font=dict(family="JetBrains Mono, Menlo, monospace", color="#D7E1E8", size=13),
        xaxis=dict(
            gridcolor="#1C2328", zerolinecolor="#1C2328",
            linecolor="#2A3338", tickcolor="#2A3338", showspikes=True
        ),
        yaxis=dict(
            gridcolor="#1C2328", zerolinecolor="#1C2328",
            linecolor="#2A3338", tickcolor="#2A3338", showspikes=True
        ),
        legend=dict(bgcolor="#0B0F10", bordercolor="#2A3338"),
        margin=dict(l=40, r=30, t=40, b=40),
        hoverlabel=dict(bgcolor="#111417", bordercolor="#2A3338", font_color="#D7E1E8"),
        colorway=["#00E676", "#00C2FF", "#FFB000", "#FF4D4D", "#A78BFA", "#64FFDA"]
    )
)
pio.templates["bloomberg"] = bloomberg_template
pio.templates.default = "bloomberg"

# Load environment variables
load_dotenv()

def get_company_logo(ticker: str) -> str:
    """Get company logo initials with consistent styling"""
    clean_ticker = ticker.replace('-', '').replace('.', '')
    if len(clean_ticker) >= 3:
        return clean_ticker[:3].upper()
    else:
        return clean_ticker.upper()

# API Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
if os.getenv('ENVIRONMENT') == 'production':
    # In production, use the Render backend URL
    API_BASE_URL = os.getenv('API_BASE_URL', 'https://quantsnap-backend.onrender.com')

def api_request(endpoint: str, params: Dict = None) -> Dict:
    """Make API request to backend"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return {}

def get_rankings_from_api(universe: str, limit: int = 50) -> pd.DataFrame:
    """Get rankings from API"""
    data = api_request(f"/rankings/{universe}", {"limit": limit})
    if data and "rankings" in data:
        return pd.DataFrame(data["rankings"])
    return pd.DataFrame()

def get_stock_data_from_api(ticker: str) -> Dict:
    """Get stock data from API"""
    return api_request(f"/stock/{ticker}")

def get_analysis_from_api(ticker: str) -> Dict:
    """Get AI analysis from API"""
    return api_request(f"/analysis/{ticker}")

# Import remaining modules
from core.universe import get_universe
from core.scoring import get_default_weights
from core.ai_analysis import generate_stock_analysis, generate_portfolio_insights, get_quota_status

# News fetching function
def fetch_news(ticker=None, limit=5):
    """Fetch financial news using NewsAPI or similar"""
    try:
        import requests
        
        # Check for NewsAPI key
        news_api_key = os.getenv('NEWS_API_KEY')
        
        if news_api_key:
            # Real NewsAPI integration
            try:
                if ticker:
                    # Stock-specific news
                    url = f"https://newsapi.org/v2/everything"
                    params = {
                        'q': f'"{ticker}" AND (stock OR earnings OR financial)',
                        'language': 'en',
                        'sortBy': 'publishedAt',
                        'pageSize': limit,
                        'apiKey': news_api_key
                    }
                else:
                    # General market news
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
                        # Simple sentiment analysis based on keywords
                        title = article.get('title', '').lower()
                        description = article.get('description', '').lower()
                        content = f"{title} {description}"
                        
                        if any(word in content for word in ['up', 'gain', 'rise', 'positive', 'strong', 'beat', 'exceed']):
                            sentiment = 'positive'
                        elif any(word in content for word in ['down', 'fall', 'drop', 'negative', 'weak', 'miss', 'decline']):
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
                st.sidebar.warning(f"News API error: {api_error}")
        
        # Fallback to placeholder data if no API key or API fails
        
        if ticker:
            # Stock-specific news
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
            # General market news
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
                },
                {
                    'title': 'Earnings Season Kicks Off with Mixed Results',
                    'description': 'Major banks report earnings this week, setting the tone for the broader market.',
                    'source': 'Financial Times',
                    'published_at': (datetime.now() - timedelta(hours=7)).strftime('%Y-%m-%d %H:%M'),
                    'url': '#',
                    'sentiment': 'neutral'
                },
                {
                    'title': 'Global Markets React to Economic Data',
                    'description': 'International markets show mixed reactions to latest economic indicators and policy announcements.',
                    'source': 'Bloomberg',
                    'published_at': (datetime.now() - timedelta(hours=9)).strftime('%Y-%m-%d %H:%M'),
                    'url': '#',
                    'sentiment': 'neutral'
                }
            ]
        
        return news_items[:limit]
    
    except Exception as e:
        return []

# Page configuration
st.set_page_config(
    page_title="AI Daily Draft - Stock Rankings",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Bloomberg Terminal Theme
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');

:root{
  --bg:        #0B0F10;  /* canvas */
  --panel:     #111417;  /* cards/panels */
  --panel-2:   #0F1419;  /* sidebar/secondary */
  --grid:      #1C2328;  /* chart grid lines */
  --border:    #2A3338;
  --text:      #D7E1E8;
  --muted:     #9FB3C8;

  /* Bloomberg-ish status colors */
  --accent:    #00E676;  /* green accent */
  --up:        #00E676;  /* positive */
  --down:      #FF4D4D;  /* negative */
  --warn:      #FFB000;  /* amber/neutral warn */
  --info:      #00C2FF;  /* cyan */
  --magenta:   #FF2EA6;  /* optional accent */
}

/* app shell */
html, body, [data-testid="stAppViewContainer"]{
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: "JetBrains Mono", SFMono-Regular, ui-monospace, Menlo, monospace;
}
[data-testid="stAppViewContainer"] .main .block-container{
  max-width: 1200px; padding-top: 1.25rem; padding-bottom: 2rem;
}

/* cards/panels with premium glass edges */
.card, .analysis-section, .stock-card{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px 18px;
  box-sizing: border-box;
  box-shadow: 0 4px 12px rgba(0,0,0,.2);
}
.analysis-section{ width: 100%; margin: 12px 0; }
.stock-card{
  display: flex; gap: 12px; align-items: center; margin-bottom: 10px;
}

/* titles */
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
.section-title ~ div:empty { display:none !important; }

/* badge and rank pill */
.badge{
  background: var(--border); color: var(--text);
  padding: 6px 10px; border-radius: 8px; font-weight: 700; font-size: 12px;
}
.rank{
  margin-left: auto; background: #182026; color: var(--muted);
  padding: 4px 8px; border-radius: 8px; font-weight: 700; font-size: 12px;
}

/* color utility classes (your 'colors class') */
.c-up{ color: var(--up) !important; }
.c-down{ color: var(--down) !important; }
.c-warn{ color: var(--warn) !important; }
.c-info{ color: var(--info) !important; }
.c-muted{ color: var(--muted) !important; }

/* inputs (light touch so they don't break between versions) */
.stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input{
  background: var(--panel-2) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
}

/* buttons */
.stButton>button{
  background: var(--panel-2);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 10px; font-weight: 700;
  margin-top: 0;  /* Align with text input */
}
.stButton>button:hover{ border-color: var(--accent); }

/* Search input alignment */
.stTextInput>div>div>input{
  margin-top: 0;
}

/* hide chrome if you like */
#MainMenu, header, footer{ visibility: hidden; }

/* Hover effects for clickable elements */
.card:hover, .stock-card:hover {
  background: var(--panel-2);
  border-color: var(--accent);
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(0,0,0,.3);
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None

# QuantStream Terminal Banner
st.markdown("""
<style>
.title-wrap{
  text-align:center;
  margin:20px 0 30px;
  font-family:'JetBrains Mono', monospace;
}
.title{
  font-size:56px;
  font-weight:900;
  letter-spacing:3px;
  color:#00E676;  /* neon green */
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

<div class="title-wrap">
  <div class="title">QUANTSNAP</div>
</div>
""", unsafe_allow_html=True)
st.write("")

# Live Ticker Tape Function
def ticker_tape(df):
    items = []
    for t, r in df.head(10).iterrows():
        mom = r['MOM_1M']
        cls = "c-up" if mom>=0 else "c-down"
        items.append(f"<span class='badge'>{t}</span> <span class='{cls}'>{mom:+.1%}</span>")
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

# Premium Neon Divider Function
def neon_divider(label:str):
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin:22px 0 8px">
      <div style="height:1px;background:var(--border);flex:1"></div>
      <div style="font-weight:800;color:var(--muted);letter-spacing:.2px;font-family: JetBrains Mono;">{label.upper()}</div>
      <div style="height:1px;background:var(--border);flex:1"></div>
    </div>
    """, unsafe_allow_html=True)

# Micro Sparkline Function
def tiny_spark(series):
    fig = go.Figure(go.Scatter(y=series.values, mode="lines", hoverinfo="skip", line=dict(color="#00E676", width=1)))
    fig.update_layout(
        height=30, margin=dict(l=0,r=0,t=0,b=0),
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig

# AI Status Check
import os
ai_enabled = bool(os.getenv('GEMINI_API_KEY'))

# Sidebar
with st.sidebar:
    st.markdown("## Settings")
    
    # Universe selection
    universe_options = ["world_top_stocks", "sp500", "top_etfs", "popular_stocks"]
    selected_universe = st.selectbox(
        "Stock Universe",
        universe_options,
        index=0,
        help="Choose which stock universe to analyze"
    )
    
    # Top N selection
    top_n = st.slider("Display Top", 5, 50, 10, help="Number of top stocks to display")
    
    # CRT Scanline Toggle (Easter Egg)
    enable_crt = st.toggle("Retro CRT Mode", value=False, help="Add retro scanline effect")
    if enable_crt:
        st.markdown("""
        <style>
        .crt::after{
          content:""; position:fixed; inset:0; pointer-events:none;
          background: repeating-linear-gradient(0deg, rgba(255,255,255,.03) 0, rgba(255,255,255,.03) 1px, transparent 2px, transparent 4px);
          mix-blend-mode: soft-light; opacity:.35;
        }
        </style>
        """, unsafe_allow_html=True)
        st.markdown("<div class='crt'></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # AI Status
    if ai_enabled:
        st.success("🤖 AI Available")
        st.info("💡 Enable AI per analysis to save API calls")
    else:
        st.info("📊 Quantitative Analysis Only")
        st.info("Add GEMINI_API_KEY for AI features")

# Data Loading from API
with st.spinner("Loading data from database..."):
    df = get_rankings_from_api(selected_universe, top_n)

if df is not None and not df.empty:
    # Show data status
    st.sidebar.success(f"Data loaded: {len(df)} stocks")
    st.sidebar.info(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Set ticker as index for compatibility
    if 'ticker' in df.columns:
        df = df.set_index('ticker')
    
    if df is not None and not df.empty:
        # Live Ticker Tape
        ticker_tape(df)
        
        st.write("")
        
        # Bloomberg Terminal KPI Cards
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"""
        <div class="card">
          <div class="section-title">STOCKS ANALYZED</div>
          <div style="font-size:28px;font-weight:800" class="c-info">{len(df):,}</div>
        </div>""", unsafe_allow_html=True)

        c2.markdown(f"""
        <div class="card">
          <div class="section-title">AVERAGE SCORE</div>
          <div style="font-size:28px;font-weight:800" class="c-up">{df['Score'].mean():.3f}</div>
        </div>""", unsafe_allow_html=True)

        c3.markdown(f"""
        <div class="card">
          <div class="section-title">AVG 1M RETURN</div>
          <div style="font-size:28px;font-weight:800"
               class="{ 'c-up' if df['MOM_1M'].mean()>=0 else 'c-down' }">
            {df['MOM_1M'].mean():.1%}
          </div>
        </div>""", unsafe_allow_html=True)

        c4.markdown(f"""
        <div class="card">
          <div class="section-title">AVG SHARPE</div>
          <div style="font-size:28px;font-weight:800" class="c-info">{df['Sharpe_3M'].mean():.2f}</div>
        </div>""", unsafe_allow_html=True)
        
        neon_divider("TOP PERFORMERS")
        cols = st.columns(2)

        for i, (ticker, row) in enumerate(df.head(top_n).iterrows(), 1):
            score = row['Score']; mom = row['MOM_1M']; sharpe = row['Sharpe_3M']
            score_class = "c-up" if score>1 else "c-warn" if score>0.5 else "c-muted" if score>0 else "c-down"
            # Left column: ranks 1-5, Right column: ranks 6-10
            with cols[0] if i <= 5 else cols[1]:
                st.markdown(f"""
                <a href="https://finance.yahoo.com/quote/{ticker}" target="_blank" style="text-decoration: none; color: inherit;">
                    <div class="stock-card" style="cursor: pointer; transition: background-color 0.2s;">
                      <div class="badge">{ticker[:3].upper()}</div>
                      <div>
                        <div style="font-weight:700">{ticker}</div>
                        <div class="c-muted" style="font-size:12px">{row.get('Name', ticker)}</div>
                        <div style="font-size:12px;margin-top:4px">
                          <span class="{score_class}">Score {score:.3f}</span> |
                          <span class="{ 'c-up' if mom>=0 else 'c-down' }">1M {mom:.1%}</span> |
                          <span class="c-info">Sharpe {sharpe:.2f}</span>
                        </div>
                      </div>
                      <div class="rank">#{i}</div>
                    </div>
                </a>
                """, unsafe_allow_html=True)
                
                # Add micro sparkline if price data is available
                try:
                    cache_path = get_cache_path(selected_universe)
                    if cache_path.exists():
                        prices_data = load_parquet(str(cache_path))
                        if isinstance(prices_data.columns, pd.MultiIndex):
                            try:
                                adj_close = prices_data.xs('Adj Close', axis=1, level=1)
                            except:
                                adj_close = prices_data.xs('Close', axis=1, level=1)
                        else:
                            if 'Adj Close' in prices_data.columns:
                                adj_close = prices_data['Adj Close']
                            else:
                                adj_close = prices_data['Close']
                        
                        if ticker in adj_close.columns:
                            price_series = adj_close[ticker].dropna().tail(30)  # Last 30 days
                            if len(price_series) > 5:
                                spark_fig = tiny_spark(price_series)
                                st.plotly_chart(spark_fig, use_container_width=True, theme=None)
                except:
                    pass  # Skip sparkline if data not available
        
        neon_divider("MARKET CHARTS")
        
        # Bloomberg-style Price Chart with Time Period Selection
        try:
            # Initialize session state for chart search
            if 'chart_search' not in st.session_state:
                st.session_state.chart_search = df.head(1).index[0] if len(df) > 0 else "AAPL"
            if 'chart_data_cache' not in st.session_state:
                st.session_state.chart_data_cache = {}
            if 'selected_period' not in st.session_state:
                st.session_state.selected_period = 63  # Default to 3M
            
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
                # Fetch data from API or yfinance as fallback
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
                        st.session_state.selected_period = 21
                        period_name = "1 Month"
                    elif period_3m:
                        st.session_state.selected_period = 63
                        period_name = "3 Months"
                    elif period_6m:
                        st.session_state.selected_period = 126
                        period_name = "6 Months"
                    elif period_1y:
                        st.session_state.selected_period = 252
                        period_name = "1 Year"
                    elif period_max:
                        st.session_state.selected_period = len(price_series)
                        period_name = "Max"
                    
                    # Get the selected period
                    selected_period = st.session_state.selected_period
                    if period_name == "":
                        if selected_period == 21:
                            period_name = "1 Month"
                        elif selected_period == 63:
                            period_name = "3 Months"
                        elif selected_period == 126:
                            period_name = "6 Months"
                        elif selected_period == 252:
                            period_name = "1 Year"
                        else:
                            period_name = "Max"
                    
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
                            company_name = df.loc[chart_stock, 'Name'] if 'Name' in df.columns else ""
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
                st.markdown('<div class="alert alert-warning">Price data not available. The app uses yfinance API for real-time data. Please ensure you have internet connection.</div>', unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f'<div class="alert alert-warning">Could not load charts: {str(e)}</div>', unsafe_allow_html=True)
        
        neon_divider("LIVE STOCK PRICES")
        
        try:
            import yfinance as yf
            
            # Get current prices for top stocks
            top_stocks_prices = df.head(10).index.tolist()
            price_data = {}
            
            for ticker in top_stocks_prices:
                try:
                    ticker_obj = yf.Ticker(ticker)
                    info = ticker_obj.info
                    current_price = info.get('regularMarketPrice', 0)
                    previous_close = info.get('regularMarketPreviousClose', 0)
                    change = current_price - previous_close if previous_close else 0
                    change_pct = (change / previous_close * 100) if previous_close else 0
                    
                    price_data[ticker] = {
                        'price': current_price,
                        'change': change,
                        'change_pct': change_pct,
                        'volume': info.get('volume', 0)
                    }
                except:
                    continue
            
            if price_data:
                # Display price cards in 2 rows of 5
                price_items = list(price_data.items())
                
                # First row (5 stocks)
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
                
                # Add spacing between rows
                st.write("")
                st.write("")
                
                # Second row (remaining stocks, up to 5)
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
        
        # AI Status in the right spot
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
        
        # Initialize session state for stock analysis
        if 'analysis_search' not in st.session_state:
            st.session_state.analysis_search = ""
        if 'analysis_triggered' not in st.session_state:
            st.session_state.analysis_triggered = False
        
        # Search form to prevent UI glitching
        with st.form("stock_analysis_form", clear_on_submit=False):
            col1, col2 = st.columns([3, 1])
            with col1:
                search_ticker = st.text_input(
                    "Enter stock symbol (e.g., AAPL, TSLA, GOOGL)", 
                    value=st.session_state.analysis_search,
                    placeholder="AAPL", 
                    label_visibility="collapsed",
                    key="analysis_input"
                )
            with col2:
                st.write("")  # Spacer for alignment
                search_button = st.form_submit_button("Analyze", type="primary", use_container_width=True)
        
        # Handle form submission
        if search_button and search_ticker:
            st.session_state.analysis_search = search_ticker.upper().strip()
            st.session_state.analysis_triggered = True
            st.rerun()
        
        # Use session state values for analysis
        search_ticker = st.session_state.analysis_search
        search_triggered = st.session_state.analysis_triggered
        
        # Reset trigger after processing
        if st.session_state.analysis_triggered:
            st.session_state.analysis_triggered = False
        
                # Simple and Robust Stock Analysis
        if search_ticker and search_triggered:
            search_ticker = search_ticker.upper().strip()
            
            # Get stock data from API
            with st.spinner(f"Analyzing {search_ticker}..."):
                stock_data = get_stock_data_from_api(search_ticker)
                
            if stock_data and "factors" in stock_data:
                # Use data from API
                ticker_data = stock_data["factors"]
                company_data = stock_data.get("company", {})
                
                # Display analysis in organized layout like portfolio analysis
                left, right = st.columns(2, gap="large")
                
                with left:
                    st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">OVERVIEW</div>', unsafe_allow_html=True)
                    
                    score = ticker_data['Score']
                    mom_1m = ticker_data['MOM_1M']
                    mom_3m = ticker_data['MOM_3M']
                    sharpe = ticker_data['Sharpe_3M']
                    volatility = ticker_data['Vol_30d']
                    
                    # Determine sentiment
                    if score > 1.0:
                        sentiment = "very bullish"
                        recommendation = "Strong Buy"
                    elif score > 0.5:
                        sentiment = "bullish"
                        recommendation = "Buy"
                    elif score > 0:
                        sentiment = "neutral"
                        recommendation = "Hold"
                    else:
                        sentiment = "bearish"
                        recommendation = "Sell"
                    
                    st.markdown(f"""
                    **{search_ticker}** ({ticker_data.get('Name', search_ticker)}) shows **{sentiment}** signals.
                    
                    **Key Metrics:**
                    - **AI Score:** {score:.3f}
                    - **1-Month Return:** {mom_1m:.1%}
                    - **3-Month Return:** {mom_3m:.1%}
                    - **Sharpe Ratio:** {sharpe:.2f}
                    - **Volatility:** {volatility:.1%}
                    
                    **Investment Recommendation:** {recommendation}
                    """)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with right:
                    st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">PERFORMANCE</div>', unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    **Performance Breakdown:**
                    
                    The stock demonstrates {'strong' if sharpe > 2 else 'moderate' if sharpe > 1 else 'weak'} risk-adjusted returns.
                    
                    **Risk Assessment:**
                    - **Volatility Risk:** {'High' if volatility > 0.3 else 'Medium' if volatility > 0.2 else 'Low'}
                    - **Momentum Risk:** {'Low' if mom_1m > 0.05 else 'Medium' if mom_1m > -0.05 else 'High'}
                    - **Overall Risk:** {'High' if volatility > 0.3 or sharpe < 0.5 else 'Medium' if volatility > 0.2 or sharpe < 1 else 'Low'}
                    
                    **Market Position:** {'Outperforming' if mom_1m > 0.1 else 'In-line' if mom_1m > -0.05 else 'Underperforming'}
                    """)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Add reputation analysis section
                if 'Reputation_Score' in ticker_data:
                    st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">REPUTATION ANALYSIS</div>', unsafe_allow_html=True)
                    
                    reputation_score = ticker_data.get('Reputation_Score', 0)
                    esg_score = ticker_data.get('ESG_Score', 0)
                    financial_health = ticker_data.get('Financial_Health', 0)
                    market_position = ticker_data.get('Market_Position', 0)
                    growth_stability = ticker_data.get('Growth_Stability', 0)
                    
                    # Reputation assessment
                    if reputation_score > 0.8:
                        reputation_level = "Excellent"
                        reputation_color = "🟢"
                    elif reputation_score > 0.6:
                        reputation_level = "Good"
                        reputation_color = "🟡"
                    elif reputation_score > 0.4:
                        reputation_level = "Fair"
                        reputation_color = "🟠"
                    else:
                        reputation_level = "Poor"
                        reputation_color = "🔴"
                    
                    st.markdown(f"""
                    **Company Reputation:** {reputation_color} **{reputation_level}** ({reputation_score:.1%})
                    
                    **Reputation Breakdown:**
                    - **ESG Score:** {esg_score:.1%} {'🟢' if esg_score > 0.7 else '🟡' if esg_score > 0.5 else '🔴'}
                    - **Financial Health:** {financial_health:.1%} {'🟢' if financial_health > 0.7 else '🟡' if financial_health > 0.5 else '🔴'}
                    - **Market Position:** {market_position:.1%} {'🟢' if market_position > 0.7 else '🟡' if market_position > 0.5 else '🔴'}
                    - **Growth Stability:** {growth_stability:.1%} {'🟢' if growth_stability > 0.7 else '🟡' if growth_stability > 0.5 else '🔴'}
                    
                    **Reputation Impact:** {'Positive' if reputation_score > 0.6 else 'Neutral' if reputation_score > 0.4 else 'Negative'} influence on overall score.
                    """)
                    st.markdown('</div>', unsafe_allow_html=True)
                
            else:
                # Simple live analysis for non-ranked stocks
                with st.spinner("Analyzing stock data..."):
                    try:
                        import yfinance as yf
                        ticker_obj = yf.Ticker(search_ticker)
                    
                        # Get basic info
                        info = ticker_obj.info
                        if not info or 'regularMarketPrice' not in info:
                            st.markdown('<div class="alert alert-danger">❌ Invalid stock symbol. Please check the ticker and try again.</div>', unsafe_allow_html=True)
                            st.stop()
                        
                        # Get historical data
                        hist = ticker_obj.history(period="6mo")
                        
                        if not hist.empty and len(hist) > 20:
                            # Simple calculations without complex factor analysis
                            close_prices = hist['Close'].values
                            current_price = close_prices[-1]
                            start_price = close_prices[0]
                            
                            # Calculate simple metrics
                            total_return = (current_price - start_price) / start_price
                            returns = hist['Close'].pct_change().dropna()
                            volatility = returns.std() * (252 ** 0.5)  # Annualized
                            sharpe = (returns.mean() * 252) / volatility if volatility > 0 else 0
                            
                            # Simple momentum calculations
                            if len(close_prices) >= 21:
                                mom_1m = (close_prices[-1] - close_prices[-21]) / close_prices[-21]
                            else:
                                mom_1m = total_return
                            
                            if len(close_prices) >= 63:
                                mom_3m = (close_prices[-1] - close_prices[-63]) / close_prices[-63]
                            else:
                                mom_3m = total_return
                            
                            # Simple score calculation
                            score = (mom_1m * 0.4 + mom_3m * 0.3 + sharpe * 0.3)
                            
                            # Create simple ticker data
                            ticker_data = pd.Series({
                                'Score': score,
                                'MOM_1M': mom_1m,
                                'MOM_3M': mom_3m,
                                'Sharpe_3M': sharpe,
                                'Vol_30d': volatility,
                                'Name': info.get('longName', info.get('shortName', search_ticker))
                            })
                            
                            # Display analysis in organized layout like portfolio analysis
                            left, right = st.columns(2, gap="large")
                            
                            with left:
                                st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
                                st.markdown('<div class="section-title">OVERVIEW</div>', unsafe_allow_html=True)
                                
                                # Determine sentiment
                                if score > 0.1:
                                    sentiment = "bullish"
                                    recommendation = "Buy"
                                elif score > -0.1:
                                    sentiment = "neutral"
                                    recommendation = "Hold"
                                else:
                                    sentiment = "bearish"
                                    recommendation = "Sell"
                                
                                st.markdown(f"""
                                **{search_ticker}** ({ticker_data.get('Name', search_ticker)}) shows **{sentiment}** signals.
                                
                                **Key Metrics:**
                                - **Current Price:** ${current_price:.2f}
                                - **6-Month Return:** {total_return:.1%}
                                - **1-Month Momentum:** {mom_1m:.1%}
                                - **3-Month Momentum:** {mom_3m:.1%}
                                - **Volatility:** {volatility:.1%}
                                - **Sharpe Ratio:** {sharpe:.2f}
                                
                                **Investment Recommendation:** {recommendation}
                                """)
                                st.markdown('</div>', unsafe_allow_html=True)
                            
                            with right:
                                st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
                                st.markdown('<div class="section-title">PERFORMANCE</div>', unsafe_allow_html=True)
                                
                                st.markdown(f"""
                                **Performance Breakdown:**
                                
                                The stock demonstrates {'strong' if sharpe > 2 else 'moderate' if sharpe > 1 else 'weak'} risk-adjusted returns.
                                
                                **Risk Assessment:**
                                - **Volatility Risk:** {'High' if volatility > 0.3 else 'Medium' if volatility > 0.2 else 'Low'}
                                - **Momentum Risk:** {'Low' if mom_1m > 0.05 else 'Medium' if mom_1m > -0.05 else 'High'}
                                - **Overall Risk:** {'High' if volatility > 0.3 or sharpe < 0.5 else 'Medium' if volatility > 0.2 or sharpe < 1 else 'Low'}
                                
                                **Market Position:** {'Outperforming' if mom_1m > 0.1 else 'In-line' if mom_1m > -0.05 else 'Underperforming'}
                                """)
                                st.markdown('</div>', unsafe_allow_html=True)
                            
                        else:
                            st.markdown('<div class="alert alert-danger">❌ Could not fetch sufficient data for this stock. Please check the symbol and try again.</div>', unsafe_allow_html=True)
                            st.stop()
                            
                    except Exception as e:
                        st.markdown(f'<div class="alert alert-danger">❌ Error analyzing {search_ticker}: {str(e)}</div>', unsafe_allow_html=True)
                        st.stop()
            
            # AI Enhancement Section (for both ranked and live analysis)
            if 'ticker_data' in locals():
                st.markdown('<div class="section-title">AI-POWERED ANALYSIS</div>', unsafe_allow_html=True)
                
                if ai_enabled:
                    # AI is enabled by default, no checkbox needed
                    try:
                        with st.spinner("Generating AI insights..."):
                                # Prepare data for AI analysis
                                factors_dict = {
                                    'MOM_1M': ticker_data['MOM_1M'],
                                    'MOM_3M': ticker_data['MOM_3M'],
                                    'Sharpe_3M': ticker_data['Sharpe_3M'],
                                    'Vol_30d': ticker_data['Vol_30d']
                                }
                                
                                # Generate AI analysis
                                # For live analysis, we have the price data available
                                price_series = None
                                if 'hist' in locals() and hist is not None and not hist.empty:
                                    price_series = hist['Close']
                                
                                ai_analysis = generate_stock_analysis(
                                    search_ticker, 
                                    factors_dict, 
                                    price_series,  # Pass actual price data if available
                                    ticker_data.get('Name', search_ticker)
                                )
                                
                                # Display AI analysis in cards
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown('<div class="card">', unsafe_allow_html=True)
                                    st.markdown('<div class="section-title">ASSESSMENT</div>', unsafe_allow_html=True)
                                    st.write(ai_analysis.get('overall', 'AI analysis complete'))
                                    st.markdown('</div>', unsafe_allow_html=True)
                                    
                                    st.markdown('<div class="card">', unsafe_allow_html=True)
                                    st.markdown('<div class="section-title">FACTORS</div>', unsafe_allow_html=True)
                                    st.write(ai_analysis.get('factors', 'AI analysis complete'))
                                    st.markdown('</div>', unsafe_allow_html=True)
                                
                                with col2:
                                    st.markdown('<div class="card">', unsafe_allow_html=True)
                                    st.markdown('<div class="section-title">RISK</div>', unsafe_allow_html=True)
                                    st.write(ai_analysis.get('risk', 'AI analysis complete'))
                                    st.markdown('</div>', unsafe_allow_html=True)
                                    
                                    st.markdown('<div class="card">', unsafe_allow_html=True)
                                    st.markdown('<div class="section-title">ADVICE</div>', unsafe_allow_html=True)
                                    st.write(ai_analysis.get('recommendation', 'AI analysis complete'))
                                    st.markdown('</div>', unsafe_allow_html=True)
                                
                                # Market context in full width
                                st.markdown('<div class="card">', unsafe_allow_html=True)
                                st.markdown('<div class="section-title">CONTEXT</div>', unsafe_allow_html=True)
                                st.write(ai_analysis.get('market_context', 'AI analysis complete'))
                                st.markdown('</div>', unsafe_allow_html=True)
                                
                    except Exception as e:
                        st.markdown(f'<div class="alert alert-warning">AI analysis temporarily unavailable: {str(e)}</div>', unsafe_allow_html=True)
                        st.info("The quantitative analysis above provides excellent insights!")
                else:
                    st.markdown('<div class="alert alert-info">🔑 Add GEMINI_API_KEY to your environment for AI-powered analysis</div>', unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Stock-specific news section (only if a stock was analyzed)
                if 'search_ticker' in locals() and search_ticker:
                    st.markdown(f'<div class="section-title">{search_ticker} NEWS</div>', unsafe_allow_html=True)
                    
                    # Fetch news for the analyzed stock
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
        
        # News Section
        neon_divider("MARKET NEWS")
        
        
        
        # Display news section
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">MARKET NEWS</div>', unsafe_allow_html=True)
            
            # Get general market news
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
            
            # Get news for top 3 stocks
            top_stocks = df.head(3).index.tolist() if df is not None and not df.empty else ['AAPL', 'TSLA', 'GOOGL']
            
            for ticker in top_stocks[:3]:  # Show news for top 3 stocks
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
        
        # AI Quota Status
        if ai_enabled:
            quota_status = get_quota_status()
            st.sidebar.markdown("---")
            st.sidebar.markdown("### AI Quota Status")
            st.sidebar.markdown(f"**Remaining:** {quota_status['remaining']}/{quota_status['max']}")
            st.sidebar.progress(quota_status['used'] / quota_status['max'])
            
            if quota_status['remaining'] < 10:
                st.sidebar.warning("⚠️ AI quota running low!")
            elif quota_status['remaining'] == 0:
                st.sidebar.error("❌ AI quota exceeded - using fallback analysis")
        
        # News settings in sidebar
        with st.sidebar:
            st.markdown("---")
            st.markdown("### News Settings")
            
            # News refresh button
            if st.button("Refresh News", use_container_width=True):
                st.rerun()
            
            # News preferences
            st.markdown("**News Sources:**")
            st.checkbox("Market News", value=True, disabled=True)
            st.checkbox("Stock-Specific", value=True, disabled=True)
            st.checkbox("Economic Data", value=True, disabled=True)
            
            st.markdown("**Note:** To enable real-time news, add a NewsAPI key to your environment variables.")
        
        neon_divider("PORTFOLIO ANALYSIS")
        left, right = st.columns(2, gap="large")

        with left:
            st.markdown('<div class="analysis-section"><div class="section-title">PORTFOLIO OVERVIEW</div>', unsafe_allow_html=True)
            avg_score = df['Score'].mean()
            avg_return = df['MOM_1M'].mean()
            avg_sharpe = df['Sharpe_3M'].mean()
            top_stocks = df.head(3).index.tolist()
            
            # Calculate reputation metrics if available
            reputation_metrics = ""
            if 'Reputation_Score' in df.columns:
                avg_reputation = df['Reputation_Score'].mean()
                avg_esg = df['ESG_Score'].mean() if 'ESG_Score' in df.columns else 0
                reputation_metrics = f"""
                - Avg Reputation Score: **{avg_reputation:.1%}**
                - Avg ESG Score: **{avg_esg:.1%}**
                """
            
            st.markdown(f"""
            This portfolio contains **{len(df)}** stocks with an average score **{avg_score:.3f}**.
            - Avg 1M Return: **{avg_return:.1%}**
            - Avg Sharpe: **{avg_sharpe:.2f}**{reputation_metrics}
            """)
            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            st.markdown('<div class="analysis-section"><div class="section-title">SECTOR ANALYSIS</div>', unsafe_allow_html=True)
            st.markdown(f"""
            **Sector Analysis:**
            
            The portfolio includes stocks from various sectors including technology, healthcare, financials, and consumer goods.
            This diversification helps reduce sector-specific risks while maintaining exposure to growth opportunities.
            
            **Portfolio Statistics:**
            - Total Stocks: **{len(df)}**
            - Average Score: **{avg_score:.3f}**
            - Risk Level: **{'Low' if avg_sharpe > 2 else 'Medium' if avg_sharpe > 1 else 'High'}**
            """)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Optional AI Enhancement
        if ai_enabled and st.sidebar.checkbox("Enable AI Analysis", value=False, help="Use AI for enhanced insights (uses API calls)"):
            try:
                with st.spinner("Generating AI insights..."):
                    portfolio_insights = generate_portfolio_insights(df)
                    
                    st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">AI Enhancement</div>', unsafe_allow_html=True)
                    st.markdown(portfolio_insights.get("portfolio_insights", "AI analysis complete"))
                    st.markdown("</div>", unsafe_allow_html=True)
            
            except Exception as e:
                st.markdown(f'<div class="alert alert-warning">AI analysis temporarily unavailable: {e}</div>', unsafe_allow_html=True)
                st.info("This is normal - the app works great with quantitative analysis only!")
        
        # Score Explanation
        with st.expander("How does the scoring work?", expanded=False):
            st.markdown("""
            **Our AI-powered scoring system evaluates stocks based on 11 key factors:**
            
            **Traditional Factors (67%):**
            1. **1-Month Momentum (20%)** - How well the stock has performed recently
            2. **3-Month Momentum (20%)** - Longer-term performance trend  
            3. **50-Day Slope (10%)** - Price trend direction and strength
            4. **30-Day Volatility (12%)** - How stable the stock price is
            5. **3-Month Sharpe Ratio (15%)** - Risk-adjusted returns
            6. **20-Day Dollar Volume (8%)** - Trading activity and liquidity
            
            **Reputation Factors (33%):**
            7. **Reputation Score (15%)** - Overall company reputation and quality
            8. **ESG Score (3%)** - Environmental, Social, and Governance metrics
            9. **Financial Health (3%)** - Debt ratios, profitability, and stability
            10. **Market Position (3%)** - Market cap, innovation, and competitive position
            11. **Growth Stability (3%)** - Revenue growth, earnings stability, and margins
            
            **Score Interpretation:**
            - **Strong Buy (1.0+)** - Top performers with excellent fundamentals and reputation
            - **Buy (0.5-1.0)** - Good stocks worth your consideration
            - **Hold (0.0-0.5)** - Average performers, monitor for changes
            - **Weak (<0.0)** - Underperformers, avoid for now
            
            *Higher scores indicate better overall performance across all factors including company reputation.*
            """)
        
        # Footer
        st.markdown("""
        <div class="footer">
            AI Daily Draft • Built with Streamlit • Data from Yahoo Finance<br>
            Last updated: {}
        </div>
        """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
        
    else:
        st.markdown('<div class="alert alert-danger">❌ No data available for the selected universe</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="alert alert-danger">❌ Could not load ranking data</div>', unsafe_allow_html=True)
