#!/usr/bin/env python3
"""
Data models for QuantSnap
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class StockData(BaseModel):
    """Stock data model"""
    ticker: str = Field(..., description="Stock ticker symbol")
    name: str = Field(..., description="Company name")
    sector: str = Field(default="Unknown", description="Company sector")
    market_cap: Optional[float] = Field(default=0, description="Market capitalization")
    price: float = Field(..., description="Current stock price")
    momentum_1m: float = Field(..., description="1-month momentum percentage")
    momentum_3m: float = Field(..., description="3-month momentum percentage")
    volatility: float = Field(..., description="30-day volatility percentage")
    volume_avg: float = Field(..., description="20-day average volume")
    sharpe_ratio: float = Field(..., description="3-month Sharpe ratio")
    score: float = Field(..., description="Composite score")
    rank: Optional[int] = Field(default=None, description="Ranking position")
    universe: Optional[str] = Field(default="world_top_stocks", description="Stock universe")
    date: str = Field(..., description="Data timestamp")

class RankingResponse(BaseModel):
    """API response for rankings"""
    universe: str = Field(..., description="Stock universe name")
    count: int = Field(..., description="Number of stocks returned")
    rankings: List[StockData] = Field(..., description="List of ranked stocks")

class StockResponse(BaseModel):
    """API response for individual stock"""
    stock: StockData = Field(..., description="Stock data")

class UniverseResponse(BaseModel):
    """API response for universes"""
    universes: List[str] = Field(..., description="Available universes")

class PopulateResponse(BaseModel):
    """API response for data population"""
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Status message")
    timestamp: str = Field(..., description="Operation timestamp")

class HealthResponse(BaseModel):
    """API health check response"""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Check timestamp")
    message: Optional[str] = Field(default=None, description="Status message")

class RootResponse(BaseModel):
    """API root response"""
    name: str = Field(..., description="API name")
    version: str = Field(..., description="API version")
    description: str = Field(..., description="API description")
    status: str = Field(..., description="Service status")



class AnalysisResponse(BaseModel):
    """Stock analysis response"""
    ticker: str = Field(..., description="Stock ticker")
    stock_data: StockData = Field(..., description="Stock data")
    news: Optional[List[dict]] = Field(default=None, description="Related news")
    ai_analysis: Optional[str] = Field(default=None, description="AI analysis")
    timestamp: str = Field(..., description="Analysis timestamp")
