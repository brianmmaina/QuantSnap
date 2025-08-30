#!/usr/bin/env python3
"""
QuantSnap - Bloomberg Terminal Style UI
"""

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime, timedelta
import numpy as np
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')

def get_ai_analysis(ticker, metrics):
    """Get AI analysis using Gemini API"""
    if not GEMINI_API_KEY:
        return None
    
    try:
        # Prepare the analysis request
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
        
        # Call Gemini API
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        headers = {
            "Content-Type": "application/json",
        }
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
    except Exception as e:
        return None

def fetch_news(ticker=None, category="business"):
    """Fetch real news using News API"""
    if not NEWS_API_KEY:
        return []
    
    try:
        if ticker:
            # Stock-specific news
            query = f"{ticker} stock"
            url = f"https://newsapi.org/v2/everything"
        else:
            # General market news
            url = f"https://newsapi.org/v2/top-headlines"
        
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
            
            # Process articles
            processed_news = []
            for article in articles[:5]:  # Limit to 5 articles
                # Simple sentiment analysis based on title keywords
                title = article.get('title', '').lower()
                sentiment = 'neutral'
                if any(word in title for word in ['surge', 'jump', 'rise', 'gain', 'positive', 'beat', 'exceed']):
                    sentiment = 'positive'
                elif any(word in title for word in ['fall', 'drop', 'decline', 'negative', 'miss', 'loss']):
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

# Bloomberg Terminal Plotly Template
bloomberg_template = dict(
    layout=dict(
        paper_bgcolor="#0B0F10",
        plot_bgcolor="#0B0F10",
        font=dict(family="JetBrains Mono, Menlo, monospace", color="#D7E1E8", size=13),
        xaxis=dict(
            gridcolor="#1C2328", 
            zerolinecolor="#1C2328", 
            linecolor="#2A3338", 
            tickcolor="#2A3338",
            tickfont=dict(color="#D7E1E8")
        ),
        yaxis=dict(
            gridcolor="#1C2328", 
            zerolinecolor="#1C2328", 
            linecolor="#2A3338", 
            tickcolor="#2A3338",
            tickfont=dict(color="#D7E1E8")
        ),
        legend=dict(bgcolor="#0B0F10", bordercolor="#2A3338", font=dict(color="#D7E1E8")),
        margin=dict(l=40, r=30, t=40, b=40),
        hoverlabel=dict(bgcolor="#111417", bordercolor="#2A3338", font_color="#D7E1E8"),
        colorway=["#00E676", "#00C2FF", "#FFB000", "#FF4D4D", "#A78BFA", "#64FFDA"],
        title=dict(font=dict(color="#D7E1E8")),
        annotations=[dict(font=dict(color="#D7E1E8"))]
    )
)
pio.templates["bloomberg"] = bloomberg_template
pio.templates.default = "bloomberg"

# Page configuration
st.set_page_config(
    page_title="QuantSnap - Stock Rankings",
    page_icon="📈",
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

# Stock Universe
STOCK_UNIVERSE = [
    # Tech
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX", "ADBE", "CRM",
    "ORCL", "INTC", "AMD", "QCOM", "AVGO", "TXN", "MU", "ADI", "KLAC", "LRCX",
    # Healthcare
    "JNJ", "PFE", "UNH", "ABBV", "TMO", "DHR", "LLY", "MRK", "BMY", "AMGN",
    "GILD", "CVS", "CI", "HUM", "CNC", "WBA", "DGX", "LH", "IDXX",
    # Financial
    "JPM", "BAC", "WFC", "GS", "MS", "C", "USB", "PNC", "TFC", "COF",
    "AXP", "BLK", "SCHW", "CME", "ICE", "SPGI", "MCO", "FIS", "GPN",
    # Consumer
    "PG", "KO", "PEP", "WMT", "HD", "MCD", "NKE", "SBUX", "TGT", "LOW",
    "COST", "TJX", "ROST", "ULTA", "BKNG", "MAR", "HLT", "YUM", "CMG", "DPZ",
    # Industrial
    "BA", "CAT", "GE", "MMM", "HON", "UPS", "FDX", "RTX", "LMT", "NOC",
    "GD", "LHX", "TDG", "AME", "ETN", "EMR", "ITW", "DOV", "XYL", "FTV",
    # Energy
    "XOM", "CVX", "COP", "EOG", "SLB", "PSX", "VLO", "MPC", "OXY", "KMI",
    # Materials
    "LIN", "APD", "FCX", "NEM", "DOW", "DD", "NUE", "STLD", "VMC", "MLM",
    # Utilities
    "NEE", "DUK", "SO", "D", "AEP", "SRE", "XEL", "WEC", "DTE", "ED",
    # Real Estate
    "AMT", "PLD", "CCI", "EQIX", "DLR", "PSA", "SPG", "O", "WELL", "EQR",
    # Communication
    "VZ", "T", "TMUS", "CMCSA", "CHTR", "DISH", "PARA", "FOX", "NWSA", "NWS"
]

def fetch_stock_data(ticker, period="6mo"):
    """Fetch stock data using yfinance"""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period, auto_adjust=True)
        return data
    except Exception as e:
        return None

