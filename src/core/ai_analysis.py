"""
AI analysis functions using Google Gemini
"""

import os
import google.generativeai as genai
import pandas as pd
from typing import Dict, List, Optional
import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Quota management for free tier (50 requests per day)
class QuotaManager:
    def __init__(self):
        self.daily_requests = 0
        self.last_reset = datetime.now().date()
        self.max_daily_requests = 45  # Leave some buffer for safety
    
    def can_make_request(self):
        current_date = datetime.now().date()
        if current_date != self.last_reset:
            self.daily_requests = 0
            self.last_reset = current_date
        
        return self.daily_requests < self.max_daily_requests
    
    def record_request(self):
        self.daily_requests += 1
    
    def get_remaining_requests(self):
        return max(0, self.max_daily_requests - self.daily_requests)

# Global quota manager
quota_manager = QuotaManager()

def get_quota_status():
    """Get current quota status"""
    return {
        'remaining': quota_manager.get_remaining_requests(),
        'used': quota_manager.daily_requests,
        'max': quota_manager.max_daily_requests
    }


def setup_gemini():
    """Setup Gemini AI"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.warning("GEMINI_API_KEY not found. AI features will be disabled.")
        return None
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model
    except Exception as e:
        logger.error(f"Failed to setup Gemini: {e}")
        return None


def _generate_fallback_analysis(ticker: str, factors: Dict[str, float], company_name: str = "") -> Dict[str, str]:
    """Generate fallback analysis when AI is unavailable"""
    
    # Calculate basic metrics
    score = factors.get('Score', 0)
    mom_1m = factors.get('MOM_1M', 0)
    mom_3m = factors.get('MOM_3M', 0)
    sharpe = factors.get('Sharpe_3M', 0)
    volatility = factors.get('Vol_30d', 0)
    
    # Determine sentiment based on factors
    if score > 1.0:
        sentiment = "very bullish"
        recommendation = "Strong Buy"
    elif score > 0.5:
        sentiment = "bullish"
        recommendation = "Buy"
    elif score > 0:
        sentiment = "neutral"
        recommendation = "Hold"
    else:
        sentiment = "bearish"
        recommendation = "Sell"
    
    # Generate analysis
    overall = f"""
    {ticker} ({company_name or ticker}) shows {sentiment} signals based on quantitative analysis.
    
    Key Metrics:
    • AI Score: {score:.3f}
    • 1-Month Return: {mom_1m:.1%}
    • 3-Month Return: {mom_3m:.1%}
    • Sharpe Ratio: {sharpe:.2f}
    • Volatility: {volatility:.1%}
    
    The stock demonstrates {'strong' if sharpe > 2 else 'moderate' if sharpe > 1 else 'weak'} risk-adjusted returns.
    """
    
    factor_analysis = f"""
    Factor Breakdown:
    
    Momentum (1M): {mom_1m:.1%} - {'Strong positive momentum' if mom_1m > 0.05 else 'Moderate momentum' if mom_1m > 0 else 'Negative momentum'}
    Momentum (3M): {mom_3m:.1%} - {'Excellent long-term trend' if mom_3m > 0.15 else 'Good trend' if mom_3m > 0.05 else 'Weak trend'}
    Sharpe Ratio: {sharpe:.2f} - {'Excellent risk-adjusted returns' if sharpe > 2 else 'Good returns' if sharpe > 1 else 'Poor risk-adjusted returns'}
    Volatility: {volatility:.1%} - {'Low volatility' if volatility < 0.02 else 'Moderate volatility' if volatility < 0.04 else 'High volatility'}
    """
    
    risk_assessment = f"""
    Risk Profile:
    
    • Volatility Risk: {'Low' if volatility < 0.02 else 'Moderate' if volatility < 0.04 else 'High'}
    • Momentum Risk: {'Low' if mom_1m > 0 and mom_3m > 0 else 'Moderate' if mom_1m > 0 or mom_3m > 0 else 'High'}
    • Risk-Adjusted Performance: {'Excellent' if sharpe > 2 else 'Good' if sharpe > 1 else 'Poor'}
    
    Overall Risk Level: {'Low' if score > 0.8 and sharpe > 1.5 else 'Moderate' if score > 0.3 else 'High'}
    """
    
    investment_rec = f"""
    Investment Recommendation: {recommendation}
    
    Rationale:
    • Quantitative Score: {score:.3f} ({sentiment})
    • Risk-Adjusted Returns: {'Strong' if sharpe > 2 else 'Moderate' if sharpe > 1 else 'Weak'}
    • Momentum: {'Positive' if mom_1m > 0 and mom_3m > 0 else 'Mixed' if mom_1m > 0 or mom_3m > 0 else 'Negative'}
    
    Consider this stock for {'aggressive' if score > 1.0 else 'moderate' if score > 0.5 else 'conservative'} portfolios.
    """
    
    market_context = f"""
    Market Context:
    
    • Current Performance: {mom_1m:.1%} over 1 month, {mom_3m:.1%} over 3 months
    • Risk Level: {'Below average' if volatility < 0.02 else 'Average' if volatility < 0.04 else 'Above average'} volatility
    • Efficiency: {'High' if sharpe > 2 else 'Moderate' if sharpe > 1 else 'Low'} risk-adjusted efficiency
    
    This analysis is based on quantitative factors and should be combined with fundamental analysis.
    """
    
    return {
        'overall': overall,
        'factors': factor_analysis,
        'risk': risk_assessment,
        'recommendation': investment_rec,
        'market_context': market_context
    }


def generate_stock_analysis(
    ticker: str,
    factors: Dict[str, float],
    price_data: pd.Series,
    company_name: str = ""
) -> Dict[str, str]:
    """
    Generate comprehensive AI analysis for a stock
    
    Args:
        ticker: Stock ticker
        factors: Factor values
        price_data: Historical price data
        company_name: Company name
        
    Returns:
        Dictionary with analysis sections
    """
    # Check quota before making any AI requests
    if not quota_manager.can_make_request():
        logger.warning(f"Daily AI quota exceeded. Using fallback analysis for {ticker}")
        return _generate_fallback_analysis(ticker, factors, company_name)
    
    model = setup_gemini()
    if not model:
        return _generate_fallback_analysis(ticker, factors, company_name)
    
    try:
        # Prepare context
        # Prepare price data summary
        if price_data is not None and len(price_data) > 0:
            current_price = f"${price_data.iloc[-1]:.2f}"
            if len(price_data) >= 30:
                price_range = f"${price_data.tail(30).min():.2f} - ${price_data.tail(30).max():.2f}"
                price_change = f"{((price_data.iloc[-1] / price_data.iloc[-30]) - 1):.2%}"
            else:
                price_range = "N/A"
                price_change = "N/A"
        else:
            current_price = "N/A"
            price_range = "N/A"
            price_change = "N/A"
        
        context = f"""
        TICKER: {ticker}
        COMPANY: {company_name or ticker}
        
        FACTOR VALUES:
        - Score: {factors.get('Score', 0):.3f}
        - 1M Return: {factors.get('MOM_1M', 0):.2%}
        - 3M Return: {factors.get('MOM_3M', 0):.2%}
        - Sharpe Ratio: {factors.get('Sharpe_3M', 0):.2f}
        - Volatility: {factors.get('Vol_30d', 0):.2%}
        - Price Trend: {factors.get('Slope_50d', 0):.4f}
        - Dollar Volume: ${factors.get('DollarVol_20d', 0):,.0f}
        
        PRICE DATA SUMMARY:
        - Current Price: {current_price}
        - 30-day Range: {price_range}
        - 30-day Change: {price_change}
        """
        
        # Generate analysis sections
        analysis = {}
        
        # Overall Assessment
        if quota_manager.can_make_request():
            overall_prompt = f"{context}\n\nTASK: Provide a concise overall assessment of this stock's investment potential based on the quantitative factors."
            try:
                quota_manager.record_request()
                response = model.generate_content(overall_prompt)
                analysis['overall'] = response.text
            except Exception as e:
                logger.warning(f"AI overall assessment failed: {e}")
                analysis['overall'] = _generate_fallback_analysis(ticker, factors, company_name)['overall']
        else:
            analysis['overall'] = _generate_fallback_analysis(ticker, factors, company_name)['overall']
        
        # Factor Analysis
        if quota_manager.can_make_request():
            factor_prompt = f"{context}\n\nTASK: Analyze the factor values and explain what they mean for this stock."
            try:
                quota_manager.record_request()
                response = model.generate_content(factor_prompt)
                analysis['factors'] = response.text
            except Exception as e:
                logger.warning(f"AI factor analysis failed: {e}")
                analysis['factors'] = _generate_fallback_analysis(ticker, factors, company_name)['factors']
        else:
            analysis['factors'] = _generate_fallback_analysis(ticker, factors, company_name)['factors']
        
        # Risk Assessment
        if quota_manager.can_make_request():
            risk_prompt = f"{context}\n\nTASK: Assess the risk profile of this stock based on volatility, momentum, and other factors."
            try:
                quota_manager.record_request()
                response = model.generate_content(risk_prompt)
                analysis['risk'] = response.text
            except Exception as e:
                logger.warning(f"AI risk assessment failed: {e}")
                analysis['risk'] = _generate_fallback_analysis(ticker, factors, company_name)['risk']
        else:
            analysis['risk'] = _generate_fallback_analysis(ticker, factors, company_name)['risk']
        
        # Investment Recommendation
        if quota_manager.can_make_request():
            rec_prompt = f"{context}\n\nTASK: Provide a clear investment recommendation (Buy/Hold/Sell) with rationale."
            try:
                quota_manager.record_request()
                response = model.generate_content(rec_prompt)
                analysis['recommendation'] = response.text
            except Exception as e:
                logger.warning(f"AI recommendation failed: {e}")
                analysis['recommendation'] = _generate_fallback_analysis(ticker, factors, company_name)['recommendation']
        else:
            analysis['recommendation'] = _generate_fallback_analysis(ticker, factors, company_name)['recommendation']
        
        # Market Context
        if quota_manager.can_make_request():
            context_prompt = f"{context}\n\nTASK: Provide market context and how this stock fits in the current market environment."
            try:
                quota_manager.record_request()
                response = model.generate_content(context_prompt)
                analysis['market_context'] = response.text
            except Exception as e:
                logger.warning(f"AI market context failed: {e}")
                analysis['market_context'] = _generate_fallback_analysis(ticker, factors, company_name)['market_context']
        else:
            analysis['market_context'] = _generate_fallback_analysis(ticker, factors, company_name)['market_context']
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error in AI analysis: {e}")
        return _generate_fallback_analysis(ticker, factors, company_name)


def generate_portfolio_insights(df: pd.DataFrame) -> Dict[str, str]:
    """
    Generate AI insights for portfolio analysis
    
    Args:
        df: DataFrame with stock rankings
        
    Returns:
        Dictionary with portfolio insights
    """
    model = setup_gemini()
    if not model:
        return _generate_fallback_portfolio_insights(df)
    
    try:
        # Prepare portfolio summary
        portfolio_summary = f"""
        PORTFOLIO SUMMARY:
        - Number of stocks: {len(df)}
        - Average score: {df['Score'].mean():.3f}
        - Average 1M return: {df['MOM_1M'].mean():.2%}
        - Average Sharpe ratio: {df['Sharpe_3M'].mean():.2f}
        - Top 5 stocks: {', '.join(df.head(5).index.tolist())}
        """
        
        insights = {}
        
        # Portfolio Overview
        overview_prompt = f"{portfolio_summary}\n\nTASK: Provide a high-level overview of this portfolio's characteristics and strengths."
        try:
            response = model.generate_content(overview_prompt)
            insights['portfolio_insights'] = response.text
        except Exception as e:
            logger.warning(f"AI portfolio overview failed: {e}")
            insights['portfolio_insights'] = _generate_fallback_portfolio_insights(df)['portfolio_insights']
        
        # Top Picks Analysis
        top_picks_prompt = f"{portfolio_summary}\n\nTASK: Analyze the top 5 stocks and explain why they rank highly."
        try:
            response = model.generate_content(top_picks_prompt)
            insights['top_picks'] = response.text
        except Exception as e:
            logger.warning(f"AI top picks analysis failed: {e}")
            insights['top_picks'] = _generate_fallback_portfolio_insights(df)['top_picks']
        
        # Sector Analysis
        sector_prompt = f"{portfolio_summary}\n\nTASK: Analyze sector diversification and concentration in this portfolio."
        try:
            response = model.generate_content(sector_prompt)
            insights['sector_analysis'] = response.text
        except Exception as e:
            logger.warning(f"AI sector analysis failed: {e}")
            insights['sector_analysis'] = _generate_fallback_portfolio_insights(df)['sector_analysis']
        
        return insights
        
    except Exception as e:
        logger.error(f"Error in portfolio analysis: {e}")
        return _generate_fallback_portfolio_insights(df)


def _generate_fallback_portfolio_insights(df: pd.DataFrame) -> Dict[str, str]:
    """Generate fallback portfolio insights when AI is unavailable"""
    
    avg_score = df['Score'].mean()
    avg_return = df['MOM_1M'].mean()
    avg_sharpe = df['Sharpe_3M'].mean()
    top_stocks = df.head(5).index.tolist()
    
    portfolio_insights = f"""
    Portfolio Overview:
    
    This portfolio contains {len(df)} stocks with an average AI score of {avg_score:.3f}.
    The portfolio shows {'strong' if avg_score > 0.5 else 'moderate' if avg_score > 0 else 'weak'} overall performance.
    
    Key Metrics:
    • Average 1-Month Return: {avg_return:.1%}
    • Average Sharpe Ratio: {avg_sharpe:.2f}
    • Portfolio Quality: {'High' if avg_score > 0.8 else 'Medium' if avg_score > 0.3 else 'Low'}
    """
    
    top_picks = f"""
    Top 5 Stocks: {', '.join(top_stocks)}
    
    These stocks rank highest based on our quantitative factor model, combining momentum, volatility, and risk-adjusted returns.
    They represent the strongest performers in the current market environment.
    """
    
    sector_analysis = f"""
    Sector Analysis:
    
    The portfolio includes stocks from various sectors including technology, healthcare, financials, and consumer goods.
    This diversification helps reduce sector-specific risks while maintaining exposure to growth opportunities.
    """
    
    return {
        'portfolio_insights': portfolio_insights,
        'top_picks': top_picks,
        'sector_analysis': sector_analysis
    }


def generate_ai_summary(ticker: str, factors: Dict[str, float], performance: Dict[str, float]) -> str:
    """
    Generate a simple AI summary for a stock
    
    Args:
        ticker: Stock ticker
        factors: Factor values
        performance: Performance metrics
        
    Returns:
        Summary string
    """
    model = setup_gemini()
    if not model:
        return _generate_fallback_summary(ticker, factors, performance)
    
    try:
        prompt = f"""
        TICKER: {ticker}
        FACTORS: {factors}
        PERFORMANCE: {performance}
        
        Provide a brief 2-3 sentence summary of this stock's investment potential.
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        logger.error(f"Error in AI summary: {e}")
        return _generate_fallback_summary(ticker, factors, performance)


def _generate_fallback_summary(ticker: str, factors: Dict[str, float], performance: Dict[str, float]) -> str:
    """Generate fallback summary when AI is unavailable"""
    
    score = factors.get('Score', 0)
    mom_1m = factors.get('MOM_1M', 0)
    
    if score > 0.8:
        sentiment = "strong buy"
    elif score > 0.3:
        sentiment = "buy"
    elif score > 0:
        sentiment = "hold"
    else:
        sentiment = "sell"
    
    return f"{ticker} shows {sentiment} signals with a {mom_1m:.1%} 1-month return and AI score of {score:.3f}."
