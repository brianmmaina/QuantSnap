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
    
    def get_world_top_stocks(self) -> List[str]:
        """Get world top stock tickers"""
        return [
            # US Mega Caps
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "UNH", "JNJ",
            "V", "PG", "HD", "MA", "DIS", "PYPL", "BAC", "ADBE", "CRM", "NFLX",
            "ABT", "KO", "PFE", "TMO", "AVGO", "COST", "ABBV", "WMT", "ACN", "DHR",
            "NEE", "LLY", "TXN", "QCOM", "UNP", "HON", "RTX", "LOW", "UPS", "SPGI",
            "INTU", "ISRG", "GILD", "ADI", "AMAT", "TGT", "SBUX", "PLD", "REGN", "MDLZ",
            "VRTX", "KLAC", "PANW", "SNPS", "CDNS", "MELI", "ASML", "ORLY", "MNST", "CHTR",
            "MAR", "ADP", "CPRT", "PAYX", "ROST", "ODFL", "FAST", "IDXX", "BIIB", "DXCM",
            "ALGN", "CTAS", "WDAY", "CTSH", "VRSK", "EXC", "PCAR", "MCHP", "XEL", "EA",
            "WBD", "ILMN", "ZS", "CRWD", "FTNT", "NET", "SNOW", "DDOG", "ZM", "TEAM",
            "PLTR", "PATH", "RBLX", "HOOD", "COIN", "SNAP", "SPOT", "UBER", "LYFT", "DASH",
            "SQ", "SHOP", "ROKU", "ZM", "PTON", "BYND", "NIO", "XPEV", "LI", "LCID",
            "RIVN", "TSLA", "AMD", "NVDA", "INTC", "QCOM", "AVGO", "MU", "AMAT", "KLAC",
            "LRCX", "ASML", "TSM", "UMC", "SMIC", "GFS", "ARM", "NVDA", "AMD", "INTC",
            # International Stocks
            "NFLX", "META", "GOOGL", "AMZN", "TSLA", "NVDA", "AMD", "AAPL", "MSFT", "CRM",
            "ADBE", "PYPL", "UBER", "SPOT", "SQ", "ZM", "SHOP", "ROKU", "SNAP", "PLTR",
            "COIN", "RBLX", "HOOD", "DASH", "LYFT", "PTON", "BYND", "NIO", "XPEV", "LI",
            "LCID", "RIVN", "TSLA", "AMD", "NVDA", "INTC", "QCOM", "AVGO", "MU", "AMAT",
            "KLAC", "LRCX", "ASML", "TSM", "UMC", "SMIC", "GFS", "ARM", "NVDA", "AMD", "INTC",
            # Add more international stocks
            "BABA", "JD", "PDD", "TCEHY", "NIO", "XPEV", "LI", "BIDU", "NTES", "TME",
            "DIDI", "XNET", "ZTO", "YUMC", "TCOM", "HTHT", "ZTO", "YUMC", "TCOM", "HTHT",
            "ASML", "NOVO-B", "NOVO-N", "SAP", "ASML", "NOVO-B", "NOVO-N", "SAP", "ASML", "NOVO-B",
            "NOVO-N", "SAP", "ASML", "NOVO-B", "NOVO-N", "SAP", "ASML", "NOVO-B", "NOVO-N", "SAP",
            # Add more to reach 500
            "TSLA", "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "NFLX", "AMD", "CRM",
            "ADBE", "PYPL", "UBER", "SPOT", "SQ", "ZM", "SHOP", "ROKU", "SNAP", "PLTR",
            "COIN", "RBLX", "HOOD", "DASH", "LYFT", "PTON", "BYND", "NIO", "XPEV", "LI",
            "LCID", "RIVN", "TSLA", "AMD", "NVDA", "INTC", "QCOM", "AVGO", "MU", "AMAT",
            "KLAC", "LRCX", "ASML", "TSM", "UMC", "SMIC", "GFS", "ARM", "NVDA", "AMD", "INTC"
        ]
    
    def calculate_factors(self, ticker: str) -> Optional[Dict]:
        """Calculate factors for a stock"""
        try:
            # Fetch data
            data = yf.download(ticker, period="1y", interval="1d", auto_adjust=True, progress=False)
            if data.empty or len(data) < 65:
                logger.warning(f"Insufficient data for {ticker}: {len(data)} rows")
                return None
            
            # Validate required columns exist
            required_columns = ['Close', 'Volume']
            if not all(col in data.columns for col in required_columns):
                logger.warning(f"Missing required columns for {ticker}")
                return None
            
            # Calculate factors
            close_prices = data['Close']
            volume = data['Volume']
            returns = close_prices.pct_change().dropna()
            
            # Handle NaN values and calculate accurate metrics
            try:
                momentum_1m = close_prices.pct_change(21).iloc[-1] * 100
            except:
                momentum_1m = 0.0
                
            try:
                momentum_3m = close_prices.pct_change(63).iloc[-1] * 100
            except:
                momentum_3m = 0.0
                
            try:
                volatility_30d = returns.rolling(30).std().iloc[-1] * 100
            except:
                volatility_30d = 0.0
                
            try:
                volume_avg = volume.rolling(20).mean().iloc[-1]
            except:
                volume_avg = 0.0
                
            try:
                price = close_prices.iloc[-1]
            except:
                price = 0.0
                
            try:
                price_change_1d = close_prices.pct_change().iloc[-1] * 100
            except:
                price_change_1d = 0.0
                
            try:
                price_change_5d = close_prices.pct_change(5).iloc[-1] * 100
            except:
                price_change_5d = 0.0
            
            # Calculate Sharpe Ratio (3-month)
            try:
                returns_3m = close_prices.pct_change(63).dropna()
                if len(returns_3m) > 0:
                    std_dev = returns_3m.std()
                    if std_dev > 0:
                        sharpe_ratio = (returns_3m.mean() / std_dev) * np.sqrt(252)
                    else:
                        sharpe_ratio = 0
                else:
                    sharpe_ratio = 0
            except:
                sharpe_ratio = 0
            
            # Helper function to safely handle NaN values
            def safe_round(value, decimals=2):
                try:
                    # Handle None values
                    if value is None:
                        return 0.0
                    
                    # Convert to float and check for NaN
                    float_value = float(value)
                    if float_value != float_value:  # NaN check (NaN != NaN)
                        return 0.0
                    
                    return round(float_value, decimals)
                except (ValueError, TypeError, AttributeError):
                    return 0.0
            
            factors = {
                'ticker': ticker,
                'momentum_1m': safe_round(momentum_1m, 2),
                'momentum_3m': safe_round(momentum_3m, 2),
                'volatility_30d': safe_round(volatility_30d, 2),
                'volume_avg': safe_round(volume_avg, 0),
                'price': safe_round(price, 2),
                'price_change_1d': safe_round(price_change_1d, 2),
                'price_change_5d': safe_round(price_change_5d, 2),
                'sharpe_ratio': safe_round(sharpe_ratio, 2),
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
        
        tickers = self.get_world_top_stocks()
        results = []
        
        for ticker in tickers:
            try:
                # Get factors
                factors = self.calculate_factors(ticker)
                if factors:
                    # Get company info
                    company_info = self.get_company_info(ticker)
                    factors.update(company_info)
                    
                                                # Calculate comprehensive score
                    momentum_score = (factors['momentum_1m'] * 0.5 + factors['momentum_3m'] * 0.3) / 100
                    sharpe_score = min(factors['sharpe_ratio'] / 3.0, 1.0)  # Normalize Sharpe ratio
                    volume_score = min(factors['volume_avg'] / 10000000, 1.0)  # Normalize volume
                    
                    score = (
                        momentum_score * 0.5 +
                        sharpe_score * 0.3 +
                        volume_score * 0.2
                    )
                    factors['score'] = round(score, 3)
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
    """Initialize on startup and auto-populate data"""
    logger.info("QuantSnap API starting up...")
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    logger.info(f"Data directory: {data_dir.absolute()}")
    
    # Auto-populate data on startup
    logger.info("Auto-populating data on startup...")
    try:
        rankings = data_store.process_universe("world_top_stocks")
        logger.info(f"Auto-populated {len(rankings)} stocks on startup")
    except Exception as e:
        logger.error(f"Error auto-populating data: {e}")

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
        rankings = data_store.process_universe("world_top_stocks")
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