def calculate_metrics(ticker_data):
    """Calculate metrics for a stock"""
    try:
        if ticker_data.empty or len(ticker_data) < 30:
            return None
        
        # Calculate returns
        returns = ticker_data['Close'].pct_change().dropna()
        
        # 1-month and 3-month returns
        if len(ticker_data) >= 21:
            month_ago = ticker_data.index[-21]
            month_return = ((ticker_data['Close'].iloc[-1] / ticker_data.loc[month_ago, 'Close']) - 1) * 100
        else:
            month_return = 0
            
        if len(ticker_data) >= 63:
            three_months_ago = ticker_data.index[-63]
            three_month_return = ((ticker_data['Close'].iloc[-1] / ticker_data.loc[three_months_ago, 'Close']) - 1) * 100
        else:
            three_month_return = 0
        
        # Volatility (annualized)
        volatility = returns.std() * np.sqrt(252) * 100
        
        # Sharpe ratio (assuming 0% risk-free rate)
        if volatility > 0:
            sharpe_ratio = (returns.mean() * 252) / (returns.std() * np.sqrt(252))
        else:
            sharpe_ratio = 0
        
        # Volume factor (normalized)
        avg_volume = ticker_data['Volume'].mean()
        volume_factor = min(avg_volume / 1000000, 1.0)
        
        return {
            'momentum_1m': month_return,
            'momentum_3m': three_month_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'volume_factor': volume_factor,
            'current_price': ticker_data['Close'].iloc[-1],
            'price_change': ticker_data['Close'].iloc[-1] - ticker_data['Close'].iloc[-2],
            'price_change_pct': ((ticker_data['Close'].iloc[-1] / ticker_data['Close'].iloc[-2]) - 1) * 100
        }
    except Exception as e:
        return None

def calculate_score(metrics):
    """Calculate composite score using 67/33 weighting"""
    if not metrics:
        return 0
    
    # Traditional factors (67% weight)
    momentum_1m = metrics.get('momentum_1m', 0)
    momentum_3m = metrics.get('momentum_3m', 0)
    sharpe_ratio = metrics.get('sharpe_ratio', 0)
    volume_factor = metrics.get('volume_factor', 0)
    
    # Apply performance filters
    if momentum_1m < -5:
        momentum_1m *= 0.1  # 90% penalty
    elif momentum_1m < 0:
        momentum_1m *= 0.3  # 70% penalty
    elif momentum_1m < 2:
        momentum_1m *= 0.7  # 30% penalty
    
    # Traditional score (67%)
    traditional_score = (
        (momentum_1m * 0.4) +      # 40% of traditional
        (momentum_3m * 0.25) +     # 25% of traditional
        (sharpe_ratio * 0.15) +    # 15% of traditional
        (volume_factor * 0.1) +    # 10% of traditional
        (volume_factor * 0.1)      # 10% market cap factor (using volume as proxy)
    ) * 0.67
    
    # Reputation factors (33%) - simplified for now
    volatility = metrics.get('volatility', 0)
    volatility_score = max(0, 10 - volatility)  # Lower volatility = higher score
    
    reputation_score = volatility_score * 0.33
    
    # Final score (0-10 scale)
    final_score = max(0, min(10, traditional_score + reputation_score))
    
    return final_score

