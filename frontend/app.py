#!/usr/bin/env python3
"""
QuantSnap 
"""

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import os
import requests
from typing import Dict, List
import time

# Page config
st.set_page_config(
    page_title="QuantSnap - AI Stock Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme
st.markdown("""
<style>
:root {
    --bg: #0E1117;
    --text: #FAFAFA;
    --muted: #9CA3AF;
    --border: #374151;
    --up: #00E676;
    --down: #FF5252;
    --warn: #FFB74D;
    --info: #64B5F6;
}

.stApp {
    background: var(--bg);
    color: var(--text);
}

.main .block-container {
    background: var(--bg);
    padding-top: 2rem;
    padding-bottom: 2rem;
}

.sidebar .sidebar-content {
    background: #1F2937;
}

.card {
    background: #1F2937;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
}

.section-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}

.metric-value {
    font-size: 24px;
    font-weight: 800;
    margin-bottom: 4px;
}

.metric-label {
    font-size: 12px;
    color: var(--muted);
}

.neon-divider {
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--up), transparent);
    margin: 2rem 0;
    border-radius: 1px;
}

/* Streamlit widget styling */
.stSelectbox > div > div {
    background: #1F2937 !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
}

.stButton > button {
    background: #1F2937 !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
}

.stButton > button:hover {
    background: #374151 !important;
}
</style>
""", unsafe_allow_html=True)

def neon_divider(title):
    """Create a neon divider with title"""
    st.markdown(f"""
    <div class="neon-divider"></div>
    <h2 style="text-align:center;color:var(--text);margin:1rem 0;">{title}</h2>
    <div class="neon-divider"></div>
    """, unsafe_allow_html=True)

def calculate_metrics(ticker_data):
    """Calculate metrics for a stock"""
    try:
        if ticker_data.empty:
            return None
        
        # Calculate returns
        returns = ticker_data['Close'].pct_change().dropna()
        
        # 1-month and 3-month returns
        if len(ticker_data) >= 21:  # At least 1 month of trading days
            month_ago = ticker_data.index[-21]
            month_return = ((ticker_data['Close'].iloc[-1] / ticker_data.loc[month_ago, 'Close']) - 1) * 100
        else:
            month_return = 0
            
        if len(ticker_data) >= 63:  # At least 3 months of trading days
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
        volume_factor = min(avg_volume / 1000000, 1.0)  # Normalize to 1M volume
        
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
        st.error(f"Error calculating metrics: {e}")
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
    # Using volatility as a quality indicator
    volatility = metrics.get('volatility', 0)
    volatility_score = max(0, 10 - volatility)  # Lower volatility = higher score
    
    reputation_score = volatility_score * 0.33
    
    # Final score (0-10 scale)
    final_score = max(0, min(10, traditional_score + reputation_score))
    
    return final_score

def fetch_stock_data(ticker, period="1y"):
    """Fetch stock data using yfinance"""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period, auto_adjust=True)
        return data
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        return None

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

def fetch_news(ticker, limit=3):
    """Fetch news for a stock (simplified)"""
    # For now, return empty list - can be enhanced later
    return []

def get_ai_analysis(ticker, stock_data, news_data=None):
    """Get AI analysis from backend"""
    try:
        backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
        
        payload = {
            "ticker": ticker,
            "stock_data": stock_data,
            "news_data": news_data or []
        }
        
        response = requests.post(
            f"{backend_url}/analyze",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"AI analysis unavailable: {response.status_code}")
            return None
            
    except Exception as e:
        st.warning(f"AI analysis unavailable: {str(e)}")
        return None

