#!/bin/bash
# Build script for QuantSnap deployment

echo "🚀 Building QuantSnap..."

# Clear any existing cache
echo "🧹 Clearing cache..."
pip cache purge 2>/dev/null || true

# Install dependencies without cache
echo "📦 Installing dependencies..."
pip install --no-cache-dir -r requirements.txt

# Verify installation
echo "Dependencies installed successfully"

# Test imports
echo "Testing imports..."
python -c "import yfinance, fastapi, streamlit, pandas, numpy; print('All imports successful')"

echo "Build complete!"