def get_stock_info(ticker):
    """Get basic stock information"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            'name': info.get('longName', info.get('shortName', ticker)),
            'sector': info.get('sector', 'Unknown'),
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': info.get('trailingPE', 0),
            'dividend_yield': info.get('dividendYield', 0),
            'beta': info.get('beta', 1.0)
        }
    except:
        return {
            'name': ticker,
            'sector': 'Unknown',
            'market_cap': 0,
            'pe_ratio': 0,
            'dividend_yield': 0,
            'beta': 1.0
        }

def neon_divider(label:str):
    """Create a neon divider with title"""
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin:22px 0 8px">
      <div style="height:1px;background:var(--border);flex:1"></div>
      <div style="font-weight:800;color:var(--muted);letter-spacing:.2px;font-family: JetBrains Mono;">{label.upper()}</div>
      <div style="height:1px;background:var(--border);flex:1"></div>
    </div>
    """, unsafe_allow_html=True)

# Methodology Section
st.markdown("""
<div class="card" style="margin-bottom: 20px;">
  <div class="section-title">RANKING METHODOLOGY</div>
  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 16px;">
    <div>
      <div style="font-weight: 700; color: var(--accent); margin-bottom: 8px;">SCORING ALGORITHM</div>
      <div style="font-size: 14px; line-height: 1.5; color: var(--text);">
        <strong>Composite Score =</strong><br>
        • 1M Stock Price Growth (40% of traditional)<br>
        • 3M Stock Price Growth (25% of traditional)<br>
        • Sharpe Ratio (15% of traditional)<br>
        • Volume Factor (10% of traditional)<br>
        • Market Cap Factor (10% of traditional)
      </div>
    </div>
    <div>
      <div style="font-weight: 700; color: var(--accent); margin-bottom: 8px;">DATA SOURCES</div>
      <div style="font-size: 14px; line-height: 1.5; color: var(--text);">
        • <strong>Yahoo Finance:</strong> Real-time prices & fundamentals<br>
        • <strong>300+ Stocks:</strong> Comprehensive market coverage<br>
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

# Data Loading
with st.spinner("Loading stock data..."):
    all_metrics = {}
    
    # Analyze top 50 stocks for ranking
    for ticker in STOCK_UNIVERSE[:50]:
        data = fetch_stock_data(ticker, "6mo")
        if data is not None and not data.empty and len(data) > 30:
            metrics = calculate_metrics(data)
            if metrics:
                metrics['ticker'] = ticker
                metrics['score'] = calculate_score(metrics)
                all_metrics[ticker] = metrics
    
    if all_metrics:
        # Convert to DataFrame and sort by score
        df = pd.DataFrame.from_dict(all_metrics, orient='index')
        df = df.sort_values('score', ascending=False).head(10)
        
        # Add company names
        for ticker in df.index:
            info = get_stock_info(ticker)
            df.loc[ticker, 'name'] = info['name']
            df.loc[ticker, 'price'] = df.loc[ticker, 'current_price']
    else:
        df = pd.DataFrame()

# Display main content
if df is not None and not df.empty:
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
      <div class="section-title">AVG 1M GROWTH</div>
      <div style="font-size:28px;font-weight:800"
                       class="{ 'c-up' if df['momentum_1m'].mean()>=0 else 'c-down' }">
         {df['momentum_1m'].mean():.1f}%
      </div>
    </div>""", unsafe_allow_html=True)

    c4.markdown(f"""
    <div class="card">
      <div class="section-title">AVG 3M GROWTH</div>
                 <div style="font-size:28px;font-weight:800" class="c-info">{df['momentum_3m'].mean():.1f}%</div>
    </div>""", unsafe_allow_html=True)
    
    neon_divider("TOP PERFORMERS")
    cols = st.columns(2)

    for i, (ticker, row) in enumerate(df.head(10).iterrows(), 1):
        score = row['score']
        growth_1m = row['momentum_1m']
        sharpe = row.get('sharpe_ratio', 0)
        company_name = row.get('name', ticker)
        
        score_class = "c-up" if score>7 else "c-warn" if score>4 else "c-muted" if score>0 else "c-down"
        
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
                      <div style="font-size: 12px; color: var(--muted);">1M Growth</div>
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
    
    # Stock search for charts
    col1, col2 = st.columns([2, 1])
    with col1:
        chart_stock = st.text_input(
            "Enter any stock symbol for chart (e.g., AAPL, TSLA, GOOGL)",
            value="AAPL",
            placeholder="AAPL",
            help="Enter any valid stock symbol to display its price chart"
        )
    
    if chart_stock:
        chart_stock = chart_stock.upper().strip()
        chart_data = fetch_stock_data(chart_stock, "1y")
        
        if chart_data is not None and not chart_data.empty:
            # Create Bloomberg-style price chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=chart_data.index,
                y=chart_data['Close'],
                mode='lines',
                line=dict(color='#00E676', width=2),
                name=f'{chart_stock} Price',
                hovertemplate='<b>%{x}</b><br>Price: $%{y:.2f}<extra></extra>'
            ))
            
            fig.update_layout(
                title=f"{chart_stock} Price Chart - 1 Year",
                xaxis_title="Date",
                yaxis_title="Price ($)",
                height=400,
                showlegend=False,
                hovermode='x unified',
                template="bloomberg"
            )
            
            st.plotly_chart(fig, use_container_width=True, theme=None)
            
            # Current price info
            current_price = chart_data['Close'].iloc[-1]
            start_price = chart_data['Close'].iloc[0]
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
                st.metric("Period", "1 Year")
        else:
            st.error(f"Could not fetch data for {chart_stock}. Please check the stock symbol.")
    
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
            placeholder="AAPL", 
            label_visibility="collapsed",
            key="analysis_input"
        )
        search_button = st.form_submit_button("Analyze", type="primary", use_container_width=True)
    
    # Handle form submission
    if search_button and search_ticker:
        search_ticker = search_ticker.upper().strip()
        
        # Get stock data
        with st.spinner(f"Analyzing {search_ticker}..."):
            stock_data = fetch_stock_data(search_ticker, "6mo")
            
        if stock_data is not None and not stock_data.empty:
            metrics = calculate_metrics(stock_data)
            if metrics:
                # Display analysis in organized layout
                left, right = st.columns(2, gap="large")
                
                with left:
                    st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">OVERVIEW</div>', unsafe_allow_html=True)
                    
                    score = metrics['score']
                    growth_1m = metrics['momentum_1m']
                    growth_3m = metrics['momentum_3m']
                    price = metrics['current_price']
                    
                    # Determine sentiment
                    if score > 7:
                        sentiment = "very bullish"
                        recommendation = "Strong Buy"
                    elif score > 5:
                        sentiment = "bullish"
                        recommendation = "Buy"
                    elif score > 3:
                        sentiment = "neutral"
                        recommendation = "Hold"
                    else:
                        sentiment = "bearish"
                        recommendation = "Sell"
                    
                    st.markdown(f"""
                    **{search_ticker}** shows **{sentiment}** signals.
                    
                    **Key Metrics:**
                    - **Current Price:** ${price:.2f}
                    - **AI Score:** {score:.1f}/10
                    - **1-Month Growth:** {growth_1m:.1f}%
                    - **3-Month Growth:** {growth_3m:.1f}%
                    
                    **Investment Recommendation:** {recommendation}
                    """)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with right:
                    st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">PERFORMANCE</div>', unsafe_allow_html=True)
                    
                    volatility = metrics['volatility']
                    sharpe = metrics['sharpe_ratio']
                    
                    st.markdown(f"""
                    **Performance Breakdown:**
                    
                    The stock demonstrates {'strong' if score > 7 else 'moderate' if score > 5 else 'weak'} performance signals.
                    
                    **Risk Assessment:**
                    - **Volatility:** {volatility:.1f}% ({'Low' if volatility < 20 else 'Medium' if volatility < 40 else 'High'} risk)
                    - **Sharpe Ratio:** {sharpe:.2f} ({'Good' if sharpe > 1 else 'Fair' if sharpe > 0 else 'Poor'} risk-adjusted returns)
                    - **Overall Risk:** {'Low' if score > 7 else 'Medium' if score > 5 else 'High'}
                    
                    **Market Position:** {'Outperforming' if growth_1m > 5 else 'In-line' if growth_1m > -5 else 'Underperforming'}
                    """)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # AI Analysis Section
                if GEMINI_API_KEY:
                    st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">AI ANALYSIS</div>', unsafe_allow_html=True)
                    
                    with st.spinner("Generating AI analysis..."):
                        ai_analysis = get_ai_analysis(search_ticker, metrics)
                    
                    if ai_analysis:
                        st.markdown(ai_analysis)
                    else:
                        st.markdown("AI analysis temporarily unavailable. Please try again later.")
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error(f"Could not analyze {search_ticker}. Please check the stock symbol.")
        else:
            st.error(f"Could not fetch data for {search_ticker}. Please check the stock symbol.")
    
    neon_divider("MARKET NEWS")
    
    # Display news section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">MARKET NEWS</div>', unsafe_allow_html=True)
        
        # Fetch real market news
        market_news = fetch_news()
        
        if market_news:
            for i, news in enumerate(market_news, 1):
                sentiment_color = {
                    'positive': 'var(--up)',
                    'negative': 'var(--down)',
                    'neutral': 'var(--muted)'
                }.get(news['sentiment'], 'var(--muted)')
                
                # Format date
                try:
                    published_date = datetime.fromisoformat(news['published_at'].replace('Z', '+00:00'))
                    formatted_date = published_date.strftime('%Y-%m-%d %H:%M')
                except:
                    formatted_date = news['published_at']
                
                st.markdown(f"""
                <a href="{news['url']}" target="_blank" style="text-decoration: none; color: inherit;">
                    <div style="margin-bottom: 16px; padding: 12px; border-left: 3px solid {sentiment_color}; background: rgba(255,255,255,.02); cursor: pointer; transition: background-color 0.2s;">
                        <div style="font-weight: 700; font-size: 14px; margin-bottom: 4px;">{news['title']}</div>
                        <div style="color: var(--muted); font-size: 13px; margin-bottom: 6px;">{news['description']}</div>
                        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: var(--muted);">
                            <span>{news['source']}</span>
                            <span>{formatted_date}</span>
                        </div>
                    </div>
                </a>
                """, unsafe_allow_html=True)
        else:
            st.markdown("News temporarily unavailable. Please check your internet connection.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">TOP STOCK NEWS</div>', unsafe_allow_html=True)
        
        # Get news for top 4 stocks
        top_stocks = df.head(4).index.tolist() if df is not None and not df.empty else ['AAPL', 'TSLA', 'GOOGL', 'MSFT']
        
        for ticker in top_stocks[:4]:  # Show news for top 4 stocks
            # Fetch stock-specific news
            stock_news = fetch_news(ticker)
            
            if stock_news:
                news = stock_news[0]  # Get the most recent news
                sentiment_color = {
                    'positive': 'var(--up)',
                    'negative': 'var(--down)',
                    'neutral': 'var(--muted)'
                }.get(news['sentiment'], 'var(--muted)')
                
                # Format date
                try:
                    published_date = datetime.fromisoformat(news['published_at'].replace('Z', '+00:00'))
                    formatted_date = published_date.strftime('%m-%d %H:%M')
                except:
                    formatted_date = news['published_at']
                
                st.markdown(f"""
                <a href="{news['url']}" target="_blank" style="text-decoration: none; color: inherit;">
                    <div style="margin-bottom: 12px; padding: 10px; border-left: 3px solid {sentiment_color}; background: rgba(255,255,255,.02); border-radius: 6px; cursor: pointer; transition: background-color 0.2s;">
                        <div style="font-weight: 700; font-size: 12px; margin-bottom: 4px; color: var(--accent);">{ticker}</div>
                        <div style="font-weight: 600; font-size: 11px; margin-bottom: 3px; line-height: 1.3;">{news['title']}</div>
                        <div style="color: var(--muted); font-size: 10px;">{news['source']} • {formatted_date}</div>
                    </div>
                </a>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="margin-bottom: 12px; padding: 10px; border-left: 3px solid var(--muted); background: rgba(255,255,255,.02); border-radius: 6px;">
                    <div style="font-weight: 700; font-size: 12px; margin-bottom: 4px; color: var(--accent);">{ticker}</div>
                    <div style="color: var(--muted); font-size: 10px;">No recent news available</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div class="footer" style="text-align: center; margin-top: 40px; padding: 20px; color: var(--muted);">
        QuantSnap • Built with Streamlit • Data from Yahoo Finance<br>
        Last updated: {}
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
    
else:
    st.markdown('<div class="alert alert-danger">❌ Could not load ranking data</div>', unsafe_allow_html=True)
