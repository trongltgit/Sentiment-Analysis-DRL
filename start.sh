#!/bin/bash

echo "🚀 Starting AI Sentiment Analysis Service..."

PORT=${PORT:-10000}
echo "🔧 Using PORT: $PORT"

# Thay port trong nginx.conf
sed -i "s/listen .*/listen $PORT;/g" /etc/nginx/conf.d/default.conf

echo "📡 Starting Backend (FastAPI) on port 8000..."
cd /app
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level info &

# Đợi backend khởi động
echo "⏳ Waiting for backend to be ready..."
sleep 8

# Kiểm tra backend
if curl -s http://localhost:8000/api/v1/health > /dev/null; then
    echo "✅ Backend is running successfully!"
else
    echo "⚠️ Warning: Backend health check failed!"
fi

echo "🌐 Starting Nginx on port $PORT..."
nginx -g 'daemon off;'
