#!/bin/bash
set -e

echo "🚀 Professional Financial Sentiment Analysis v2.0"
echo "🤖 AI Engine: Groq LLaMA 3.3 70B (FREE)"
echo "📈 Market Data: yfinance + Open Exchange Rates + RSS"

PORT=${PORT:-10000}
echo "🔧 PORT: $PORT"

# Check frontend
if [ -f "/usr/share/nginx/html/index.html" ]; then
    echo "✅ Frontend: OK ($(wc -c < /usr/share/nginx/html/index.html) bytes)"
else
    echo "❌ Frontend index.html NOT FOUND"
    exit 1
fi

# Check GROQ_API_KEY
if [ -z "$GROQ_API_KEY" ]; then
    echo "⚠️  GROQ_API_KEY not set — will use VADER fallback"
else
    echo "✅ GROQ_API_KEY configured"
fi

# Pre-check imports
python -c "
import sys
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/backend')
try:
    from backend.main import app
    print('✅ FastAPI app import OK')
    from backend.app.services.sentiment_analyzer import ProfessionalSentimentAnalyzer
    print('✅ Sentiment analyzer import OK')
    from backend.app.services.financial_data import fetch_vn_stocks
    print('✅ Financial data service import OK')
except Exception as e:
    print(f'❌ Import error: {e}')
    import traceback; traceback.print_exc()
    sys.exit(1)
" || exit 1

export OMP_NUM_THREADS=1
export PYTHONUNBUFFERED=1

echo ""
echo "🌐 Starting FastAPI on 0.0.0.0:${PORT}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port ${PORT} \
    --workers 1 \
    --log-level info
