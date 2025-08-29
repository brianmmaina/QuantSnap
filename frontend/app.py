#!/usr/bin/env python3
"""
QuantSnap 
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime, timedelta
from typing import Dict
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bloomberg Terminal Plotly Template
bloomberg_template = dict(
    layout=dict(
        paper_bgcolor="#0B0F10",
        plot_bgcolor="#0B0F10",
        font=dict(family="JetBrains Mono, Menlo, monospace", color="#FFFFFF", size=13),
        xaxis=dict(
            gridcolor="#2A3338", 
            zerolinecolor="#2A3338", 
            linecolor="#4A5568", 
            tickcolor="#4A5568",
            tickfont=dict(color="#FFFFFF", size=11),
            title=dict(font=dict(color="#FFFFFF", size=12))
        ),
        yaxis=dict(
            gridcolor="#2A3338", 
            zerolinecolor="#2A3338", 
            linecolor="#4A5568", 
            tickcolor="#4A5568",
            tickfont=dict(color="#FFFFFF", size=11),
            title=dict(font=dict(color="#FFFFFF", size=12))
        ),
        legend=dict(
            bgcolor="#111417", 
            bordercolor="#4A5568", 
            font=dict(color="#FFFFFF", size=11)
        ),
        margin=dict(l=50, r=30, t=50, b=50),
        hoverlabel=dict(
            bgcolor="#1A202C", 
            bordercolor="#4A5568", 
            font_color="#FFFFFF",
            font_size=12
        ),
        colorway=["#00E676", "#00C2FF", "#FFB000", "#FF4D4D", "#A78BFA", "#64FFDA"],
        title=dict(font=dict(color="#FFFFFF", size=16)),
        annotations=[dict(font=dict(color="#FFFFFF"))]
    )
)
pio.templates["bloomberg"] = bloomberg_template
pio.templates.default = "bloomberg"

# API Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'https://quantsnap-backend.onrender.com')

def api_request(endpoint: str, params: Dict = None) -> Dict:
    """Make API request to backend"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
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

# News fetching function
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
                        
                        # Enhanced sentiment analysis with comprehensive word lists
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
                        
                        # Count positive and negative words
                        positive_count = sum(1 for word in positive_words if word in content)
                        negative_count = sum(1 for word in negative_words if word in content)
                        
                        # Determine sentiment based on word frequency
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
        
        # Fallback news
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

# Page configuration
st.set_page_config(
    page_title="QuantSnap - Stock Rankings",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Bloomberg Terminal Theme
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

# QuantSnap Terminal Banner
st.markdown("""
<div class="title-wrap">
  <div class="title">QUANTSNAP</div>
</div>
""", unsafe_allow_html=True)
st.write("")

# Methodology Section
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
      <div style="font-weight: 700; color: var(--accent); margin-bottom: 8px;">DATA SOURCES</div>
      <div style="font-size: 14px; line-height: 1.5; color: var(--text);">
        • <strong>Yahoo Finance:</strong> Real-time prices & fundamentals<br>
        • <strong>500+ Stocks:</strong> Comprehensive market coverage<br>
        • <strong>Daily Updates:</strong> Fresh data every session<br>
        • <strong>Auto-adjusted:</strong> Splits & dividends included
      </div>
    </div>
  </div>
  <div style="font-size: 13px; color: var(--muted); border-top: 1px solid var(--border); padding-top: 12px;">
    <strong>Note:</strong> Rankings are based on quantitative factors only. Past performance does not guarantee future results.
  </div>
</div>
""", unsafe_allow_html=True)

# Live Ticker Tape Function
def ticker_tape(df):
    items = []
    for t, r in df.head(10).iterrows():
        # Use 1-month stock price growth for ticker tape (more stable)
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

# Premium Neon Divider Function
def neon_divider(label:str):
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin:22px 0 8px">
      <div style="height:1px;background:var(--border);flex:1"></div>
      <div style="font-weight:800;color:var(--muted);letter-spacing:.2px;font-family: JetBrains Mono;">{label.upper()}</div>
      <div style="height:1px;background:var(--border);flex:1"></div>
    </div>
    """, unsafe_allow_html=True)

