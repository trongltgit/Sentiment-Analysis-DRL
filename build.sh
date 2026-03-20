#!/bin/bash

echo "🚀 Building Sentiment Analysis DRL System..."

# Backend dependencies
echo "📦 Installing backend dependencies..."
cd backend
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('vader_lexicon')"

# Create directories
mkdir -p models data

# Download pre-trained models (nếu có lưu trên cloud)
# wget -O models/sentiment_model.pt https://your-storage/sentiment_model.pt
# wget -O models/drl_agent.zip https://your-storage/drl_agent.zip

echo "✅ Build completed!"
