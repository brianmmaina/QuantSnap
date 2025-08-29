#!/usr/bin/env python3
"""
QuantSnap - FastAPI Backend
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

# Import our modules
from database import Database
from gemini import ai_analyzer
from scraper import news_scraper, data_scraper
from models import (
    RankingResponse, StockResponse, UniverseResponse, 
    PopulateResponse, HealthResponse, RootResponse,
    AnalysisResponse, StockData
)

# Load environment variables
load_dotenv()

# Configure logging
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

# Global database instance
db = Database()

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("QuantSnap API starting up...")
    
    # Update all data on startup
    logger.info("Updating all stock data with yfinance...")
    rankings = db.update_all_data("world_top_stocks")
    logger.info(f"Updated {len(rankings)} stocks with enhanced yfinance data")

@app.get("/", response_model=RootResponse)
async def root():
    """Root endpoint"""
    return RootResponse(
        name="QuantSnap API",
        version="1.0.0",
        description="Quantitative stock analysis API with 67/33 factor breakdown",
        status="running"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check"""
    return HealthResponse(
        status="healthy", 
        timestamp=datetime.now().isoformat()
    )

@app.get("/rankings/{universe}", response_model=RankingResponse)
async def get_rankings(
    universe: str = "world_top_stocks",
    limit: int = Query(10, description="Number of stocks to return")
):
    """Get stock rankings for a universe"""
    try:
        rankings = db.get_rankings(universe, limit)
        return RankingResponse(
            universe=universe,
            count=len(rankings),
            rankings=rankings
        )
    except Exception as e:
        logger.error(f"Error getting rankings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stock/{ticker}", response_model=StockResponse)
async def get_stock_data(ticker: str):
    """Get individual stock data"""
    try:
        data = db.get_stock_data(ticker)
        if not data:
            raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
        return StockResponse(stock=data)
    except Exception as e:
        logger.error(f"Error getting stock data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stock/{ticker}/analysis", response_model=AnalysisResponse)
async def analyze_stock(ticker: str):
    """Get comprehensive stock analysis with AI and news"""
    try:
        # Get stock data
        stock_data = db.get_stock_data(ticker)
        if not stock_data:
            raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
        
        # Get news
        news_data = news_scraper.fetch_stock_news(ticker, limit=3)
        
        # Get AI analysis
        ai_analysis = ai_analyzer.analyze_stock(stock_data, news_data)
        
        return AnalysisResponse(
            ticker=ticker,
            stock_data=stock_data,
            news=news_data,
            ai_analysis=ai_analysis,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error analyzing stock {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/factors/traditional")
async def get_traditional_factors():
    """Get traditional factors data (67% weight)"""
    try:
        import pandas as pd
        factors_file = db.traditional_factors_file
        if factors_file.exists():
            df = pd.read_csv(factors_file)
            return {
                "factors": df.to_dict('records'),
                "count": len(df),
                "weight": "67%",
                "description": "Traditional quantitative factors including stock price growth, volatility, volume, and Sharpe ratio",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Traditional factors not found")
    except Exception as e:
        logger.error(f"Error getting traditional factors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/factors/reputation")
async def get_reputation_factors():
    """Get reputation factors data (33% weight)"""
    try:
        import pandas as pd
        factors_file = db.reputation_factors_file
        if factors_file.exists():
            df = pd.read_csv(factors_file)
            return {
                "factors": df.to_dict('records'),
                "count": len(df),
                "weight": "33%",
                "description": "Reputation factors including financial health, market position, and growth stability",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Reputation factors not found")
    except Exception as e:
        logger.error(f"Error getting reputation factors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/factors/breakdown")
async def get_factor_breakdown():
    """Get factor breakdown explanation"""
    return {
        "traditional_factors": {
            "weight": "67%",
            "components": {
                        "momentum_1m": "30% - 1-month stock price growth",
        "momentum_3m": "25% - 3-month stock price growth", 
                "sharpe_ratio": "25% - Risk-adjusted returns",
                "volume": "10% - Trading volume",
                "volatility": "10% - Price volatility (inverse)"
            },
            "description": "Quantitative market performance indicators"
        },
        "reputation_factors": {
            "weight": "33%",
            "components": {
                "financial_health": "40% - Debt ratios, ROE, ROA",
                "market_position": "30% - Market cap, valuation ratios",
                "growth_stability": "30% - Revenue growth, margins, dividends"
            },
            "description": "Company fundamentals and stability indicators"
        },
        "composite_score": "Combined weighted score for final ranking"
    }

@app.get("/news/market")
async def get_market_news():
    """Get general market news"""
    try:
        news = news_scraper.fetch_market_news(limit=5)
        return {
            "news": news,
            "count": len(news),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching market news: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/news/{ticker}")
async def get_stock_news(ticker: str, limit: int = Query(5, description="Number of news items")):
    """Get news for a specific stock"""
    try:
        news = news_scraper.fetch_stock_news(ticker, limit)
        return {
            "ticker": ticker,
            "news": news,
            "count": len(news),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sentiment/market")
async def get_market_sentiment():
    """Get market sentiment indicators"""
    try:
        sentiment = data_scraper.get_market_sentiment()
        return sentiment
    except Exception as e:
        logger.error(f"Error getting market sentiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sectors/performance")
async def get_sector_performance():
    """Get sector performance data"""
    try:
        sectors = data_scraper.scrape_sector_performance()
        return {
            "sectors": sectors,
            "count": len(sectors),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting sector performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/prices/live")
async def get_live_prices(tickers: str = Query(..., description="Comma-separated list of tickers")):
    """Get live prices for multiple stocks"""
    try:
        ticker_list = [t.strip().upper() for t in tickers.split(',')]
        price_data = db.get_live_prices(ticker_list)
        
        return {
            "prices": price_data,
            "count": len(price_data),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting live prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chart/{ticker}")
async def get_chart_data(ticker: str, period: str = Query("1y", description="Chart period")):
    """Get chart data for a stock"""
    try:
        chart_data = db.get_chart_data(ticker, period)
        
        if not chart_data:
            raise HTTPException(status_code=404, detail=f"No data found for {ticker}")
        
        return chart_data
    except Exception as e:
        logger.error(f"Error getting chart data for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/universes", response_model=UniverseResponse)
async def get_universes():
    """Get available universes"""
    try:
        universes = db.get_all_universes()
        return UniverseResponse(universes=universes)
    except Exception as e:
        logger.error(f"Error getting universes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/populate", response_model=PopulateResponse)
async def populate_data():
    """Update all stock data"""
    try:
        rankings = db.update_all_data("world_top_stocks")
        return PopulateResponse(
            status="success",
            message=f"Updated {len(rankings)} stocks with 67/33 factor breakdown",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error populating data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/populate/{universe}", response_model=PopulateResponse)
async def populate_universe(universe: str):
    """Update stock data for specific universe"""
    try:
        rankings = db.update_all_data(universe)
        return PopulateResponse(
            status="success",
            message=f"Updated {len(rankings)} stocks for {universe} with 67/33 factor breakdown",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error populating universe {universe}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
