"""
FastAPI endpoints for AI Daily Draft
Following the basketball scout pattern with specific endpoints
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict
import pandas as pd
from datetime import datetime, timedelta
import logging
import os

from infrastructure.database import StockDatabase, init_database
from core.factors import calculate_all_factors
from core.scoring import rank_tickers, get_default_weights
from core.universe import get_universe
from core.ai_analysis import generate_stock_analysis

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Daily Draft API", version="1.0.0")

# CORS middleware
allowed_origins = ["*"]
if os.getenv('ENVIRONMENT') == 'production':
    # In production, allow specific origins
    allowed_origins = [
        "https://quantsnap-frontend.onrender.com",
        "https://quantsnap.onrender.com",
        "http://localhost:8501"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        init_database()
        logger.info("API started successfully")
    except Exception as e:
        logger.error(f"Failed to start API: {e}")
        raise

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "AI Daily Draft API",
        "version": "1.0.0",
        "description": "Stock analysis and ranking API with reputation factors",
        "endpoints": {
            "/health": "Health check",
            "/universes": "List available universes",
            "/stocks": "Get all stocks",
            "/stocks/{universe}": "Get stocks by universe",
            "/stock/{ticker}": "Get stock data and factors",
            "/rankings/{universe}": "Get rankings for universe",
            "/analysis/{ticker}": "Generate AI analysis for stock"
        }
    }

# Universes endpoint
@app.get("/universes")
async def get_universes():
    """Get list of available universes"""
    universes = [
        {"id": "world_top_stocks", "name": "World Top Stocks", "description": "500+ global stocks"},
        {"id": "sp500", "name": "S&P 500", "description": "S&P 500 Index constituents"},
        {"id": "top_etfs", "name": "Top ETFs", "description": "Popular ETFs for trading"},
        {"id": "popular_stocks", "name": "Popular Stocks", "description": "High-profile individual stocks"}
    ]
    return {"universes": universes}

# Stocks endpoint
@app.get("/stocks")
async def get_all_stocks():
    """Get all stocks from database"""
    try:
        db = StockDatabase()
        query = """
        SELECT ticker, name, sector, industry, market_cap, enterprise_value
        FROM companies
        ORDER BY ticker
        """
        stocks = db.db.read_dataframe(query)
        return {"stocks": stocks.to_dict('records')}
    except Exception as e:
        logger.error(f"Failed to get stocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stocks/{universe}")
async def get_stocks_by_universe(universe: str):
    """Get stocks for specific universe"""
    try:
        # Get universe data
        universe_df = get_universe(universe)
        tickers = universe_df['Ticker'].tolist()
        
        # Get additional data from database
        db = StockDatabase()
        tickers_str = "','".join(tickers)
        query = f"""
        SELECT ticker, name, sector, industry, market_cap, enterprise_value
        FROM companies
        WHERE ticker IN ('{tickers_str}')
        ORDER BY ticker
        """
        stocks = db.db.read_dataframe(query)
        
        return {
            "universe": universe,
            "count": len(stocks),
            "stocks": stocks.to_dict('records')
        }
    except Exception as e:
        logger.error(f"Failed to get stocks for universe {universe}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Individual stock endpoint
@app.get("/stock/{ticker}")
async def get_stock_data(
    ticker: str,
    include_factors: bool = Query(True, description="Include calculated factors"),
    include_rankings: bool = Query(True, description="Include ranking history")
):
    """Get comprehensive stock data"""
    try:
        db = StockDatabase()
        
        # Get company info
        company_query = f"""
        SELECT ticker, name, sector, industry, market_cap, enterprise_value
        FROM companies
        WHERE ticker = '{ticker.upper()}'
        """
        company = db.db.read_dataframe(company_query)
        
        if company.empty:
            raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
        
        result = {"company": company.iloc[0].to_dict()}
        
        # Get latest factors if requested
        if include_factors:
            factors_query = f"""
            SELECT * FROM daily_factors
            WHERE ticker = '{ticker.upper()}'
            AND date = (SELECT MAX(date) FROM daily_factors WHERE ticker = '{ticker.upper()}')
            """
            factors = db.db.read_dataframe(factors_query)
            if not factors.empty:
                result["factors"] = factors.iloc[0].to_dict()
        
        # Get ranking history if requested
        if include_rankings:
            rankings_query = f"""
            SELECT universe, date, rank, score
            FROM daily_rankings
            WHERE ticker = '{ticker.upper()}'
            AND date >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY date DESC
            """
            rankings = db.db.read_dataframe(rankings_query)
            result["rankings"] = rankings.to_dict('records')
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get stock data for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rankings endpoint
@app.get("/rankings/{universe}")
async def get_rankings(
    universe: str,
    limit: int = Query(50, description="Number of top stocks to return"),
    include_factors: bool = Query(True, description="Include factor breakdown")
):
    """Get rankings for universe"""
    try:
        from infrastructure.simple_pipeline import SimpleDataPipeline
        pipeline = SimpleDataPipeline()
        
        # Get latest rankings from CSV
        rankings = pipeline.get_rankings(universe, limit)
        
        if rankings.empty:
            raise HTTPException(status_code=404, detail=f"No rankings found for universe {universe}. Please populate the database first.")
        
        result = {
            "universe": universe,
            "date": rankings['date'].iloc[0].isoformat() if not rankings.empty else None,
            "count": len(rankings),
            "rankings": rankings.to_dict('records')
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get rankings for universe {universe}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# AI Analysis endpoint
@app.get("/analysis/{ticker}")
async def generate_analysis(
    ticker: str,
    include_news: bool = Query(True, description="Include news analysis")
):
    """Generate AI analysis for stock"""
    try:
        db = StockDatabase()
        
        # Get stock data
        stock_data = await get_stock_data(ticker, include_factors=True, include_rankings=False)
        
        if "factors" not in stock_data:
            raise HTTPException(status_code=404, detail=f"No factor data available for {ticker}")
        
        # Generate AI analysis
        factors = stock_data["factors"]
        analysis = generate_stock_analysis(ticker, factors, include_news=include_news)
        
        return {
            "ticker": ticker,
            "analysis": analysis,
            "factors": factors,
            "generated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate analysis for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Data refresh endpoint
@app.post("/refresh/{universe}")
async def refresh_universe_data(universe: str):
    """Refresh data for universe (admin endpoint)"""
    try:
        # This would trigger the data pipeline
        # For now, return success
        return {
            "universe": universe,
            "status": "refresh_initiated",
            "message": f"Data refresh initiated for {universe}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to refresh universe {universe}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Populate database endpoint
@app.post("/populate")
async def populate_database():
    """Populate database with initial stock data"""
    try:
        from infrastructure.data_pipeline import DataPipeline
        
        pipeline = DataPipeline()
        
        # Process popular stocks first (smaller dataset)
        logger.info("Processing popular stocks...")
        pipeline.process_universe('popular_stocks')
        
        logger.info("Processing S&P 500...")
        pipeline.process_universe('sp500')
        
        logger.info("Processing top ETFs...")
        pipeline.process_universe('top_etfs')
        
        logger.info("Processing world top stocks...")
        pipeline.process_universe('world_top_stocks')
        
        return {
            "status": "success",
            "message": "Database populated successfully",
            "universes_processed": ["popular_stocks", "sp500", "top_etfs", "world_top_stocks"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to populate database: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Quick populate endpoint (accurate)
@app.post("/populate/quick")
async def quick_populate_database():
    """Quick populate database with popular stocks using simplified CSV approach"""
    try:
        from infrastructure.simple_pipeline import quick_populate
        result = quick_populate()
        return {
            "status": "success",
            "message": "Popular stocks processed and saved to CSV files",
            "universe_processed": "popular_stocks",
            "approach": "Simplified CSV-based pipeline",
            "timestamp": datetime.now().isoformat(),
            "result": result
        }
    except Exception as e:
        logger.error(f"Failed to quick populate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
