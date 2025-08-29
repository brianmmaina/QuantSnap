#!/usr/bin/env python3
"""
FastAPI backend for QuantSnap
"""

import os
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
import logging
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="QuantSnap API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:8501"),
        "https://quantsnap-frontend.onrender.com",
        "https://quantsnap.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Content-Type", 
        "Authorization",
        "X-Requested-With",
        "X-CSRF-Token",
        "Cache-Control",
    ],
    max_age=3600
)

# Data storage (in-memory with CSV backup)
class DataStore:
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.cache = {}
    
    def get_popular_stocks(self) -> List[str]:
        """Get popular stock tickers"""
        return [
            "TSLA", "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "NFLX", 
            "AMD", "CRM", "ADBE", "PYPL", "UBER", "SPOT", "SQ", "ZM", 
            "SHOP", "ROKU", "SNAP", "PLTR", "COIN", "RBLX", "HOOD"
        ]
    
    def calculate_factors(self, ticker: str) -> Optional[Dict]:
        """Calculate factors for a stock"""
        try:
            # Fetch data
            data = yf.download(ticker, period="1y", interval="1d", auto_adjust=True, progress=False)
            if data.empty or len(data) < 65:
                return None
            
            # Calculate factors
            close_prices = data['Close']
            volume = data['Volume']
            returns = close_prices.pct_change().dropna()
            
            factors = {
                'ticker': ticker,
                'momentum_1m': float(close_prices.pct_change(21).iloc[-1] * 100),
                'momentum_3m': float(close_prices.pct_change(63).iloc[-1] * 100),
                'volatility_30d': float(returns.rolling(30).std().iloc[-1] * 100),
                'volume_avg': float(volume.rolling(20).mean().iloc[-1]),
                'price': float(close_prices.iloc[-1]),
                'price_change_1d': float(close_prices.pct_change().iloc[-1] * 100),
                'price_change_5d': float(close_prices.pct_change(5).iloc[-1] * 100),
                'date': datetime.now().isoformat()
            }
            
            return factors
            
        except Exception as e:
            logger.error(f"Error calculating factors for {ticker}: {e}")
            return None
    
    def get_company_info(self, ticker: str) -> Dict:
        """Get company information"""
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            
            return {
                'ticker': ticker,
                'name': info.get('longName', info.get('shortName', ticker)),
                'sector': info.get('sector', 'Unknown'),
                'market_cap': info.get('marketCap', 0)
            }
        except Exception as e:
            logger.warning(f"Error fetching company info for {ticker}: {e}")
            return {
                'ticker': ticker,
                'name': ticker,
                'sector': 'Unknown',
                'market_cap': 0
            }
    
    def process_universe(self, universe_name: str = "popular_stocks") -> List[Dict]:
        """Process universe and return rankings"""
        cache_key = f"rankings_{universe_name}"
        
        # Check cache
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        logger.info(f"Processing universe: {universe_name}")
        
        tickers = self.get_popular_stocks()
        results = []
        
        for ticker in tickers:
            try:
                # Get factors
                factors = self.calculate_factors(ticker)
                if factors:
                    # Get company info
                    company_info = self.get_company_info(ticker)
                    factors.update(company_info)
                    
                                                # Calculate score (momentum + volume)
                    score = (
                        factors['momentum_1m'] * 0.4 +
                        factors['momentum_3m'] * 0.3 +
                        (factors['volume_avg'] / 1000000) * 0.3  # Normalize volume
                    )
                    factors['score'] = round(score, 2)
                    results.append(factors)
                
            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
                continue
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Add rank
        for i, result in enumerate(results):
            result['rank'] = i + 1
        
        # Cache results
        self.cache[cache_key] = results
        
        # Save to CSV
        try:
            df = pd.DataFrame(results)
            csv_file = self.data_dir / f"{universe_name}_rankings.csv"
            df.to_csv(csv_file, index=False)
            logger.info(f"Saved rankings to {csv_file}")
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
        
        return results

# Global data store
data_store = DataStore()

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("QuantSnap API starting up...")
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    logger.info(f"Data directory: {data_dir.absolute()}")

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
    universe: str = "popular_stocks",
    limit: int = Query(10, description="Number of stocks to return")
):
    """Get stock rankings"""
    try:
        rankings = data_store.process_universe(universe)
        return {
            "universe": universe,
            "count": len(rankings),
            "rankings": rankings[:limit]
        }
    except Exception as e:
        logger.error(f"Error getting rankings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stock/{ticker}")
async def get_stock_data(ticker: str):
    """Get individual stock data"""
    try:
        factors = data_store.calculate_factors(ticker)
        if not factors:
            raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
        
        company_info = data_store.get_company_info(ticker)
        factors.update(company_info)
        
        return factors
    except Exception as e:
        logger.error(f"Error getting stock data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/populate")
async def populate_data():
    """Populate data (simple version)"""
    try:
        rankings = data_store.process_universe("popular_stocks")
        return {
            "status": "success",
            "message": f"Processed {len(rankings)} stocks",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error populating data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
