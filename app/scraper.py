#!/usr/bin/env python3
"""
Data scraping utilities for QuantSnap
"""

import os
import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time
import random

logger = logging.getLogger(__name__)

class NewsScraper:
    """News scraping and fetching utilities"""
    
    def __init__(self):
        self.news_api_key = os.getenv('NEWS_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_stock_news(self, ticker: str, limit: int = 5) -> List[Dict]:
        """Fetch news for a specific stock"""
        if not self.news_api_key:
            logger.warning("No NEWS_API_KEY found. Using fallback news.")
            return self._get_fallback_news(ticker, limit)
        
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': f'"{ticker}" AND (stock OR earnings OR financial OR company)',
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': limit,
                'apiKey': self.news_api_key
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            news_items = []
            for article in articles:
                news_item = {
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'url': article.get('url', ''),
                    'published_at': article.get('publishedAt', ''),
                    'source': article.get('source', {}).get('name', ''),
                    'sentiment': self._analyze_sentiment(article.get('title', '') + ' ' + article.get('description', ''))
                }
                news_items.append(news_item)
            
            logger.info(f"Fetched {len(news_items)} news items for {ticker}")
            return news_items
            
        except Exception as e:
            logger.error(f"Error fetching news for {ticker}: {e}")
            return self._get_fallback_news(ticker, limit)
    
    def fetch_market_news(self, limit: int = 10) -> List[Dict]:
        """Fetch general market news"""
        if not self.news_api_key:
            logger.warning("No NEWS_API_KEY found. Using fallback market news.")
            return self._get_fallback_market_news(limit)
        
        try:
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                'category': 'business',
                'language': 'en',
                'pageSize': limit,
                'apiKey': self.news_api_key
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            news_items = []
            for article in articles:
                news_item = {
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'url': article.get('url', ''),
                    'published_at': article.get('publishedAt', ''),
                    'source': article.get('source', {}).get('name', ''),
                    'sentiment': self._analyze_sentiment(article.get('title', '') + ' ' + article.get('description', ''))
                }
                news_items.append(news_item)
            
            logger.info(f"Fetched {len(news_items)} market news items")
            return news_items
            
        except Exception as e:
            logger.error(f"Error fetching market news: {e}")
            return self._get_fallback_market_news(limit)
    
    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis"""
        text_lower = text.lower()
        
        positive_words = ['up', 'gain', 'rise', 'positive', 'strong', 'beat', 'growth', 'profit', 'success']
        negative_words = ['down', 'fall', 'drop', 'negative', 'weak', 'miss', 'loss', 'decline', 'risk']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _get_fallback_news(self, ticker: str, limit: int) -> List[Dict]:
        """Fallback news when API is not available"""
        fallback_news = [
            {
                'title': f'{ticker} Stock Analysis: Market Performance Review',
                'description': f'Comprehensive analysis of {ticker} stock performance and market outlook.',
                'url': f'https://finance.yahoo.com/quote/{ticker}',
                'published_at': datetime.now().isoformat(),
                'source': 'Yahoo Finance',
                'sentiment': 'neutral'
            },
            {
                'title': f'{ticker} Earnings Report: Financial Performance Update',
                'description': f'Latest earnings and financial performance data for {ticker}.',
                'url': f'https://finance.yahoo.com/quote/{ticker}',
                'published_at': datetime.now().isoformat(),
                'source': 'Yahoo Finance',
                'sentiment': 'neutral'
            }
        ]
        return fallback_news[:limit]
    
    def _get_fallback_market_news(self, limit: int) -> List[Dict]:
        """Fallback market news when API is not available"""
        fallback_news = [
            {
                'title': 'Market Update: Stock Market Performance Today',
                'description': 'Latest updates on major stock market indices and trading activity.',
                'url': 'https://finance.yahoo.com',
                'published_at': datetime.now().isoformat(),
                'source': 'Yahoo Finance',
                'sentiment': 'neutral'
            },
            {
                'title': 'Economic Indicators: Market Sentiment Analysis',
                'description': 'Analysis of current economic indicators and market sentiment.',
                'url': 'https://finance.yahoo.com',
                'published_at': datetime.now().isoformat(),
                'source': 'Yahoo Finance',
                'sentiment': 'neutral'
            }
        ]
        return fallback_news[:limit]

class DataScraper:
    """General data scraping utilities"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_stock_info(self, ticker: str) -> Optional[Dict]:
        """Scrape additional stock information"""
        try:
            # This is a placeholder for actual scraping logic
            # In a real implementation, you might scrape from various financial websites
            
            # For now, return basic structure
            return {
                'ticker': ticker,
                'scraped_at': datetime.now().isoformat(),
                'additional_info': 'Scraped data placeholder'
            }
            
        except Exception as e:
            logger.error(f"Error scraping data for {ticker}: {e}")
            return None
    
    def get_market_sentiment(self) -> Dict:
        """Get overall market sentiment indicators"""
        try:
            # Placeholder for market sentiment scraping
            # In a real implementation, you might scrape from various sources
            
            return {
                'fear_greed_index': random.randint(30, 70),  # Placeholder
                'market_mood': random.choice(['bullish', 'neutral', 'bearish']),
                'volatility_index': random.uniform(15, 25),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting market sentiment: {e}")
            return {
                'fear_greed_index': 50,
                'market_mood': 'neutral',
                'volatility_index': 20,
                'timestamp': datetime.now().isoformat()
            }
    
    def scrape_sector_performance(self) -> List[Dict]:
        """Scrape sector performance data"""
        try:
            # Placeholder for sector performance scraping
            sectors = ['Technology', 'Healthcare', 'Finance', 'Energy', 'Consumer']
            
            sector_data = []
            for sector in sectors:
                sector_data.append({
                    'sector': sector,
                    'performance': random.uniform(-5, 10),
                    'volume': random.randint(1000000, 10000000),
                    'timestamp': datetime.now().isoformat()
                })
            
            return sector_data
            
        except Exception as e:
            logger.error(f"Error scraping sector performance: {e}")
            return []

# Global instances
news_scraper = NewsScraper()
data_scraper = DataScraper()
