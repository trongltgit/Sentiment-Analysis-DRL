# ============================================
# STAGE 1: Build Frontend
# ============================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund

COPY frontend/ ./
RUN npm run build

# ✅ Kiểm tra build output
RUN echo "=== Build output ===" && \
    ls -la /app/frontend/dist/ && \
    echo "=== index.html exists? ===" && \
    test -f /app/frontend/dist/index.html && echo "YES" || echo "NO" && \
    echo "=== nginx.conf exists? ===" && \
    test -f /app/frontend/nginx.conf && echo "YES" || echo "NO"

# ============================================
# STAGE 2: Python Backend + Nginx
# ============================================
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && \
    apt-get install -y nginx curl && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /app/logs /tmp /run/nginx /usr/share/nginx/html

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
RUN find backend -type d -exec touch {}/__init__.py \; 2>/dev/null || true

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

# ✅ THÊM: Copy nginx.conf từ builder stage
COPY --from=frontend-builder /app/frontend/nginx.conf /etc/nginx/conf.d/default.conf

# ✅ Kiểm tra sau khi copy
RUN echo "=== Checking /usr/share/nginx/html ===" && \
    ls -la /usr/share/nginx/html/ && \
    echo "=== Checking nginx.conf ===" && \
    cat /etc/nginx/conf.d/default.conf | head -20

COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 10000
CMD ["/start.sh"]
