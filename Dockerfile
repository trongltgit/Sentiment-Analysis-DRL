# ===== STAGE 1: Build Frontend =====
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ===== STAGE 2: Backend + Serve Frontend =====
FROM python:3.10-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend từ stage 1
COPY --from=frontend-builder /app/frontend/dist ./backend/static/

WORKDIR /app/backend

# Port
EXPOSE 10000

# Run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