# Main app
def main():
    # Header
    st.markdown("""
    <div style="text-align:center;margin-bottom:2rem;">
        <h1 style="color:var(--text);font-size:3rem;font-weight:800;margin-bottom:0.5rem;">
            📈 QuantSnap
        </h1>
        <p style="color:var(--muted);font-size:1.2rem;margin:0;">
            AI-Powered Stock Analysis & Ranking
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.markdown("## 📊 Options")
    
    # Stock selection
    default_stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX", "ADBE", "CRM"]
    selected_stocks = st.sidebar.multiselect(
        "Select stocks to analyze:",
        options=default_stocks,
        default=default_stocks[:5]
    )
    
    if not selected_stocks:
        st.warning("Please select at least one stock to analyze.")
        return
    
    # Analysis period
    period = st.sidebar.selectbox(
        "Analysis period:",
        options=["6mo", "1y", "2y", "5y"],
        index=1
    )
    
    # Main content
    if selected_stocks:
        # Fetch data and calculate metrics
        with st.spinner("Fetching stock data..."):
            all_metrics = {}
            
            for ticker in selected_stocks:
                data = fetch_stock_data(ticker, period)
                if data is not None and not data.empty:
                    metrics = calculate_metrics(data)
                    if metrics:
                        metrics['ticker'] = ticker
                        metrics['score'] = calculate_score(metrics)
                        all_metrics[ticker] = metrics
            
            if not all_metrics:
                st.error("No data could be fetched for the selected stocks.")
                return
            
            # Convert to DataFrame
            df = pd.DataFrame.from_dict(all_metrics, orient='index')
            df = df.sort_values('score', ascending=False)
        
        # TOP PERFORMERS SECTION
        neon_divider("TOP PERFORMERS")
        
        # Display top performers
        top_performers = df.head(10)
        
        for i, (ticker, row) in enumerate(top_performers.iterrows()):
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
            
            with col1:
                st.markdown(f"""
                <div class="card">
                    <div style="font-size:18px;font-weight:700;color:var(--text);margin-bottom:4px;">
                        #{i+1} {ticker}
                    </div>
                    <div style="font-size:12px;color:var(--muted);">
                        Score: {row['score']:.2f}/10
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                change_color = "var(--up)" if row['price_change'] >= 0 else "var(--down)"
                st.markdown(f"""
                <div class="card" style="text-align:center;">
                    <div class="section-title">Current Price</div>
                    <div class="metric-value" style="color:var(--text);">${row['current_price']:.2f}</div>
                    <div style="font-size:12px;color:{change_color};">
                        {row['price_change']:+.2f} ({row['price_change_pct']:+.2f}%)
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                color_1m = "var(--up)" if row['momentum_1m'] >= 0 else "var(--down)"
                st.markdown(f"""
                <div class="card" style="text-align:center;">
                    <div class="section-title">1M Growth</div>
                    <div class="metric-value" style="color:{color_1m};">{row['momentum_1m']:+.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                color_3m = "var(--up)" if row['momentum_3m'] >= 0 else "var(--down)"
                st.markdown(f"""
                <div class="card" style="text-align:center;">
                    <div class="section-title">3M Growth</div>
                    <div class="metric-value" style="color:{color_3m};">{row['momentum_3m']:+.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col5:
                sharpe_color = "var(--up)" if row['sharpe_ratio'] >= 1 else "var(--warn)" if row['sharpe_ratio'] >= 0 else "var(--down)"
                st.markdown(f"""
                <div class="card" style="text-align:center;">
                    <div class="section-title">Sharpe</div>
                    <div class="metric-value" style="color:{sharpe_color};">{row['sharpe_ratio']:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # LIVE STOCK PRICES SECTION
        neon_divider("LIVE STOCK PRICES")
        
        # Stock search
        col1, col2 = st.columns([3, 1])
        with col1:
            search_ticker = st.text_input("Search for a stock:", value="AAPL").upper().strip()
        with col2:
            chart_period = st.selectbox("Chart period:", ["1M", "3M", "6M", "1Y", "2Y", "5Y"], index=3)
        
        if search_ticker:
            # Fetch data for chart
            period_map = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "2Y": "2y", "5Y": "5y"}
            chart_data = fetch_stock_data(search_ticker, period_map[chart_period])
            
            if chart_data is not None and not chart_data.empty:
                # Create chart
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=chart_data.index,
                    y=chart_data['Close'],
                    mode='lines',
                    name=search_ticker,
                    line=dict(color='#00E676', width=2),
                    fill='tonexty',
                    fillcolor='rgba(0, 230, 118, 0.1)'
                ))
                
                fig.update_layout(
                    title=f"{search_ticker} Stock Price ({chart_period})",
                    xaxis_title="Date",
                    yaxis_title="Price ($)",
                    template="plotly_dark",
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    height=400
                )
                
                fig.update_xaxes(
                    gridcolor='rgba(255,255,255,0.1)',
                    showgrid=True
                )
                
                fig.update_yaxes(
                    gridcolor='rgba(255,255,255,0.1)',
                    showgrid=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Current price info
                current_price = chart_data['Close'].iloc[-1]
                prev_price = chart_data['Close'].iloc[-2]
                price_change = current_price - prev_price
                price_change_pct = (price_change / prev_price) * 100
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Current Price", f"${current_price:.2f}")
                
                with col2:
                    st.metric("Change", f"${price_change:+.2f}")
                
                with col3:
                    st.metric("Change %", f"{price_change_pct:+.2f}%")
                
                with col4:
                    st.metric("Period", chart_period)
            else:
                st.error(f"Could not fetch data for {search_ticker}")
        
        # AI ANALYSIS SECTION
        neon_divider("AI-POWERED ANALYSIS")
        
        # AI status
        ai_status = "AI Online" if os.getenv('GEMINI_API_KEY') else "AI Offline"
        pulse_color = "var(--up)" if os.getenv('GEMINI_API_KEY') else "var(--warn)"
        
        st.markdown(f"""
        <div style="text-align:center;margin-bottom:16px">
            <div class="chip" style="display:inline-flex;align-items:center;gap:8px;padding:6px 10px;background:#0F1518;border:1px solid var(--border);border-radius:999px;">
                <span style="width:8px;height:8px;border-radius:50%;background:{pulse_color};box-shadow:0 0 0 0 rgba(0,230,118,.7);animation:pulse 1.6s infinite;"></span>
                <span>{ai_status}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if os.getenv('GEMINI_API_KEY'):
            st.markdown("### 🤖 AI Investment Analysis")
            st.markdown("*AI-powered analysis of top performing stocks*")
            
            # Analyze top 3 stocks
            top_3_tickers = df.head(3).index.tolist()
            
            for i, ticker in enumerate(top_3_tickers):
                with st.expander(f"📊 {ticker} - AI Analysis", expanded=(i==0)):
                    stock_data = df.loc[ticker].to_dict()
                    stock_data['ticker'] = ticker
                    
                    # Get news
                    news_data = fetch_news(ticker, limit=2)
                    
                    # Get AI analysis from backend
                    ai_response = get_ai_analysis(ticker, stock_data, news_data)
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown("**🤖 AI Analysis:**")
                        if ai_response:
                            st.markdown(ai_response.get('analysis', 'AI analysis unavailable'))
                        else:
                            st.info("AI analysis will be provided by backend integration.")
                    
                    with col2:
                        # Risk assessment
                        score = stock_data.get('score', 0)
                        momentum_1m = stock_data.get('momentum_1m', 0)
                        volatility = stock_data.get('volatility', 0)
                        
                        # Risk level calculation
                        risk_score = 0
                        if momentum_1m < -10: risk_score += 3
                        elif momentum_1m < 0: risk_score += 2
                        elif momentum_1m < 5: risk_score += 1
                        
                        if volatility > 30: risk_score += 2
                        elif volatility > 20: risk_score += 1
                        
                        if score < 3: risk_score += 2
                        elif score < 5: risk_score += 1
                        
                        # Risk level
                        if risk_score <= 2:
                            risk_level = "🟢 Low Risk"
                            risk_color = "var(--up)"
                        elif risk_score <= 4:
                            risk_level = "🟡 Medium Risk"
                            risk_color = "var(--warn)"
                        else:
                            risk_level = "🔴 High Risk"
                            risk_color = "var(--down)"
                        
                        # Investment recommendation
                        if score >= 7:
                            recommendation = "🟢 Strong Buy"
                            rec_color = "var(--up)"
                        elif score >= 5:
                            recommendation = "🟡 Buy"
                            rec_color = "var(--warn)"
                        elif score >= 3:
                            recommendation = "⚪ Hold"
                            rec_color = "var(--muted)"
                        else:
                            recommendation = "🔴 Avoid"
                            rec_color = "var(--down)"
                        
                        st.markdown(f"""
                        <div style="margin-bottom:16px;">
                            <div style="font-size:12px;color:var(--muted);margin-bottom:4px;">Risk Level</div>
                            <div style="font-weight:700;color:{risk_color};">{risk_level}</div>
                        </div>
                        <div style="margin-bottom:16px;">
                            <div style="font-size:12px;color:var(--muted);margin-bottom:4px;">Recommendation</div>
                            <div style="font-weight:700;color:{rec_color};">{recommendation}</div>
                        </div>
                        <div style="margin-bottom:16px;">
                            <div style="font-size:12px;color:var(--muted);margin-bottom:4px;">Score</div>
                            <div style="font-weight:700;font-size:18px;">{score:.1f}/10</div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.markdown("### 🤖 AI Analysis Unavailable")
            st.markdown("*Add your Gemini API key to enable AI-powered stock analysis*")
            st.info("💡 **To enable AI features:** Add `GEMINI_API_KEY=your_key_here` to your environment variables")
        
        # METHODOLOGY SECTION
        neon_divider("METHODOLOGY")
        
        st.markdown("### 📊 Scoring Algorithm")
        st.markdown("*Our proprietary 67/33 factor breakdown combines quantitative and qualitative analysis*")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔢 Traditional Factors (67% Weight)")
            st.markdown("""
            **Quantitative Performance Metrics:**
            
            • **1-Month Stock Price Growth** (40% of traditional)
              - Recent momentum and short-term performance
            
            • **3-Month Stock Price Growth** (25% of traditional)
              - Medium-term trend analysis
            
            • **Sharpe Ratio** (15% of traditional)
              - Risk-adjusted returns over 3 months
            
            • **Volume Factor** (10% of traditional)
              - Trading activity and liquidity
            
            • **Market Cap Factor** (10% of traditional)
              - Company size and stability
            """)
        
        with col2:
            st.markdown("#### 🏆 Reputation Factors (33% Weight)")
            st.markdown("""
            **Qualitative Quality Metrics:**
            
            • **P/E Ratio Quality** (40% of reputation)
              - Valuation attractiveness
            
            • **Dividend Yield** (35% of reputation)
              - Income generation potential
            
            • **Beta Stability** (25% of reputation)
              - Market correlation and volatility
            """)
        
        # Score interpretation
        st.markdown("#### 📈 Score Interpretation (0-10 Scale)")
        
        score_cols = st.columns(5)
        
        with score_cols[0]:
            st.markdown("""
            **🟢 Strong Buy (8-10)**
            Excellent performance across all factors
            """)
        
        with score_cols[1]:
            st.markdown("""
            **🟡 Buy (6-8)**
            Good performance, worth considering
            """)
        
        with score_cols[2]:
            st.markdown("""
            **⚪ Hold (4-6)**
            Average performance, monitor closely
            """)
        
        with score_cols[3]:
            st.markdown("""
            **🟠 Sell (2-4)**
            Poor performance, avoid for now
            """)
        
        with score_cols[4]:
            st.markdown("""
            **🔴 Strong Sell (0-2)**
            Very poor performance, strong avoid
            """)
        
        # Performance filters
        st.markdown("#### ⚡ Performance Filters")
        st.markdown("""
        **Strict Quality Controls:**
        
        • **Severe Penalty (-90%)**: 1M growth < -5%
        • **Heavy Penalty (-70%)**: 1M growth < 0%
        • **Moderate Penalty (-30%)**: 1M growth < 2%
        
        *These filters ensure only quality stocks with positive momentum are recommended.*
        """)
        
        # Data sources
        st.markdown("#### 📊 Data Sources")
        st.markdown("""
        **Real-Time Market Data:**
        
        • **Yahoo Finance API**: Historical prices, company info, financial metrics
        • **Auto-Adjustment**: Dividends and splits automatically accounted for
        • **Daily Updates**: Fresh data on every session
        • **500+ Stocks**: Comprehensive universe including US mega-caps and international stocks
        """)

if __name__ == "__main__":
    main()
