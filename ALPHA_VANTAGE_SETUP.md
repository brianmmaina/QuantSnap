# Alpha Vantage Setup Guide

## 🚀 Getting Started with Alpha Vantage

### 1. Get Your Free API Key

1. **Visit Alpha Vantage**: Go to [https://www.alphavantage.co/](https://www.alphavantage.co/)
2. **Sign Up**: Click "Get Your Free API Key Today"
3. **Register**: Create a free account
4. **Get API Key**: Your API key will be displayed immediately

### 2. Free Tier Limits

- **500 API calls per day** (perfect for development)
- **Real-time stock data**
- **Historical data**
- **Company fundamentals**
- **No credit card required**

### 3. Set Up Your Environment

1. **Copy your API key** from Alpha Vantage
2. **Create `.env` file** in your project root:
   ```bash
   cp env.template .env
   ```
3. **Add your API key** to `.env`:
   ```
   ALPHA_VANTAGE_API_KEY=your_actual_api_key_here
   ```

### 4. Install Dependencies

```bash
pip install alpha-vantage==2.3.1
```

### 5. Test the Integration

The app will automatically:
- **Try Alpha Vantage first** for accurate data
- **Fallback to yfinance** if Alpha Vantage fails
- **Log which data source** is being used

## 📊 Benefits of Alpha Vantage

### ✅ More Accurate Data
- **Real-time pricing** from major exchanges
- **Consistent data format** across all stocks
- **Professional-grade accuracy**

### ✅ Better Reliability
- **No rate limiting issues** like yfinance
- **Stable API** with 99.9% uptime
- **Consistent response times**

### ✅ Rich Company Data
- **Company overview** with fundamentals
- **Sector classification**
- **Market capitalization**
- **Financial ratios**

## 🔧 How It Works

### Data Flow:
1. **App requests stock data**
2. **Tries Alpha Vantage first**
3. **If successful**: Uses Alpha Vantage data
4. **If failed**: Falls back to yfinance
5. **Logs the data source** for transparency

### Rate Limiting:
- **Alpha Vantage**: 12-second delays between requests
- **yfinance**: 100ms delays between requests
- **Automatic fallback** if one fails

## 🎯 Expected Results

### More Accurate Percentages:
- **Realistic 1-month returns**: +5% to +25%
- **Accurate daily changes**: -2% to +5%
- **Proper Sharpe ratios**: 0.5 to 3.0

### Better Company Information:
- **Full company names**: "Apple Inc." instead of "AAPL"
- **Correct sectors**: "Technology", "Healthcare", etc.
- **Accurate market caps**

## 🚨 Troubleshooting

### If Alpha Vantage Fails:
1. **Check API key** in `.env` file
2. **Verify daily limit** (500 calls/day)
3. **Check logs** for specific error messages
4. **App will automatically** use yfinance fallback

### If You Hit Rate Limits:
- **Free tier**: 500 calls/day
- **Upgrade**: $49.99/month for 1200 calls/minute
- **Or wait**: Reset at midnight UTC

## 📈 Next Steps

1. **Get your API key** from Alpha Vantage
2. **Add it to your `.env` file**
3. **Deploy your app**
4. **Enjoy more accurate data!**

The app will automatically use Alpha Vantage for better accuracy while maintaining yfinance as a reliable fallback.
