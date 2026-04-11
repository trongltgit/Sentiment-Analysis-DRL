#!/bin/bash
set -e

echo "🚀 Starting AI Sentiment Analysis Service..."
PORT=${PORT:-10000}
echo "🔧 PORT: $PORT"

# 1. Cleanup nginx
rm -f /etc/nginx/sites-enabled/default /etc/nginx/conf.d/default.conf 2>/dev/null || true
sed -i "s/listen 10000/listen $PORT/g" /etc/nginx/conf.d/default.conf 2>/dev/null || true

# 2. Test nginx config
nginx -t || exit 1

# 3. Start nginx
echo "🌐 Starting nginx..."
nginx

# 4. Start backend
echo "📡 Starting Backend on port 8000..."
cd /app
export PYTHONUNBUFFERED=1

# Pre-check imports
python -c "
import sys
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/backend')
try:
    from app.services.analyzer import SentimentAnalyzer
    from app.services.crawler import CommentCrawler
    print('✅ Imports OK')
except Exception as e:
    print(f'❌ Import error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
" || exit 1

# Start uvicorn
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level info &
BACKEND_PID=$!

# 5. Wait for backend (max 120s)
echo "⏳ Waiting for backend..."
for i in {1..60}; do
    if curl -s --max-time 2 http://localhost:8000/api/v1/health 2>/dev/null | grep -q "healthy"; then
        echo "✅ Backend ready!"
        break
    fi
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ Backend died!"
        exit 1
    fi
    sleep 2
done

# 6. Reload nginx
nginx -s reload || true

echo "✅ Service ready at port $PORT"

# Keep alive
wait $BACKEND_PID
