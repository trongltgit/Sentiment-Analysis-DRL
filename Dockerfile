# ============================================
# STAGE 1: Build Frontend
# ============================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund

COPY frontend/ ./
RUN npm run build

# Kiểm tra build output
RUN echo "=== Build output ===" && \
    ls -la /app/frontend/dist/ && \
    echo "=== index.html exists? ===" && \
    test -f /app/frontend/dist/index.html && echo "YES" || echo "NO"

# ============================================
# STAGE 2: Python Backend (không cần Nginx)
# ============================================
FROM python:3.11-slim
WORKDIR /app

# Cài đặt dependencies (không cần nginx)
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

# Kiểm tra sau khi copy
RUN echo "=== Checking /usr/share/nginx/html ===" && \
    ls -la /usr/share/nginx/html/

COPY start.sh /start.sh
RUN chmod +x /start.sh

# ✅ Chỉ expose 1 port cho Render Web Service
EXPOSE 10000

CMD ["/start.sh"]
