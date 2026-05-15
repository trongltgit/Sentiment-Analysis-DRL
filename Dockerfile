# ============================================================
# Stage 1: Build Frontend
# ============================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund

ARG CACHEBUST=20
RUN echo "Cache bust: $CACHEBUST"

COPY frontend/ ./
RUN rm -rf dist && npm run build && echo "✅ Frontend built" && ls -la dist/

# ============================================================
# Stage 2: Python Backend (lightweight — no torch!)
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python deps — Groq replaces torch (much lighter!)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Backend code
COPY backend/ ./backend/
RUN find backend -type d -exec touch {}/__init__.py \; 2>/dev/null || true

# Frontend static files
RUN mkdir -p /usr/share/nginx/html
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

RUN echo "=== Static files ===" && ls -la /usr/share/nginx/html/

COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 10000
CMD ["/start.sh"]
