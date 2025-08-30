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
        """Analyze a stock using AI with comprehensive insights"""
        if not self.enabled:
            return "AI analysis disabled - no API key configured"
        
        if not self.quota_manager.can_make_request():
            return "AI analysis quota exceeded for today"
        
        try:
            # Prepare comprehensive context
            context = self._prepare_analysis_context(stock_data, news_data)
            
            # Enhanced prompt for better analysis
            prompt = f"""
            As a professional financial analyst, provide a comprehensive analysis of this stock:
            
            {context}
            
            Please provide a structured analysis covering:
            
            1. **Performance Summary** (2-3 sentences)
               - Key performance indicators and recent trends
            
            2. **Risk Assessment** (2-3 sentences)
               - Volatility analysis, market position, and potential risks
            
            3. **Investment Outlook** (2-3 sentences)
               - Short-term and medium-term prospects
            
            4. **Recommendation** (1 sentence)
               - Clear buy/hold/sell recommendation with reasoning
            
            Keep the total analysis under 150 words. Be concise but insightful.
            Focus on actionable insights and clear recommendations.
            """
            
            response = self.model.generate_content(prompt)
            self.quota_manager.record_request()
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return f"AI analysis error: {str(e)}"
    
    def get_market_insights(self, top_stocks: List[Dict]) -> Optional[str]:
        """Get AI-powered market insights for top stocks"""
        if not self.enabled:
            return "AI market insights disabled - no API key configured"
        
        if not self.quota_manager.can_make_request():
            return "AI analysis quota exceeded for today"
        
        try:
            # Prepare market context
            market_context = "Top performing stocks:\n"
            for i, stock in enumerate(top_stocks[:5], 1):
                market_context += f"{i}. {stock.get('ticker', 'N/A')}: Score {stock.get('score', 0):.2f}, 1M Growth {stock.get('momentum_1m', 0):.1f}%, 3M Growth {stock.get('momentum_3m', 0):.1f}%\n"
            
            prompt = f"""
            Analyze these top performing stocks and provide market insights:
            
            {market_context}
            
            Provide brief insights on:
            1. Common themes or sectors among top performers
            2. Market trends and patterns
            3. Investment opportunities and risks
            
            Keep it under 100 words and focus on actionable insights.
            """
            
            response = self.model.generate_content(prompt)
            self.quota_manager.record_request()
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error in market insights: {e}")
            return f"Market insights error: {str(e)}"
    
    def analyze_risk_profile(self, stock_data: Dict) -> Dict:
        """Analyze risk profile of a stock"""
        score = stock_data.get('score', 0)
        momentum_1m = stock_data.get('momentum_1m', 0)
        momentum_3m = stock_data.get('momentum_3m', 0)
        volatility = stock_data.get('volatility', 0)
        sharpe_ratio = stock_data.get('sharpe_ratio', 0)
        
        # Risk scoring
        risk_score = 0
        
        # Momentum risk
        if momentum_1m < -10: risk_score += 3
        elif momentum_1m < 0: risk_score += 2
        elif momentum_1m < 5: risk_score += 1
        
        # Volatility risk
        if volatility > 30: risk_score += 3
        elif volatility > 20: risk_score += 2
        elif volatility > 15: risk_score += 1
        
        # Score risk
        if score < 3: risk_score += 3
        elif score < 5: risk_score += 2
        elif score < 7: risk_score += 1
        
        # Sharpe ratio risk
        if sharpe_ratio < 0: risk_score += 2
        elif sharpe_ratio < 1: risk_score += 1
        
        # Risk level classification
        if risk_score <= 2:
            risk_level = "Low"
            risk_description = "Stable performance with low volatility"
        elif risk_score <= 4:
            risk_level = "Medium"
            risk_description = "Moderate risk with balanced performance"
        elif risk_score <= 6:
            risk_level = "High"
            risk_description = "High volatility and performance concerns"
        else:
            risk_level = "Very High"
            risk_description = "Significant risk factors present"
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_description": risk_description,
            "factors": {
                "momentum_risk": momentum_1m < 0,
                "volatility_risk": volatility > 20,
                "score_risk": score < 5,
                "sharpe_risk": sharpe_ratio < 1
            }
        }
    
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
