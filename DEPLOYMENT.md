# 🚀 QuantSnap Deployment Guide

## Render Deployment

### Overview
QuantSnap uses a simplified architecture with two optional services:
- **Frontend**: Streamlit app (required)
- **Backend**: AI analysis service (optional)

### Quick Deploy

1. **Fork/Clone Repository**
   ```bash
   git clone <your-repo-url>
   cd ai-daily-draft
   ```

2. **Deploy to Render**
   - Go to [render.com](https://render.com)
   - Connect your GitHub repository
   - Use the `render.yaml` blueprint for automatic deployment

### Manual Deployment

#### Frontend Service (Required)
1. Create new **Web Service** on Render
2. Connect your GitHub repository
3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run frontend/app.py --server.port $PORT --server.address 0.0.0.0`
   - **Environment**: Python 3.9

#### AI Backend Service (Optional)
1. Create new **Web Service** on Render
2. Connect your GitHub repository
3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3.9

### Environment Variables

#### Frontend Service
- `GEMINI_API_KEY`: Your Google Gemini API key (optional)
- `NEWS_API_KEY`: Your News API key (optional)
- `BACKEND_URL`: URL of your AI backend (if deployed)

#### AI Backend Service
- `GEMINI_API_KEY`: Your Google Gemini API key (required for AI features)
- `PORT`: 8000 (default)

### Deployment Options

#### Option 1: Frontend Only (Recommended)
- Deploy only the frontend service
- Works without AI backend
- Uses direct yfinance integration
- Faster and simpler

#### Option 2: Full Stack
- Deploy both frontend and backend
- Enable AI analysis features
- Requires Gemini API key
- More features but higher complexity

### URLs After Deployment

- **Frontend**: `https://your-app-name.onrender.com`
- **Backend**: `https://your-backend-name.onrender.com`
- **API Docs**: `https://your-backend-name.onrender.com/docs`

### Testing Deployment

1. **Test Frontend**:
   - Visit your frontend URL
   - Check if stock data loads
   - Verify charts and rankings work

2. **Test Backend** (if deployed):
   ```bash
   curl https://your-backend-name.onrender.com/health
   ```

3. **Test AI Integration**:
   - Set `BACKEND_URL` in frontend environment
   - Check if AI analysis appears in the app

### Troubleshooting

#### Common Issues
- **Build Failures**: Check Python version compatibility
- **Import Errors**: Verify all dependencies in `requirements.txt`
- **API Errors**: Check environment variables are set correctly
- **Timeout Issues**: Render free tier has limitations

#### Performance Tips
- Use Render's free tier for testing
- Upgrade to paid plan for production
- Monitor resource usage
- Optimize for cold starts

### Cost Considerations

#### Free Tier (Recommended for testing)
- **Frontend**: Free with limitations
- **Backend**: Free with limitations
- **Bandwidth**: Limited but sufficient for testing

#### Paid Plans
- **Frontend**: $7/month for better performance
- **Backend**: $7/month for better performance
- **Bandwidth**: Higher limits

### Alternative Deployments

#### Streamlit Cloud
- Deploy frontend only
- Simpler setup
- Free tier available
- No backend needed

#### Railway
- Similar to Render
- Good for full-stack deployment
- Free tier available

#### Heroku
- More complex setup
- Requires Procfile
- Paid plans only

### Monitoring

#### Health Checks
- Frontend: Visit the URL
- Backend: `GET /health` endpoint
- AI: Test analysis endpoint

#### Logs
- Check Render dashboard logs
- Monitor for errors
- Track API usage

### Security

#### API Keys
- Never commit API keys to repository
- Use Render environment variables
- Rotate keys regularly

#### CORS
- Backend configured for frontend access
- Adjust if needed for custom domains

---

**Ready to deploy? Follow the Quick Deploy steps above!** 🚀
