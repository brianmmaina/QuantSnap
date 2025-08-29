#!/usr/bin/env python3
"""
Database management for QuantSnap
"""

import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import yfinance as yf
import numpy as np

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Database files
        self.rankings_file = self.data_dir / "rankings.csv"
        self.stocks_file = self.data_dir / "stocks.csv"
        self.factors_file = self.data_dir / "factors.csv"
        
    def get_stock_universe(self, universe_name: str = "world_top_stocks") -> List[str]:
        """Get stock tickers for a universe"""
        universe_file = self.data_dir / "universes" / f"{universe_name}.csv"
        
        if universe_file.exists():
            try:
                df = pd.read_csv(universe_file)
                return df['Ticker'].tolist()
            except Exception as e:
                logger.error(f"Error reading universe {universe_name}: {e}")
        
        # Fallback to hardcoded list
        return [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "UNH", "JNJ",
            "JPM", "V", "PG", "HD", "MA", "DIS", "PYPL", "ADBE", "CRM", "NFLX", "ABT", "PFE",
            "KO", "PEP", "AVGO", "TMO", "COST", "ABBV", "WMT", "ACN", "DHR", "NEE", "LLY",
            "TXN", "HON", "UNP", "LOW", "SPGI", "ISRG", "GILD", "BMY", "RTX", "QCOM", "AMAT",
            "ADI", "MDLZ", "BKNG", "REGN", "CMCSA", "KLAC", "VRTX", "PANW", "SNPS", "CDNS",
            "MU", "ORCL", "CSCO", "INTC", "IBM", "GE", "CAT", "DE", "BA", "GS", "MS", "BLK",
            "AXP", "C", "WFC", "BAC", "USB", "PNC", "T", "VZ", "CME", "ICE", "AMD", "ZM",
            "SHOP", "SQ", "ROKU", "SPOT", "UBER", "LYFT", "SNAP", "TWTR", "PLTR", "SNOW",
            "CRWD", "ZS", "OKTA", "TEAM", "DOCU", "DDOG", "NET", "MDB", "ESTC", "PATH",
            "RBLX", "COIN", "HOOD", "DASH", "PTON", "BYND", "NIO", "XPEV", "LI", "LCID",
            "RIVN", "BABA", "JD", "PDD", "TCEHY", "NTES", "BILI", "TME", "DIDI"
        ]
    
    def fetch_stock_data(self, ticker: str) -> Optional[Dict]:
        """Fetch and analyze stock data"""
        try:
            # Download data
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            
            if hist.empty or len(hist) < 30:
                logger.warning(f"Insufficient data for {ticker}")
                return None
            
            # Get basic info
            info = stock.info
            current_price = hist['Close'].iloc[-1]
            
            # Calculate metrics
            returns = hist['Close'].pct_change().dropna()
            
            # 1-month momentum
            if len(hist) >= 21:
                momentum_1m = ((current_price / hist['Close'].iloc[-22]) - 1) * 100
            else:
                momentum_1m = 0
            
            # 3-month momentum
            if len(hist) >= 63:
                momentum_3m = ((current_price / hist['Close'].iloc[-64]) - 1) * 100
            else:
                momentum_3m = 0
            
            # Volatility (30-day)
            if len(returns) >= 30:
                volatility = returns.tail(30).std() * 100
            else:
                volatility = returns.std() * 100
            
            # Volume average (20-day)
            if len(hist) >= 20:
                volume_avg = hist['Volume'].tail(20).mean()
            else:
                volume_avg = hist['Volume'].mean()
            
            # Sharpe ratio (3-month)
            if len(returns) >= 63:
                returns_3m = returns.tail(63)
                if returns_3m.std() > 0:
                    sharpe = (returns_3m.mean() / returns_3m.std()) * np.sqrt(252)
                else:
                    sharpe = 0
            else:
                sharpe = 0
            
            # Calculate composite score
            score = (
                momentum_1m * 0.3 +
                momentum_3m * 0.2 +
                sharpe * 0.3 +
                (volume_avg / 1000000) * 0.2  # Normalize volume
            )
            
            return {
                'ticker': ticker,
                'name': info.get('longName', info.get('shortName', ticker)),
                'sector': info.get('sector', 'Unknown'),
                'market_cap': info.get('marketCap', 0),
                'price': round(current_price, 2),
                'momentum_1m': round(momentum_1m, 2),
                'momentum_3m': round(momentum_3m, 2),
                'volatility': round(volatility, 2),
                'volume_avg': round(volume_avg, 0),
                'sharpe_ratio': round(sharpe, 2),
                'score': round(score, 3),
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}")
            return None
    
    def update_rankings(self, universe_name: str = "world_top_stocks") -> List[Dict]:
        """Update stock rankings for a universe"""
        logger.info(f"Updating rankings for universe: {universe_name}")
        
        tickers = self.get_stock_universe(universe_name)
        results = []
        
        for i, ticker in enumerate(tickers, 1):
            logger.info(f"Processing {ticker} ({i}/{len(tickers)})")
            data = self.fetch_stock_data(ticker)
            if data:
                results.append(data)
        
        if results:
            # Create DataFrame and sort by score
            df = pd.DataFrame(results)
            df = df.sort_values('score', ascending=False).reset_index(drop=True)
            
            # Add rank
            df['rank'] = range(1, len(df) + 1)
            df['universe'] = universe_name
            
            # Save to CSV
            df.to_csv(self.rankings_file, index=False)
            logger.info(f"Saved {len(df)} stocks to {self.rankings_file}")
            
            return df.to_dict('records')
        else:
            logger.error("No stock data processed")
            return []
    
    def get_rankings(self, universe_name: str = "world_top_stocks", limit: int = 10) -> List[Dict]:
        """Get current rankings for a universe"""
        if not self.rankings_file.exists():
            logger.info("No rankings file found, updating...")
            return self.update_rankings(universe_name)[:limit]
        
        try:
            df = pd.read_csv(self.rankings_file)
            
            # Filter by universe if specified
            if universe_name != "all":
                df = df[df['universe'] == universe_name]
            
            return df.head(limit).to_dict('records')
        except Exception as e:
            logger.error(f"Error reading rankings: {e}")
            return self.update_rankings(universe_name)[:limit]
    
    def get_stock_data(self, ticker: str) -> Optional[Dict]:
        """Get data for a specific stock"""
        return self.fetch_stock_data(ticker)
    
    def get_all_universes(self) -> List[str]:
        """Get list of available universes"""
        universe_dir = self.data_dir / "universes"
        if universe_dir.exists():
            return [f.stem for f in universe_dir.glob("*.csv")]
        return ["world_top_stocks"]
