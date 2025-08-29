#!/usr/bin/env python3
"""
Database management for QuantSnap
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Focused stock universe - top stocks only
        self.stocks = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "ADBE", "CRM",
            "ORCL", "INTC", "AMD", "QCOM", "TXN", "AVGO", "MU", "AMAT", "KLAC", "LRCX",
            "ASML", "TSM", "SMCI", "PLTR", "SNOW", "DDOG", "CRWD", "ZS", "OKTA", "NET",
            "SQ", "PYPL", "COIN", "HOOD", "DASH", "UBER", "LYFT", "ZM", "TEAM", "SHOP",
            "WMT", "TGT", "COST", "HD", "LOW", "NKE", "SBUX", "MCD", "DIS", "CMCSA",
            "SPOT", "PINS", "SNAP", "RBLX", "EA", "ATVI", "TTWO", "JPM", "BAC", "WFC",
            "GS", "MS", "C", "AXP", "V", "MA", "UNH", "JNJ", "PFE", "ABBV", "MRK",
            "TMO", "ABT", "DHR", "BMY", "AMGN", "XOM", "CVX", "COP", "EOG", "SLB",
            "KO", "PEP", "PG", "ULTA", "LULU", "UA", "DECK", "SKX", "FL", "JBLU",
            "DAL", "UAL", "AAL", "LUV", "SAVE", "ALK", "HA", "SKYW", "ALGT", "BA",
            "RTX", "LMT", "GD", "NOC", "LHX", "TDG", "AJRD", "KTOS", "TXT", "CAT",
            "DE", "CNH", "AGCO", "TTC", "LNN", "ALG", "WNC", "OSK", "JCI", "EMR",
            "ETN", "ROK", "DOV", "XYL", "AME", "FTV", "ITT", "FLS", "PH", "DHR"
        ]
    
    def get_stock_data(self, ticker: str) -> Optional[Dict]:
        """Get comprehensive stock data directly from yfinance with rate limiting"""
        try:
            # Add delay to prevent rate limiting
            time.sleep(0.1)  # 100ms delay between requests
            
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            info = stock.info
            
            if hist.empty or len(hist) < 30:
                return None
            
            current_price = hist['Close'].iloc[-1]
            returns = hist['Close'].pct_change().dropna()
            
            # Calculate accurate momentum using pandas pct_change
            if len(hist) >= 21:
                momentum_1m = hist['Close'].pct_change(21).iloc[-1] * 100
            else:
                momentum_1m = 0
                
            if len(hist) >= 63:
                momentum_3m = hist['Close'].pct_change(63).iloc[-1] * 100
            else:
                momentum_3m = 0
                
            if len(hist) >= 126:
                momentum_6m = hist['Close'].pct_change(126).iloc[-1] * 100
            else:
                momentum_6m = 0
            
            # Volatility
            volatility_30d = returns.tail(30).std() * 100 if len(returns) >= 30 else returns.std() * 100
            
            # Volume
            volume_avg_20d = hist['Volume'].tail(20).mean() if len(hist) >= 20 else hist['Volume'].mean()
            
            # Sharpe ratio
            if len(returns) >= 63:
                returns_3m = returns.tail(63)
                sharpe_ratio = (returns_3m.mean() / returns_3m.std()) * np.sqrt(252) if returns_3m.std() > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Price changes - get actual daily change
            price_change_1d = hist['Close'].pct_change().iloc[-1] * 100
            price_change_5d = hist['Close'].pct_change(5).iloc[-1] * 100 if len(hist) >= 5 else 0
            
            # Get current vs previous close for actual daily change
            current_price = hist['Close'].iloc[-1]
            previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            daily_change = current_price - previous_close
            daily_change_pct = (daily_change / previous_close) * 100 if previous_close > 0 else 0
            
            # Company info
            company_name = info.get('longName', info.get('shortName', ticker))
            sector = info.get('sector', 'Unknown')
            market_cap = info.get('marketCap', 0)
            
            # Calculate composite score (adjusted for realistic percentages)
            score = (
                (momentum_1m * 2.0) +  # 1M momentum (typically -20% to +30%)
                (momentum_3m * 1.5) +  # 3M momentum (typically -40% to +60%)
                (sharpe_ratio * 5.0) + # Sharpe ratio (typically 0 to 3)
                (volume_avg_20d / 1000000 * 0.1) + # Volume factor
                (market_cap / 1e12 * 0.1) # Market cap factor
            )
            
            return {
                'ticker': ticker,
                'name': company_name,
                'sector': sector,
                'price': round(current_price, 2),
                'momentum_1m': round(momentum_1m, 2),
                'momentum_3m': round(momentum_3m, 2),
                'momentum_6m': round(momentum_6m, 2),
                'volatility': round(volatility_30d, 2),
                'volume_avg': round(volume_avg_20d, 0),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'price_change_1d': round(price_change_1d, 2),
                'price_change_5d': round(price_change_5d, 2),
                'daily_change': round(daily_change, 2),
                'daily_change_pct': round(daily_change_pct, 2),
                'market_cap': market_cap,
                'score': round(score, 3),
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            if "Too Many Requests" in str(e):
                logger.warning(f"Rate limited for {ticker}, skipping...")
            else:
                logger.error(f"Error getting stock data for {ticker}: {e}")
            return None
    
    def get_rankings(self, universe_name: str = "world_top_stocks", limit: int = 10) -> List[Dict]:
        """Get current rankings by fetching fresh data with rate limiting"""
        try:
            rankings = []
            successful_fetches = 0
            
            for ticker in self.stocks:
                data = self.get_stock_data(ticker)
                if data and data['score'] > 0:  # Only include stocks with valid data
                    rankings.append(data)
                    successful_fetches += 1
                    
                    # Stop after getting enough stocks to avoid rate limits
                    if successful_fetches >= limit * 2:  # Get 2x the limit to have options
                        break
            
            # Sort by score (highest first) and add rank
            rankings.sort(key=lambda x: x['score'], reverse=True)
            
            for i, ranking in enumerate(rankings[:limit]):
                ranking['rank'] = i + 1
            
            logger.info(f"Successfully fetched {len(rankings[:limit])} stock rankings")
            return rankings[:limit]
            
        except Exception as e:
            logger.error(f"Error getting rankings: {e}")
            return []
    
    def get_all_universes(self) -> List[str]:
        """Get list of available universes"""
        return ["world_top_stocks"]
    
    def update_all_data(self, universe_name: str = "world_top_stocks") -> List[Dict]:
        """Update all stock data (same as get_rankings for direct approach)"""
        return self.get_rankings(universe_name, limit=50)
