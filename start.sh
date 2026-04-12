#!/bin/bash
set -e

echo "🚀 Starting AI Sentiment Analysis Service..."
PORT=${PORT:-10000}
echo "🔧 PORT: $PORT"

# ============================================
# Kiểm tra frontend build
# ============================================
echo "📁 Checking /usr/share/nginx/html/ ..."
if [ -d "/usr/share/nginx/html" ]; then
    ls -la /usr/share/nginx/html/ || echo "⚠️ Cannot list directory"
    if [ -f "/usr/share/nginx/html/index.html" ]; then
        echo "✅ index.html EXISTS ($(wc -c < /usr/share/nginx/html/index.html) bytes)"
    else
        echo "❌ index.html NOT FOUND"
    fi
else
    echo "❌ Directory /usr/share/nginx/html does NOT exist"
fi

# ============================================
# ✅ SỬA: Dùng nginx.conf đã có trong image
# ============================================
echo "🧹 Cleaning nginx default configs..."
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true

# ✅ KIỂM TRA: nginx.conf đã được copy trong Dockerfile chưa
if [ -f "/etc/nginx/conf.d/default.conf" ]; then
    echo "✅ Found /etc/nginx/conf.d/default.conf (copied from Dockerfile)"
else
    echo "❌ /etc/nginx/conf.d/default.conf not found!"
    echo "📂 Contents of /etc/nginx/conf.d/:"
    ls -la /etc/nginx/conf.d/ 2>/dev/null || echo "Directory empty"
    exit 1
fi

# ✅ THAY THẾ PORT trong config
echo "🔧 Replacing port ${PORT} in nginx config..."
sed -i "s/listen 10000/listen ${PORT}/g" /etc/nginx/conf.d/default.conf

# ✅ HIỂN THỊ CONFIG
echo "📝 Final nginx config:"
cat /etc/nginx/conf.d/default.conf

# ============================================
# Test và khởi động nginx
# ============================================
echo "🧪 Testing nginx config..."
nginx -t || exit 1

echo "🌐 Starting nginx..."
nginx

# ============================================
# Khởi động backend
# ============================================
echo "📡 Starting Backend on port 8000..."
cd /app
export PYTHONUNBUFFERED=1

# Pre-check imports
python -c "
import sys
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/backend')
try:
    from backend.main import app
    from backend.app.config import settings
    print('✅ FastAPI app import OK')
    print(f'✅ Config loaded: {settings.APP_NAME if hasattr(settings, \"APP_NAME\") else \"OK\"}')
except Exception as e:
    print(f'❌ Import error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
" || exit 1

# Giới hạn thread
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

# Start uvicorn
echo "🚀 Starting uvicorn..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level info &
BACKEND_PID=$!

# ============================================
# Đợi backend sẵn sàng
# ============================================
echo "⏳ Waiting for backend..."
for i in {1..60}; do
    if curl -s --max-time 2 http://localhost:8000/api/v1/health 2>/dev/null | grep -q "healthy\|ok"; then
        echo "✅ Backend ready!"
        break
    fi
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ Backend died!"
        exit 1
    fi
    sleep 2
done

# ============================================
# ✅ TEST: Kiểm tra nginx đang serve đúng
# ============================================
echo "🧪 Testing nginx at port ${PORT}..."
sleep 2
TEST_RESPONSE=$(curl -s --max-time 5 http://localhost:${PORT}/ 2>/dev/null || echo "CONNECTION_FAILED")

if echo "$TEST_RESPONSE" | grep -q "<!DOCTYPE html>\|<html"; then
    echo "✅ SUCCESS: Nginx is serving HTML!"
    echo "📄 Response preview:"
    echo "$TEST_RESPONSE" | head -5
elif echo "$TEST_RESPONSE" | grep -q "service.*Sentiment\|Sentiment Analysis API"; then
    echo "❌ WARNING: Nginx is serving JSON from backend instead of HTML!"
    echo "🔍 Response:"
    echo "$TEST_RESPONSE" | head -10
else
    echo "⚠️ Response from port ${PORT}:"
    echo "$TEST_RESPONSE" | head -10
fi

# Reload nginx
echo "🔄 Reloading nginx..."
nginx -s reload 2>/dev/null || true

echo "✅ Service ready at port $PORT"
echo "🌐 URL: http://localhost:$PORT"

# Keep alive
wait $BACKEND_PID
