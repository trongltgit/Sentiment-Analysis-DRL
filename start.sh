#!/bin/bash
set -e  # Exit on error

echo "🚀 Starting AI Sentiment Analysis Service..."

PORT=${PORT:-10000}
echo "🔧 Using PORT: $PORT"

# ============================================
# 1. CONFIGURE NGINX
# ============================================
echo "📝 Configuring nginx..."

# Xóa config cũ
rm -f /etc/nginx/sites-enabled/default /etc/nginx/conf.d/default.conf 2>/dev/null || true

# Thay port trong nginx.conf
sed -i "s/listen 10000/listen $PORT/g" /etc/nginx/conf.d/default.conf 2>/dev/null || \
sed -i "s/listen .*/listen $PORT;/g" /etc/nginx/conf.d/default.conf

# Validate nginx config
nginx -t || {
    echo "❌ Nginx config failed!"
    cat /etc/nginx/conf.d/default.conf
    exit 1
}

# ============================================
# 2. START BACKGROUND NGINX (trước để khởi động nhanh)
# ============================================
echo "🌐 Starting nginx temporarily..."
nginx

# ============================================
# 3. START BACKEND (quan trọng nhất!)
# ============================================
echo "📡 Starting Backend (FastAPI) on port 8000..."
cd /app

# Chạy backend với unbuffered output
export PYTHONUNBUFFERED=1
python -c "
import sys
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/backend')

# Pre-load để kiểm tra lỗi import
try:
    from app.services.analyzer import SentimentAnalyzer
    from app.services.crawler import CommentCrawler
    print('✅ Imports successful')
except Exception as e:
    print(f'❌ Import error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
" || exit 1

# Start uvicorn
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level info --access-log &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# ============================================
# 4. WAIT FOR BACKEND (tối đa 120 giây)
# ============================================
echo "⏳ Waiting for backend (max 120s)..."

MAX_RETRIES=60
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    if curl -s --max-time 2 http://localhost:8000/api/v1/health 2>/dev/null | grep -q "healthy"; then
        echo "✅ Backend is healthy!"
        break
    fi
    
    # Check if process still alive
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ Backend process died!"
        exit 1
    fi
    
    RETRY=$((RETRY + 1))
    echo "   Attempt $RETRY/$MAX_RETRIES..."
    sleep 2
done

if [ $RETRY -eq $MAX_RETRIES ]; then
    echo "❌ Backend failed to start after $MAX_RETRIES attempts"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Test endpoints
echo "🔍 Testing endpoints..."
curl -s http://localhost:8000/ | head -20 || echo "   Root check skipped"
curl -s http://localhost:8000/api/v1/health || echo "   Health check warning"

# ============================================
# 5. RELOAD NGINX VỚI PROXY
# ============================================
echo "🔄 Reloading nginx with proxy config..."
nginx -s reload || nginx

echo "✅ Service is ready!"
echo "   Frontend: http://localhost:$PORT"
echo "   Backend API: http://localhost:8000"

# ============================================
# 6. KEEP ALIVE
# ============================================
# Monitor backend
while true; do
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ Backend crashed! Exiting..."
        exit 1
    fi
    
    if ! curl -s --max-time 5 http://localhost:8000/api/v1/health >/dev/null 2>&1; then
        echo "⚠️ Backend health check failed"
    fi
    
    sleep 30
done
