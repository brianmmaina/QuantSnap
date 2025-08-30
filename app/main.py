#!/usr/bin/env python3
"""
QuantSnap - FastAPI Backend
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="QuantSnap AI Service",
    description="AI-powered stock analysis service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class HealthResponse(BaseModel):
    """API health check response"""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Check timestamp")
    message: Optional[str] = Field(default=None, description="Status message")

class StockAnalysisRequest(BaseModel):
    """Request for stock analysis"""
    ticker: str = Field(..., description="Stock ticker symbol")
    stock_data: Dict = Field(..., description="Stock metrics and data")
    news_data: Optional[List[Dict]] = Field(default=None, description="Recent news articles")

class StockAnalysisResponse(BaseModel):
    """AI analysis response"""
    ticker: str = Field(..., description="Stock ticker")
    analysis: str = Field(..., description="AI-generated analysis")
    risk_level: str = Field(..., description="Risk assessment")
    recommendation: str = Field(..., description="Investment recommendation")
    confidence: float = Field(..., description="Analysis confidence score")

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        current_time = datetime.now()
        
        return HealthResponse(
            status="healthy",
            timestamp=current_time.isoformat(),
            message="AI service is ready"
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now().isoformat(),
            message="Health check failed"
        )

# AI Analysis endpoint
@app.post("/analyze", response_model=StockAnalysisResponse)
async def analyze_stock(request: StockAnalysisRequest):
    """Analyze a stock using AI"""
    try:
        # Validate ticker
        ticker = request.ticker.upper().strip()
        if not ticker or len(ticker) > 10:
            raise HTTPException(status_code=400, detail="Invalid ticker symbol")
        
        # Check if Gemini API key is available
        if not os.getenv('GEMINI_API_KEY'):
            raise HTTPException(status_code=503, detail="AI service not configured")
        
        # Import Gemini analyzer
        try:
            from app.gemini import ai_analyzer
        except ImportError:
            raise HTTPException(status_code=503, detail="AI module not available")
        
        # Get AI analysis
        stock_data = request.stock_data
        stock_data['ticker'] = ticker
        
        ai_analysis = ai_analyzer.analyze_stock(stock_data, request.news_data)
        e 
        if not ai_analysis:
            raise HTTPException(status_code=500, detail="AI analysis failed")
        
        # Calculate risk level and recommendation based on data
        score = stock_data.get('score', 0)
        momentum_1m = stock_data.get('momentum_1m', 0)
        volatility = stock_data.get('volatility', 0)
        
        # Risk assessment
        risk_score = 0
        if momentum_1m < -10: risk_score += 3
        elif momentum_1m < 0: risk_score += 2
        elif momentum_1m < 5: risk_score += 1
        
        if volatility > 30: risk_score += 2
        elif volatility > 20: risk_score += 1
        
        if score < 3: risk_score += 2
        elif score < 5: risk_score += 1
        
        # Risk level
        if risk_score <= 2:
            risk_level = "Low Risk"
        elif risk_score <= 4:
            risk_level = "Medium Risk"
        else:
            risk_level = "High Risk"
        
        # Investment recommendation
        if score >= 7:
            recommendation = "Strong Buy"
        elif score >= 5:
            recommendation = "Buy"
        elif score >= 3:
            recommendation = "Hold"
        else:
            recommendation = "Avoid"
        
        # Confidence score (simplified)
        confidence = min(score / 10.0, 1.0)
        
        logger.info(f"Successfully analyzed {ticker}")
        
        return StockAnalysisResponse(
            ticker=ticker,
            analysis=ai_analysis,
            risk_level=risk_level,
            recommendation=recommendation,
            confidence=confidence
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing stock {request.ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "QuantSnap AI Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
