#!/usr/bin/env python3
"""
QuantSnap - Simple Stock Analysis API
"""

import os
import logging
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, Query
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="QuantSnap API", version="1.0.0")

class StockAnalyzer:
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.rankings_file = self.data_dir / "stock_rankings.csv"
        
    def get_stock_list(self) -> List[str]:
        """Get list of stocks to analyze"""
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
    
    def update_rankings(self):
        """Update stock rankings"""
        logger.info("Starting stock analysis...")
        
        stocks = self.get_stock_list()
        results = []
        
        for i, ticker in enumerate(stocks, 1):
            logger.info(f"Processing {ticker} ({i}/{len(stocks)})")
            data = self.fetch_stock_data(ticker)
            if data:
                results.append(data)
        
        if results:
            # Create DataFrame and sort by score
            df = pd.DataFrame(results)
            df = df.sort_values('score', ascending=False).reset_index(drop=True)
            
            # Add rank
            df['rank'] = range(1, len(df) + 1)
            
            # Save to CSV
            df.to_csv(self.rankings_file, index=False)
            logger.info(f"Saved {len(df)} stocks to {self.rankings_file}")
            
            return df.to_dict('records')
        else:
            logger.error("No stock data processed")
            return []
    
    def get_rankings(self, limit: int = 10) -> List[Dict]:
        """Get current rankings"""
        if not self.rankings_file.exists():
            logger.info("No rankings file found, updating...")
            return self.update_rankings()[:limit]
        
        try:
            df = pd.read_csv(self.rankings_file)
            return df.head(limit).to_dict('records')
        except Exception as e:
            logger.error(f"Error reading rankings: {e}")
            return self.update_rankings()[:limit]

# Global analyzer
analyzer = StockAnalyzer()

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("QuantSnap API starting up...")
    
    # Update rankings on startup
    logger.info("Updating stock rankings...")
    rankings = analyzer.update_rankings()
    logger.info(f"Updated {len(rankings)} stocks")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "QuantSnap API",
        "version": "1.0.0",
        "description": "Simple stock analysis API",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/rankings/{universe}")
async def get_rankings(
    universe: str = "world_top_stocks",
    limit: int = Query(10, description="Number of stocks to return")
):
    """Get stock rankings"""
    try:
        rankings = analyzer.get_rankings(limit)
        return {
            "universe": universe,
            "count": len(rankings),
            "rankings": rankings
        }
    except Exception as e:
        logger.error(f"Error getting rankings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stock/{ticker}")
async def get_stock_data(ticker: str):
    """Get individual stock data"""
    try:
        data = analyzer.fetch_stock_data(ticker)
        if not data:
            raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
        return data
    except Exception as e:
        logger.error(f"Error getting stock data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/populate")
async def populate_data():
    """Update stock data"""
    try:
        rankings = analyzer.update_rankings()
        return {
            "status": "success",
            "message": f"Updated {len(rankings)} stocks",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error populating data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
