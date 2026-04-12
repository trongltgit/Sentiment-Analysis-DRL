#!/bin/bash
set -e

echo "🚀 Starting AI Sentiment Analysis Service..."
PORT=${PORT:-10000}
echo "🔧 PORT: $PORT"

# ✅ THÊM: Kiểm tra file tồn tại
echo "📁 Checking frontend build..."
ls -la /usr/share/nginx/html/ || echo "❌ /usr/share/nginx/html not found"
if [ -f /usr/share/nginx/html/index.html ]; then
    echo "✅ index.html exists"
    head -5 /usr/share/nginx/html/index.html
else
    echo "❌ index.html NOT FOUND"
fi

# 1. Cleanup nginx
rm -f /etc/nginx/sites-enabled/default /etc/nginx/conf.d/default.conf 2>/dev/null || true
sed -i "s/listen 10000/listen $PORT/g" /etc/nginx/conf.d/default.conf 2>/dev/null || true

# ✅ THÊM: Hiển thị config để debug
echo "📝 Nginx config:"
cat /etc/nginx/conf.d/default.conf

# 2. Test nginx config
nginx -t || exit 1

# ... rest giữ nguyên
