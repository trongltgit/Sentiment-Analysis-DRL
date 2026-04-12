#!/bin/bash
set -e

echo "🚀 Starting AI Sentiment Analysis Service..."

# ✅ Lấy PORT từ environment (Render sẽ set)
PORT=${PORT:-10000}
echo "🔧 PORT from env: $PORT"

# ============================================
# Kiểm tra frontend build
# ============================================
echo "📁 Checking /usr/share/nginx/html/ ..."
if [ -d "/usr/share/nginx/html" ]; then
    ls -la /usr/share/nginx/html/
    if [ -f "/usr/share/nginx/html/index.html" ]; then
        echo "✅ index.html EXISTS ($(wc -c < /usr/share/nginx/html/index.html) bytes)"
    else
        echo "❌ index.html NOT FOUND"
        exit 1
    fi
else
    echo "❌ Directory /usr/share/nginx/html does NOT exist"
    exit 1
fi

# ============================================
# ✅ Setup nginx với PORT động
# ============================================
echo "🧹 Cleaning nginx default configs..."
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true

# Kiểm tra template
if [ ! -f "/etc/nginx/conf.d/default.conf.template" ]; then
    echo "❌ Nginx template not found!"
    exit 1
fi

# ✅ Thay thế ${PORT} trong template bằng giá trị thực
echo "🔧 Generating nginx config with PORT=${PORT}..."
export PORT
envsubst '$PORT' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

echo "📝 Final nginx config:"
cat /etc/nginx/conf.d/default.conf

# Test nginx config
echo "🧪 Testing nginx config..."
nginx -t || exit 1

# ============================================
# Start nginx
# ============================================
echo "🌐 Starting nginx on port ${PORT}..."
nginx -g "daemon off;" &
NGINX_PID=$!

# Đợi nginx khởi động
sleep 2

# Test nginx ngay
echo "🧪 Testing nginx at localhost:${PORT}..."
NGINX_TEST=$(curl -s --max-time 3 http://localhost:${PORT}/ 2>&1 || echo "FAILED")
if echo "$NGINX_TEST" | grep -q "<!DOCTYPE html>\|<html"; then
    echo "✅ Nginx is serving HTML correctly!"
elif echo "$NGINX_TEST" | grep -q "service.*Sentiment\|Sentiment Analysis API"; then
    echo "❌ WARNING: Nginx is serving JSON from backend!"
else
    echo "⚠️ Nginx test result: $NGINX_TEST"
fi

# ============================================
# Start backend (chỉ trên localhost)
# ============================================
echo "📡 Starting Backend on port 8000 (localhost only)..."
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
except Exception as e:
    print(f'❌ Import error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
" || exit 1

# Giới hạn thread
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

# ✅ Backend chỉ listen trên localhost (không expose ra ngoài)
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --workers 1 --log-level info &
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

echo "✅ Service ready at port $PORT"
echo "🌐 URL: http://localhost:$PORT"

# Giữ cả 2 process sống
wait $NGINX_PID
