#!/bin/bash
set -e

echo "🚀 Starting AI Sentiment Analysis Service..."
PORT=${PORT:-10000}
echo "🔧 PORT: $PORT"

# ============================================
# ✅ THÊM: Kiểm tra thư mục frontend TRƯỚC
# ============================================
echo "📁 Checking /usr/share/nginx/html/ ..."
if [ -d "/usr/share/nginx/html" ]; then
    ls -la /usr/share/nginx/html/ || echo "⚠️ Cannot list directory"
    if [ -f "/usr/share/nginx/html/index.html" ]; then
        echo "✅ index.html EXISTS"
        echo "📄 First 10 lines of index.html:"
        head -10 /usr/share/nginx/html/index.html
    else
        echo "❌ index.html NOT FOUND in /usr/share/nginx/html/"
        echo "📂 Contents of /usr/share/nginx/html/:"
        find /usr/share/nginx/html/ -type f -name "*" 2>/dev/null | head -20 || echo "Directory empty or not accessible"
    fi
else
    echo "❌ Directory /usr/share/nginx/html does NOT exist"
fi

# ============================================
# 1. Cleanup nginx default configs
# ============================================
echo "🧹 Cleaning nginx default configs..."
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
rm -f /etc/nginx/conf.d/default.conf 2>/dev/null || true

# ============================================
# ✅ THÊM: Copy nginx config nếu chưa có
# ============================================
if [ -f "/app/frontend/nginx.conf" ]; then
    echo "📝 Copying nginx.conf from /app/frontend/nginx.conf..."
    cp /app/frontend/nginx.conf /etc/nginx/conf.d/default.conf
else
    echo "⚠️ /app/frontend/nginx.conf not found, checking /etc/nginx/conf.d/default.conf..."
fi

# ✅ THÊM: Replace port trong nginx config
echo "🔧 Replacing port ${PORT} in nginx config..."
sed -i "s/listen 10000/listen ${PORT}/g" /etc/nginx/conf.d/default.conf 2>/dev/null || true
sed -i "s/listen 10000/listen ${PORT}/g" /etc/nginx/sites-enabled/default 2>/dev/null || true

# ✅ THÊM: Hiển thị nginx config để debug
echo "📝 Final nginx config:"
cat /etc/nginx/conf.d/default.conf

# ============================================
# 2. Test nginx config
# ============================================
echo "🧪 Testing nginx config..."
nginx -t || exit 1

# ============================================
# 3. Start nginx
# ============================================
echo "🌐 Starting nginx..."
nginx

# ============================================
# 4. Start backend
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

# Giới hạn thread để tiết kiệm RAM
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

# Start uvicorn
echo "🚀 Starting uvicorn..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level info &
BACKEND_PID=$!

# ============================================
# 5. Wait for backend
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
# ✅ THÊM: Test nginx đang serve đúng không
# ============================================
echo "🧪 Testing nginx is serving index.html..."
sleep 1
if curl -s --max-time 5 http://localhost:${PORT}/ | grep -q "<!DOCTYPE html>\|<html"; then
    echo "✅ Nginx is serving HTML correctly!"
elif curl -s --max-time 5 http://localhost:${PORT}/ | grep -q "service.*Sentiment"; then
    echo "❌ WARNING: Nginx is serving JSON from backend instead of HTML!"
    echo "🔍 Response from port ${PORT}:"
    curl -s http://localhost:${PORT}/ | head -5
else
    echo "⚠️ Unexpected response from nginx:"
    curl -s http://localhost:${PORT}/ | head -10
fi

# ============================================
# 6. Reload nginx
# ============================================
echo "🔄 Reloading nginx..."
nginx -s reload || true

echo "✅ Service ready at port $PORT"
echo "🌐 URL: http://localhost:$PORT"

# Keep alive
wait $BACKEND_PID