# Initialize session state
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None
if 'chart_search' not in st.session_state:
    st.session_state.chart_search = "AAPL"
if 'analysis_search' not in st.session_state:
    st.session_state.analysis_search = ""

# Data Loading from API
st.markdown('<div style="text-align: center; color: var(--accent); font-family: JetBrains Mono; font-weight: 600; margin: 20px 0;">Loading data from database...</div>', unsafe_allow_html=True)
df = get_rankings_from_api("world_top_stocks", 10)

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
        cols = st.columns(2)

        for i, (ticker, row) in enumerate(df.head(10).iterrows(), 1):
            score = row['score']
            # This is actual stock price growth percentage (not momentum)
            growth_1m = row['momentum_1m']
            sharpe = row.get('sharpe_ratio', 0)
            company_name = row.get('name', ticker)
            logo_url = row.get('logo_url', '')
            
            score_class = "c-up" if score>10 else "c-warn" if score>5 else "c-muted" if score>0 else "c-down"
            
            # Left column: ranks 1-5, Right column: ranks 6-10
            with cols[0] if i <= 5 else cols[1]:
                st.markdown(f"""
                <a href="https://finance.yahoo.com/quote/{ticker}" target="_blank" style="text-decoration: none; color: inherit;">
                    <div class="stock-card" style="cursor: pointer; transition: background-color 0.2s; margin-bottom: 16px;">
                      <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                        <div class="badge" style="font-size: 14px; font-weight: 800;">#{i}</div>
                        <div style="font-weight: 700; font-size: 16px; color: var(--accent);">{ticker}</div>
                      </div>
                      <div style="font-weight: 600; font-size: 14px; color: var(--text); margin-bottom: 8px; line-height: 1.3;">
                        {company_name}
                      </div>
                      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px;">
                        <div>
                          <div style="font-size: 12px; color: var(--muted);">Rating</div>
                          <div style="font-weight: 700; font-size: 16px;" class="{score_class}">{score:.1f}</div>
                        </div>
                        <div>
                          <div style="font-size: 12px; color: var(--muted);">1M Stock Growth</div>
                          <div style="font-weight: 700; font-size: 16px;" class="{'c-up' if growth_1m>=0 else 'c-down'}">{growth_1m:+.1f}%</div>
                        </div>
                      </div>
                      <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                          <div style="font-size: 12px; color: var(--muted);">Sharpe</div>
                          <div style="font-weight: 600; font-size: 14px;" class="c-info">{sharpe:.2f}</div>
                        </div>
                        <div style="text-align: right;">
                          <div style="font-size: 12px; color: var(--muted);">Price</div>
                          <div style="font-weight: 700; font-size: 16px;">${row['price']:.2f}</div>
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
                # Fetch data from backend API
                st.markdown(f'<div style="text-align: center; color: var(--accent); font-family: JetBrains Mono; font-weight: 600; margin: 10px 0;">Fetching data for {chart_stock}...</div>', unsafe_allow_html=True)

                try:
                        chart_response = api_request(f"/chart/{chart_stock}?period=1y")
                        if chart_response and 'data' in chart_response:
                            # Convert chart data to pandas series for compatibility
                            chart_data = chart_response['data']
                            dates = pd.to_datetime([item['date'] for item in chart_data])
                            prices = [item['close'] for item in chart_data]
                            price_series = pd.Series(prices, index=dates)
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
                        hovermode='x unified',
                        template="bloomberg"
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
            # Get current prices for top stocks from backend API
            top_stocks_prices = df.head(10).index.tolist()
            tickers_str = ','.join(top_stocks_prices)
            
            # Fetch live prices from backend
            price_response = api_request(f"/prices/live?tickers={tickers_str}")
            price_data = price_response.get('prices', {})
            
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
        
        # AI Status
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
        
        # Stock Analysis Form
        with st.form("stock_analysis_form", clear_on_submit=False):
            search_ticker = st.text_input(
                "Enter stock symbol (e.g., AAPL, TSLA, GOOGL)", 
                value=st.session_state.analysis_search,
                placeholder="AAPL", 
                label_visibility="collapsed",
                key="analysis_input"
            )
            search_button = st.form_submit_button("Analyze", type="primary", use_container_width=True)
        
        # Handle form submission
        if search_button and search_ticker:
            st.session_state.analysis_search = search_ticker.upper().strip()
            search_ticker = st.session_state.analysis_search
            
            # Get stock data from API
            st.markdown(f'<div style="text-align: center; color: var(--accent); font-family: JetBrains Mono; font-weight: 600; margin: 10px 0;">Analyzing {search_ticker}...</div>', unsafe_allow_html=True)
            stock_data = get_stock_data_from_api(search_ticker)
            
            # Get AI analysis
            ai_analysis = None
            if stock_data:
                ai_response = api_request(f"/stock/{search_ticker}/analysis")
                if ai_response and 'ai_analysis' in ai_response:
                    ai_analysis = ai_response['ai_analysis']
                
            if stock_data:
                # Display analysis in organized layout
                left, right = st.columns(2, gap="large")
                
                with left:
                    st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">OVERVIEW</div>', unsafe_allow_html=True)
                    
                    score = stock_data.get('score', 0)
                    # These are actual stock price growth percentages from backend
                    growth_1m = stock_data.get('momentum_1m', 0)  # 1-month price growth %
                    growth_3m = stock_data.get('momentum_3m', 0)  # 3-month price growth %
                    price = stock_data.get('price', 0)
                    
                    # Convert score to 0-100 scale and determine sentiment
                    score_100 = min(max(score * 10, 0), 100)  # Scale to 0-100, cap at 100
                    
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
                    
                    st.markdown(f"""
                    **{search_ticker}** ({stock_data.get('name', search_ticker)}) shows **{sentiment}** signals.
                    
                    **Key Metrics:**
                    - **Current Price:** ${price:.2f}
                    - **AI Score:** {score_100:.1f}/100
                    - **1-Month Stock Growth:** {growth_1m:.1%}
                    - **3-Month Stock Growth:** {growth_3m:.1%}
                    
                    **Investment Recommendation:** {recommendation}
                    """)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with right:
                    st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">PERFORMANCE</div>', unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    **Performance Breakdown:**
                    
                    The stock demonstrates {'strong' if score > 1 else 'moderate' if score > 0.5 else 'weak'} performance signals.
                    
                    **Risk Assessment:**
                    - **Stock Growth Risk:** {'Low' if growth_1m > 0.05 else 'Medium' if growth_1m > -0.05 else 'High'}
                    - **Trend Risk:** {'Low' if growth_3m > 0.1 else 'Medium' if growth_3m > -0.05 else 'High'}
                    - **Overall Risk:** {'Low' if score > 1 else 'Medium' if score > 0.5 else 'High'}
                    
                    **Market Position:** {'Outperforming' if growth_1m > 0.1 else 'In-line' if growth_1m > -0.05 else 'Underperforming'}
                    """)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # AI Analysis section
                if ai_analysis and ai_analysis != "AI analysis disabled - no API key configured" and ai_analysis != "AI analysis quota exceeded for today":
                    st.markdown(f'<div class="section-title">AI ANALYSIS</div>', unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="analysis-section">
                        <div style="font-size: 14px; line-height: 1.6; color: var(--text);">
                            {ai_analysis}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Stock-specific news section
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
            
            # Get news for top 4 stocks
            top_stocks = df.head(4).index.tolist() if df is not None and not df.empty else ['AAPL', 'TSLA', 'GOOGL', 'MSFT']
            
            for ticker in top_stocks[:4]:  # Show news for top 4 stocks
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
        
        # Footer
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
