# Sử dụng Python 3.10 chính thức
FROM python:3.10-slim

WORKDIR /app

# Cài system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt ./backend/

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Copy backend code
COPY backend/ ./backend/

# Set working directory
WORKDIR /app/backend

# Expose port
EXPOSE 10000

# Run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
