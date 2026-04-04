#!/bin/bash

echo "🚀 Starting AI Sentiment Analysis Service..."

# Start backend in background
echo "📡 Starting Backend API on port 8000..."
cd /app/backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 &

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 5

# Check if backend is running
if curl -s http://localhost:8000/api/v1/analysis/test > /dev/null; then
    echo "✅ Backend is running!"
else
    echo "⚠️ Backend may not be ready yet, continuing..."
fi

# Start nginx (foreground)
echo "🌐 Starting Nginx on port 10000..."
nginx -g 'daemon off;'
