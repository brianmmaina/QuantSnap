# AI Daily Draft - Stock Rankings

A data-driven stock ranking application powered by quantitative factors and AI analysis. Built with Python, FastAPI, PostgreSQL, and Streamlit. Following the basketball scout pattern with clean data processing and API-first design.

## 🚀 Features

### **Core Functionality**
- **Multi-Factor Quantitative Model**: Momentum (1M, 3M), Volatility (30d), Sharpe Ratio (3M), Dollar Volume (20d), Slope (50d)
- **World's Top 500+ Stocks**: Comprehensive database including US mega-caps, international stocks, and emerging markets
- **Real-Time Data**: Daily updates using Yahoo Finance API
- **Professional UI**: Clean, Chronicle-inspired design with company logos

### **AI-Powered Analysis**
- **Google Gemini AI Integration**: Intelligent stock analysis and recommendations
- **Portfolio Insights**: AI-generated portfolio overview and sector analysis
- **Risk Assessment**: AI-powered risk evaluation and investment recommendations
- **Fallback Analysis**: Works even without API key using quantitative factors

### **Real-Time News Integration**
- **Market News**: Latest financial and business headlines
- **Stock-Specific News**: Relevant news for individual stocks
- **Sentiment Analysis**: Color-coded news sentiment (positive/negative/neutral)
- **NewsAPI Integration**: Real-time news when API key is provided
- **Fallback Content**: Curated placeholder news when API is unavailable

### **Stock Universes**
- **World Top Stocks**: 500+ global stocks (AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, etc.)
- **S&P 500**: Traditional large-cap US stocks
- **Top ETFs**: Popular ETFs for diversification
- **Popular Stocks**: High-profile individual stocks
- **Custom Search**: Analyze any stock ticker

### **Professional Design**
- **Company Logos**: Visual branding with colored initials
- **Standardized Typography**: Inter font with consistent sizing
- **Responsive Layout**: Works on desktop and mobile
- **Clean Interface**: Minimalist design focused on data

## 📊 How It Works

1. **Data Collection**: Fetches historical price data from Yahoo Finance
2. **Factor Calculation**: Computes momentum, volatility, Sharpe ratio, and other metrics
3. **Normalization**: Applies winsorization and Z-scoring for fair comparison
4. **Scoring**: Combines factors with weighted scoring algorithm
5. **AI Analysis**: Uses Gemini AI for intelligent insights and recommendations
6. **Ranking**: Displays top stocks with detailed analysis

## 🛠️ Tech Stack

- **Python 3.11+**: Core application logic
- **FastAPI**: RESTful API backend
- **PostgreSQL**: Clean, normalized database
- **Streamlit**: Web interface and deployment
- **Pandas & NumPy**: Data manipulation and analysis
- **yfinance**: Real-time stock data
- **scikit-learn**: Statistical calculations
- **Plotly**: Interactive charts
- **Google Gemini AI**: Intelligent analysis
- **SQLAlchemy**: Database ORM
- **Redis**: Caching (optional)

## 📁 Project Structure

```
ai-daily-draft/
├── src/                  # Main application source
│   ├── frontend.py      # Streamlit frontend application
│   ├── backend.py       # FastAPI backend application
│   └── core/            # Core business logic
│       ├── factors.py   # Factor calculations
│       ├── scoring.py   # Ranking algorithms
│       ├── universe.py  # Stock universe definitions
│       └── ai_analysis.py # AI-powered analysis
├── infrastructure/       # Infrastructure & data layer
│   ├── database.py      # PostgreSQL database operations
│   ├── data_pipeline.py # Data processing pipeline
│   └── schema.sql       # Database schema
├── data/                # Static data files
│   └── universes/       # Stock universe CSV files
├── scripts/             # Utility scripts
│   └── start_app.py     # Unified startup script
├── requirements.txt     # Python dependencies
├── env.template         # Environment template
├── .gitignore          # Git ignore rules
└── README.md           # Documentation
```

## 🚀 Quick Start

### **Local Development**

