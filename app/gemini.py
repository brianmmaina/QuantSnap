#!/usr/bin/env python3
"""
Gemini AI integration for QuantSnap
"""

import os
import logging
import google.generativeai as genai
from typing import Dict, Optional, List
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class QuotaManager:
    """Manage API quota to stay within free tier limits"""
    
    def __init__(self, daily_limit: int = 45):
        self.daily_limit = daily_limit
        self.requests_today = 0
        self.last_reset = datetime.now().date()
    
    def can_make_request(self) -> bool:
        """Check if we can make a request without exceeding quota"""
        current_date = datetime.now().date()
        
        # Reset counter if it's a new day
        if current_date > self.last_reset:
            self.requests_today = 0
            self.last_reset = current_date
        
        return self.requests_today < self.daily_limit
    
    def record_request(self):
        """Record that a request was made"""
        self.requests_today += 1
        logger.info(f"API requests today: {self.requests_today}/{self.daily_limit}")

class GeminiAI:
    """Gemini AI integration for stock analysis"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.quota_manager = QuotaManager()
        
        if not self.api_key:
            logger.warning("No GEMINI_API_KEY found. AI features will be disabled.")
            self.enabled = False
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self.enabled = True
            logger.info("Gemini AI initialized successfully")
    
    def analyze_stock(self, stock_data: Dict, news_data: Optional[List[Dict]] = None) -> Optional[str]:
        """Analyze a stock using AI"""
        if not self.enabled:
            return "AI analysis disabled - no API key configured"
        
        if not self.quota_manager.can_make_request():
            return "AI analysis quota exceeded for today"
        
        try:
            # Prepare context
            context = self._prepare_analysis_context(stock_data, news_data)
            
            # Generate analysis
            prompt = f"""
            Analyze this stock data and provide a concise, professional analysis:
            
            {context}
            
            Provide a brief analysis covering:
            1. Key performance indicators
            2. Risk assessment
            3. Investment outlook
            
            Keep it under 200 words and focus on actionable insights.
            """
            
            response = self.model.generate_content(prompt)
            self.quota_manager.record_request()
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return f"AI analysis error: {str(e)}"
    
    def _prepare_analysis_context(self, stock_data: Dict, news_data: Optional[List[Dict]] = None) -> str:
        """Prepare context for AI analysis"""
        context = f"""
        Stock: {stock_data.get('ticker', 'N/A')} - {stock_data.get('name', 'N/A')}
        Sector: {stock_data.get('sector', 'N/A')}
        Current Price: ${stock_data.get('price', 0):.2f}
        Market Cap: ${stock_data.get('market_cap', 0):,.0f}
        
        Performance Metrics:
        - 1-Month Stock Price Growth: {stock_data.get('momentum_1m', 0):.2f}%
- 3-Month Stock Price Growth: {stock_data.get('momentum_3m', 0):.2f}%
        - Volatility: {stock_data.get('volatility', 0):.2f}%
        - Sharpe Ratio: {stock_data.get('sharpe_ratio', 0):.2f}
        - Average Volume: {stock_data.get('volume_avg', 0):,.0f}
        - Composite Score: {stock_data.get('score', 0):.3f}
        """
        
        if news_data:
            context += "\n\nRecent News:\n"
            for i, news in enumerate(news_data[:3], 1):
                context += f"{i}. {news.get('title', 'N/A')}\n"
        
        return context
    


# Global AI instance
ai_analyzer = GeminiAI()
