#!/usr/bin/env python3
"""
Streamlit frontend for QuantSnap
"""

import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')

# Page config
st.set_page_config(
    page_title="QuantSnap",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for silver surfer theme
st.markdown("""
<style>
    /* Global styles */
    .main {
        background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
        color: #ffffff;
    }
    .stApp {
        background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
    }
    
    /* Header styling */
    h1 {
        background: linear-gradient(90deg, #c0c0c0, #ffffff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    h2, h3 {
        color: #c0c0c0;
        border-bottom: 2px solid #404040;
        padding-bottom: 0.5rem;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #404040 0%, #606060 100%);
        color: #ffffff;
        border: 1px solid #808080;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #606060 0%, #808080 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    
    /* Card styling */
    .metric-card {
        background: linear-gradient(135deg, #2a2a2a 0%, #3a3a3a 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #404040;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        margin: 0.5rem 0;
    }
    
    .stock-card {
        background: linear-gradient(135deg, #2a2a2a 0%, #3a3a3a 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #404040;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    .stock-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.4);
        border-color: #606060;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background-color: #2a2a2a;
        border: 1px solid #404040;
        color: #ffffff;
        border-radius: 8px;
    }
    
    .stSelectbox > div > div > select {
        background-color: #2a2a2a;
        border: 1px solid #404040;
        color: #ffffff;
        border-radius: 8px;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #1a1a1a 0%, #2a2a2a 100%);
    }
    
    /* Success/Error messages */
    .stSuccess {
        background: linear-gradient(135deg, #2d5a2d 0%, #3a6b3a 100%);
        border: 1px solid #4a7a4a;
        border-radius: 8px;
        padding: 1rem;
    }
    
    .stError {
        background: linear-gradient(135deg, #5a2d2d 0%, #6b3a3a 100%);
        border: 1px solid #7a4a4a;
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Metric styling */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #2a2a2a 0%, #3a3a3a 100%);
        border: 1px solid #404040;
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Chart styling */
    .js-plotly-plot {
        background-color: #2a2a2a !important;
        border-radius: 8px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def api_request(endpoint: str, params: Dict = None) -> Dict:
    """Make API request to backend"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return {}

def get_rankings(universe: str = "popular_stocks", limit: int = 10) -> pd.DataFrame:
    """Get rankings from API"""
    data = api_request(f"/rankings/{universe}", {"limit": limit})
    if data and "rankings" in data:
        return pd.DataFrame(data["rankings"])
    return pd.DataFrame()

def get_stock_data(ticker: str) -> Dict:
    """Get stock data from API"""
    return api_request(f"/stock/{ticker}")

def populate_data():
    """Populate data"""
    try:
        response = requests.post(f"{API_BASE_URL}/populate", timeout=60)
        if response.status_code == 200:
            st.success("✅ Data populated successfully!")
        else:
            st.error("❌ Failed to populate data")
    except Exception as e:
        st.error(f"❌ Error: {e}")

# Main app
def main():
    # Header
    st.title("📈 QuantSnap")
    st.markdown("**AI-Powered Stock Analysis & Ranking**")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Controls")
        
        # Populate button
        if st.button("🚀 Populate Data", type="primary"):
            with st.spinner("Populating data..."):
                populate_data()
        
        st.markdown("---")
        
        # Universe selection
        universe = st.selectbox(
            "Select Universe",
            ["popular_stocks"],
            index=0
        )
        
        # Limit selection
        limit = st.slider("Number of stocks", 5, 20, 10)
        
        # Backend status
        try:
            health = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if health.status_code == 200:
                st.success("🔗 Backend Connected")
            else:
                st.error("🔌 Backend Error")
        except:
            st.error("🔌 Backend Disconnected")
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📊 Stock Rankings")
        
        # Get rankings
        rankings_df = get_rankings(universe, limit)
        
        if not rankings_df.empty:
            # Display rankings
            for _, row in rankings_df.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div class="stock-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="flex: 1;">
                                <h3 style="margin: 0; color: #c0c0c0;">#{row['rank']} - {row['ticker']}</h3>
                                <p style="margin: 0.5rem 0; color: #a0a0a0;">{row['name']}</p>
                                <p style="margin: 0; color: #808080; font-size: 0.9rem;">{row['sector']} • ${row['price']:,.2f}</p>
                            </div>
                            <div style="text-align: right;">
                                <h4 style="margin: 0; color: #ffffff;">Score: {row['score']:.1f}</h4>
                                <p style="margin: 0.5rem 0; color: {'#4CAF50' if row['price_change_1d'] > 0 else '#f44336'}; font-weight: bold;">
                                    {row['price_change_1d']:+.2f}%
                                </p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("📊 No data available. Click 'Populate Data' to load stock rankings.")
    
    with col2:
        st.header("🔍 Stock Analysis")
        
        # Stock search
        ticker = st.text_input("Enter Stock Ticker", "AAPL").upper()
        
        if st.button("Analyze"):
            if ticker:
                with st.spinner(f"Analyzing {ticker}..."):
                    stock_data = get_stock_data(ticker)
                    
                    if stock_data:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3 style="margin: 0 0 1rem 0; color: #c0c0c0;">{ticker} Analysis</h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Key metrics
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"""
                            <div class="metric-card">
                                <h4 style="margin: 0; color: #c0c0c0;">Price</h4>
                                <h2 style="margin: 0.5rem 0; color: #ffffff;">${stock_data['price']:,.2f}</h2>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <div class="metric-card">
                                <h4 style="margin: 0; color: #c0c0c0;">1M Momentum</h4>
                                <h2 style="margin: 0.5rem 0; color: {'#4CAF50' if stock_data['momentum_1m'] > 0 else '#f44336'};">
                                    {stock_data['momentum_1m']:+.2f}%
                                </h2>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown(f"""
                            <div class="metric-card">
                                <h4 style="margin: 0; color: #c0c0c0;">Market Cap</h4>
                                <h2 style="margin: 0.5rem 0; color: #ffffff;">${stock_data['market_cap']/1e9:.1f}B</h2>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <div class="metric-card">
                                <h4 style="margin: 0; color: #c0c0c0;">3M Momentum</h4>
                                <h2 style="margin: 0.5rem 0; color: {'#4CAF50' if stock_data['momentum_3m'] > 0 else '#f44336'};">
                                    {stock_data['momentum_3m']:+.2f}%
                                </h2>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Price chart
                        st.markdown("### Price Performance")
                        fig = go.Figure()
                        fig.add_trace(go.Indicator(
                            mode="gauge+number+delta",
                            value=stock_data['price'],
                            delta={'reference': stock_data['price'] * (1 - stock_data['price_change_1d']/100)},
                            gauge={'axis': {'range': [None, stock_data['price'] * 1.2]},
                                   'bar': {'color': "#c0c0c0"},
                                   'steps': [{'range': [0, stock_data['price']], 'color': "#404040"}],
                                   'threshold': {'line': {'color': "#ffffff", 'width': 4}, 'thickness': 0.75, 'value': stock_data['price']}}))
                        fig.update_layout(
                            height=200,
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font={'color': '#ffffff'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.error(f"❌ Could not fetch data for {ticker}")
    
    # Footer
    st.markdown("---")
    st.markdown("**QuantSnap** - Simple, powerful stock analysis")

if __name__ == "__main__":
    main()
