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
    
    def get_portfolio_insights(self, portfolio_data: List[Dict]) -> Optional[str]:
        """Get AI insights for portfolio analysis"""
        if not self.enabled:
            return "AI analysis disabled - no API key configured"
        
        if not self.quota_manager.can_make_request():
            return "AI analysis quota exceeded for today"
        
        try:
            # Prepare portfolio context
            context = self._prepare_portfolio_context(portfolio_data)
            
            prompt = f"""
            Analyze this portfolio and provide insights:
            
            {context}
            
            Provide brief insights on:
            1. Portfolio diversification
            2. Risk assessment
            3. Potential improvements
            
            Keep it under 150 words.
            """
            
            response = self.model.generate_content(prompt)
            self.quota_manager.record_request()
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error in portfolio AI analysis: {e}")
            return f"AI analysis error: {str(e)}"
    
    def _prepare_portfolio_context(self, portfolio_data: List[Dict]) -> str:
        """Prepare portfolio context for AI analysis"""
        if not portfolio_data:
            return "No portfolio data available"
        
        context = f"Portfolio Analysis ({len(portfolio_data)} stocks):\n\n"
        
        total_score = sum(stock.get('score', 0) for stock in portfolio_data)
        avg_score = total_score / len(portfolio_data) if portfolio_data else 0
        
        sectors = {}
        for stock in portfolio_data:
            sector = stock.get('sector', 'Unknown')
            sectors[sector] = sectors.get(sector, 0) + 1
        
        context += f"Average Score: {avg_score:.3f}\n"
        context += f"Top Sectors: {', '.join(list(sectors.keys())[:3])}\n\n"
        
        context += "Top Holdings:\n"
        for i, stock in enumerate(portfolio_data[:5], 1):
            context += f"{i}. {stock.get('ticker', 'N/A')} - Score: {stock.get('score', 0):.3f}\n"
        
        return context
    
    def get_market_insights(self, market_data: Dict) -> Optional[str]:
        """Get AI insights for overall market analysis"""
        if not self.enabled:
            return "AI analysis disabled - no API key configured"
        
        if not self.quota_manager.can_make_request():
            return "AI analysis quota exceeded for today"
        
        try:
            context = f"""
            Market Overview:
            - Top performing stocks: {market_data.get('top_performers', [])}
            - Market sentiment indicators
            - Sector performance trends
            """
            
            prompt = f"""
            Provide a brief market analysis based on this data:
            
            {context}
            
            Focus on:
            1. Market trends
            2. Sector opportunities
            3. Risk factors
            
            Keep it under 150 words.
            """
            
            response = self.model.generate_content(prompt)
            self.quota_manager.record_request()
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error in market AI analysis: {e}")
            return f"AI analysis error: {str(e)}"

# Global AI instance
ai_analyzer = GeminiAI()
