# File: Dockerfile

# ============================================
# STAGE 1: Build Frontend
# ============================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./

# ✅ --no-cache buộc npm cài lại, tránh Docker dùng layer cũ
RUN npm install --no-audit --no-fund

COPY frontend/ ./

# ✅ Xóa dist cũ trước khi build để tránh artifact cũ lẫn vào
RUN rm -rf dist && npm run build

RUN echo "=== Build output ===" && \
    ls -la /app/frontend/dist/ && \
    echo "=== index.html ===" && \
    cat /app/frontend/dist/index.html

# ============================================
# STAGE 2: Python Backend
# ============================================
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /usr/share/nginx/html

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
RUN find backend -type d -exec touch {}/__init__.py \; 2>/dev/null || true

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

RUN echo "=== Checking /usr/share/nginx/html ===" && \
    ls -la /usr/share/nginx/html/ && \
    echo "=== JS files ===" && \
    ls -la /usr/share/nginx/html/assets/

COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 10000
CMD ["/start.sh"]
