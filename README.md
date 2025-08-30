# 📈 QuantSnap - AI-Powered Stock Analysis

A modern, streamlined stock analysis application built with Streamlit and yfinance, featuring AI-powered insights and real-time market data.

## 🎯 Features

- **Real-Time Stock Data**: Direct integration with Yahoo Finance API
- **AI-Powered Analysis**: Google Gemini integration for intelligent stock insights
- **Interactive Charts**: Beautiful Plotly charts with dark theme
- **67/33 Scoring Algorithm**: Proprietary quantitative and qualitative factor analysis
- **Live Stock Prices**: Real-time price tracking and performance metrics
- **Top Performers**: Ranked stock recommendations based on comprehensive analysis

## 🏗️ Architecture

### Simplified Design
- **Frontend**: Streamlit app with direct yfinance integration
- **Backend**: Lightweight FastAPI service for AI analysis only
- **Data Flow**: Streamlit → yfinance → Process → Display
- **AI Enhancement**: Optional backend integration for advanced analysis

### Key Components
- **Data Fetching**: Direct yfinance calls for real-time data
- **Metrics Calculation**: 1M/3M growth, volatility, Sharpe ratio
- **Scoring Algorithm**: 67% traditional factors + 33% reputation factors
- **AI Analysis**: Google Gemini integration for intelligent insights

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager
- Google Gemini API key (optional, for AI features)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-daily-draft
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env.template .env
   # Edit .env and add your API keys
   ```

### Running the Application

#### Option 1: Frontend Only (Recommended)
```bash
streamlit run frontend/app.py
```

#### Option 2: Full Application with AI Backend
```bash
# Terminal 1: Start AI Backend
python3 -m uvicorn app.main:app --reload

# Terminal 2: Start Frontend
streamlit run frontend/app.py
```

### Environment Variables

Create a `.env` file with:
```env
# AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Backend Configuration (optional)
BACKEND_URL=http://localhost:8000

# Optional: News API
NEWS_API_KEY=your_news_api_key_here
```

## 📊 Scoring Algorithm

### Traditional Factors (67% Weight)
- **1-Month Stock Price Growth** (40% of traditional)
- **3-Month Stock Price Growth** (25% of traditional)
- **Sharpe Ratio** (15% of traditional)
- **Volume Factor** (10% of traditional)
- **Market Cap Factor** (10% of traditional)

### Reputation Factors (33% Weight)
- **P/E Ratio Quality** (40% of reputation)
- **Dividend Yield** (35% of reputation)
- **Beta Stability** (25% of reputation)

### Performance Filters
- **Severe Penalty (-90%)**: 1M growth < -5%
- **Heavy Penalty (-70%)**: 1M growth < 0%
- **Moderate Penalty (-30%)**: 1M growth < 2%

## 🎨 UI Features

- **Dark Theme**: Professional terminal-style interface
- **Interactive Charts**: Plotly charts with multiple time periods
- **Real-Time Updates**: Live data fetching on each session
- **Responsive Design**: Optimized for desktop and mobile
- **Custom Styling**: Bloomberg-inspired financial interface

## 🔧 Technical Stack

### Frontend
- **Streamlit**: Web application framework
- **yfinance**: Yahoo Finance data integration
- **Plotly**: Interactive data visualization
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computations

### Backend (Optional)
- **FastAPI**: Lightweight API for AI analysis
- **Google Gemini**: AI-powered stock analysis
- **Pydantic**: Data validation

### Data Sources
- **Yahoo Finance**: Real-time stock data
- **Auto-Adjustment**: Dividends and splits handled automatically
- **500+ Stocks**: Comprehensive market coverage

## 📈 Usage

1. **Select Stocks**: Choose from predefined list or add custom tickers
2. **View Rankings**: See top performers with scores and metrics
3. **Analyze Charts**: Interactive price charts with multiple timeframes
4. **AI Insights**: Get AI-powered analysis for top stocks
5. **Review Methodology**: Understand the scoring algorithm

## 🚀 Deployment

### Streamlit Cloud (Recommended)
1. Push code to GitHub
2. Connect repository to Streamlit Cloud
3. Deploy with environment variables

### Local Development
```bash
# Frontend only
streamlit run frontend/app.py

# Full application (two terminals)
# Terminal 1: python3 -m uvicorn app.main:app --reload
# Terminal 2: streamlit run frontend/app.py
```

### Backend (Optional)
```bash
cd app
uvicorn main:app --reload
```

## 🔍 API Endpoints

### Backend Service (Optional)
- `GET /health` - Service health check
- `POST /analyze` - AI stock analysis
- `GET /` - Service information

### Testing the API
```bash
# Health check
curl http://localhost:8000/health

# AI analysis (requires running backend)
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker":"AAPL","stock_data":{"score":7.8},"news_data":[]}'
```

## 📝 Project Structure

```
ai-daily-draft/
├── frontend/
│   └── app.py              # Main Streamlit application
├── app/
│   ├── main.py             # FastAPI backend (AI only)
│   └── gemini.py           # AI analysis module

├── requirements.txt        # Python dependencies
├── env.template           # Environment variables template
└── README.md              # Project documentation
```

## 🎯 Key Benefits

- **Simplified Architecture**: No complex database or heavy backend processing
- **Real-Time Data**: Direct yfinance integration for live market data
- **AI Enhancement**: Optional backend for advanced analysis
- **User-Friendly**: Clean, intuitive interface
- **Cost-Effective**: Free tier compatible with minimal dependencies

## 🔮 Future Enhancements

- **News Integration**: Real-time financial news with sentiment analysis
- **Portfolio Tracking**: User portfolio management
- **Advanced Charts**: Technical indicators and analysis tools
- **Mobile App**: Native mobile application
- **Social Features**: Community insights and sharing

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ using Streamlit, yfinance, and Google Gemini AI**
 
