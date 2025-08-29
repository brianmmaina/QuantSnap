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

# Import our database and models
from database import Database
from models import (
    RankingResponse, StockResponse, UniverseResponse, 
    PopulateResponse, HealthResponse, RootResponse,
    StockData
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
    
    # Update rankings on startup
    logger.info("Updating stock rankings...")
    rankings = db.update_rankings("world_top_stocks")
    logger.info(f"Updated {len(rankings)} stocks")

@app.get("/", response_model=RootResponse)
async def root():
    """Root endpoint"""
    return RootResponse(
        name="QuantSnap API",
        version="1.0.0",
        description="Quantitative stock analysis API",
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
    """Update stock data"""
    try:
        rankings = db.update_rankings("world_top_stocks")
        return PopulateResponse(
            status="success",
            message=f"Updated {len(rankings)} stocks",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error populating data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/populate/{universe}", response_model=PopulateResponse)
async def populate_universe(universe: str):
    """Update stock data for specific universe"""
    try:
        rankings = db.update_rankings(universe)
        return PopulateResponse(
            status="success",
            message=f"Updated {len(rankings)} stocks for {universe}",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error populating universe {universe}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
