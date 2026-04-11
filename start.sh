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
sed -i "s/listen .*/listen $PORT;/g" /etc/nginx/conf.d/default.conf 2>/dev/null || \
sed -i "s/listen .*/listen $PORT;/g" /etc/nginx/conf.d/app.conf 2>/dev/null || true

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
# 3. CHỜ BACKEND SẴN SÀNG (30 lần x 2s = 60s max)
# ============================================
echo "⏳ Waiting for backend to load PhoBERT model (có thể mất 20-30s)..."

MAX_RETRIES=30
RETRY_COUNT=0
BACKEND_READY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo "✅ Backend is running successfully!"
        BACKEND_READY=true
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Attempt $RETRY_COUNT/$MAX_RETRIES... (waiting for model load)"
    sleep 2
done

# Kiểm tra backend log nếu fail
if [ "$BACKEND_READY" = false ]; then
    echo "❌ Backend failed to start after $MAX_RETRIES attempts!"
    echo "📋 Backend logs:"
    tail -50 /tmp/backend.log
    exit 1
fi

# Extra: Kiểm tra root endpoint
echo "🔍 Testing root endpoint..."
curl -s http://localhost:8000/ || echo "   Root not available (OK if only /api exists)"

# ============================================
# 4. KHỞI ĐỘNG NGINX (chỉ khi backend OK)
# ============================================
echo "🌐 Starting Nginx on port $PORT..."

# Test nginx config trước
nginx -t || exit 1

# Start nginx foreground
exec nginx -g 'daemon off;'
