#!/bin/bash

echo "🚀 Starting AI Sentiment Analysis Service..."

# Start backend ở background
echo "📡 Starting Backend API on port 8000..."
cd /app/backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 &

# Đợi backend sẵn sàng
echo "⏳ Waiting for backend..."
sleep 5

# Test backend
if curl -s http://localhost:8000/api/v1/health > /dev/null; then
    echo "✅ Backend is running!"
else
    echo "⚠️ Backend may not be ready, continuing anyway..."
fi

# Start nginx (foreground)
echo "🌐 Starting Nginx on port 10000..."
nginx -g 'daemon off;'