1. **Clone and Setup**
   ```bash
   git clone <your-repo>
   cd ai-daily-draft
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp env.template .env
   # Add your API keys to .env file:
   # DATABASE_URL=postgresql://username:password@localhost:5432/ai_daily_draft
   # GEMINI_API_KEY=your_gemini_api_key_here
   # NEWS_API_KEY=your_newsapi_key_here (optional)
   ```

3. **Set up PostgreSQL Database**
   ```bash
   # Install PostgreSQL (if not already installed)
   brew install postgresql@14  # macOS
   # or
   sudo apt-get install postgresql postgresql-contrib  # Ubuntu
   
   # Create database
   createdb ai_daily_draft
   ```

4. **Run the Application**
   ```bash
   python3 scripts/start_app.py
   ```
   
   This will start both the FastAPI backend (port 8000) and Streamlit frontend (port 8501).
   
   **Or run individually:**
   ```bash
   # Backend only
   python3 -m uvicorn src.backend:app --reload --port 8000
   
   # Frontend only
   streamlit run src/frontend.py --server.port 8501
   ```

### **Deploy to Render**

1. **Prepare Repository**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Deploy on Render**
   - Connect your GitHub repository
   - Use the `render.yaml` blueprint
   - Set environment variables in Render dashboard
   - Deploy!

## 📈 Usage

### **Select Universe**
- Choose from World Top Stocks, S&P 500, Top ETFs, or Popular Stocks
- Each universe contains different stock categories

### **View Rankings**
- See top-ranked stocks with company logos
- View quantitative scores and performance metrics
- Understand factor breakdowns

### **Search Any Stock**
- Enter any ticker symbol to analyze
- Get instant factor calculations and AI insights
- Compare with universe rankings

### **AI Analysis**
- Portfolio overview and sector analysis
- Risk assessment and investment recommendations
- Market context and trends

## 🔧 Configuration

### **Environment Variables**
```bash
# Required for AI features
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
OPENAI_API_KEY=your_openai_key_here
NEWSAPI_KEY=your_news_api_key_here
```

### **CLI Commands**
```bash
# Build rankings for any universe
python3 cli.py build --universe world_top_stocks --top 20

# List available universes
python3 cli.py list-universes

# Get latest data info
python3 cli.py latest
```

## 📊 Factor Model

### **Quantitative Factors**
- **Momentum (1M)**: 1-month price return (22% weight)
- **Momentum (3M)**: 3-month price return (22% weight)
- **Slope (50d)**: 50-day price trend (12% weight)
- **Volatility (30d)**: 30-day price volatility (16% weight)
- **Sharpe Ratio (3M)**: Risk-adjusted returns (18% weight)
- **Dollar Volume (20d)**: Trading activity (10% weight)

### **Scoring Process**
1. **Data Collection**: Historical price data from Yahoo Finance
2. **Factor Calculation**: Compute all quantitative metrics
3. **Normalization**: Winsorize outliers (±3σ) and Z-score
4. **Weighted Scoring**: Combine factors with optimized weights
5. **Ranking**: Sort by composite score

## 🎯 Investment Strategy

### **Score Interpretation**
- **Strong Buy (>0.8)**: Excellent performance across all factors
- **Buy (0.3-0.8)**: Good performance, worth considering
- **Hold (0.0-0.3)**: Average performance, monitor closely
- **Sell (<0.0)**: Poor performance, avoid for now

### **Risk Management**
- **Diversification**: Spread across multiple sectors
- **Risk-Adjusted Returns**: Prioritize Sharpe ratio
- **Volume Analysis**: Ensure sufficient liquidity
- **AI Validation**: Use AI insights for confirmation

## 🔒 Security & Privacy

- **No Personal Data**: App doesn't collect or store personal information
- **API Key Security**: Environment variables for sensitive data
- **Public Data**: Uses only publicly available market data
- **No Trading**: Educational tool only, no actual trading

## 📝 License

This project is for educational and research purposes. Use at your own risk.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues or questions:
- Check the documentation
- Review error logs
- Ensure API keys are configured correctly
- Verify data sources are accessible

---

**Disclaimer**: This application is for educational purposes only. It does not constitute financial advice. Always do your own research and consult with financial professionals before making investment decisions.
 