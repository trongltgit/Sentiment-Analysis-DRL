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
# Start FastAPI (serve cả API và static files)
# ============================================
echo "🌐 Starting FastAPI on port ${PORT}..."
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

# Giới hạn thread để tiết kiệm RAM
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

# ✅ Start uvicorn trên 0.0.0.0 để Render có thể truy cập
uvicorn backend.main:app --host 0.0.0.0 --port ${PORT} --workers 1 --log-level info
