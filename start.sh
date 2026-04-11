#!/bin/bash

echo "🚀 Starting AI Sentiment Analysis Service..."

PORT=${PORT:-10000}
echo "🔧 Using PORT: $PORT"

# ============================================
# 1. DỌN DẸP NGINX CŨ (quan trọng!)
# ============================================
echo "🧹 Cleaning up nginx configs..."
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
rm -f /etc/nginx/conf.d/default.conf 2>/dev/null || true

# Thay port trong nginx.conf
if [ -f /etc/nginx/conf.d/app.conf ]; then
    sed -i "s/listen .*/listen $PORT;/g" /etc/nginx/conf.d/app.conf
    echo "   Updated nginx port to $PORT"
fi

# ============================================
# 2. KHỞI ĐỘNG BACKEND TRƯỚC
# ============================================
echo "📡 Starting Backend (FastAPI) on port 8000..."
cd /app

# Chạy backend và log ra file để debug
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level info > /tmp/backend.log 2>&1 &
BACKEND_PID=$!

echo "   Backend PID: $BACKEND_PID"

# ============================================
# 3. CHỜ BACKEND SẴN SÀNG (60 lần x 2s = 120s max cho model load)
# ============================================
echo "⏳ Waiting for backend to load (có thể mất 30-60s cho PhoBERT)..."

MAX_RETRIES=60
RETRY_COUNT=0
BACKEND_READY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo "✅ Backend health check passed!"
        BACKEND_READY=true
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    
    # Show progress every 5 attempts
    if [ $((RETRY_COUNT % 5)) -eq 0 ]; then
        echo "   Attempt $RETRY_COUNT/$MAX_RETRIES... (still loading)"
    fi
    
    sleep 2
done

# Kiểm tra backend log nếu fail
if [ "$BACKEND_READY" = false ]; then
    echo "❌ Backend failed to start after $MAX_RETRIES attempts!"
    echo "📋 Last 30 lines of backend logs:"
    tail -30 /tmp/backend.log
    echo ""
    echo "📋 Full error:"
    cat /tmp/backend.log
    exit 1
fi

# Extra: Kiểm tra API endpoints
echo "🔍 Testing API endpoints..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/api/v1/health)
echo "   Health: $HEALTH_RESPONSE"

# ============================================
# 4. KHỞI ĐỘNG NGINX (chỉ khi backend OK)
# ============================================
echo "🌐 Starting Nginx on port $PORT..."

# Test nginx config trước
nginx -t || {
    echo "❌ Nginx config test failed!"
    exit 1
}

# Start nginx foreground
exec nginx -g 'daemon off;'
