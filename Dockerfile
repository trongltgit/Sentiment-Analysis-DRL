# ============================================
# STAGE 1: Build Frontend
# ============================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund

# Copy source và build
COPY frontend/ ./
RUN npm run build

# ✅ Kiểm tra build output
RUN echo "=== Build output ===" && \
    ls -la /app/frontend/dist/ && \
    echo "=== index.html exists? ===" && \
    test -f /app/frontend/dist/index.html && echo "YES" || echo "NO"

# ============================================
# STAGE 2: Python Backend + Nginx
# ============================================
FROM python:3.11-slim
WORKDIR /app

# Cài đặt nginx và dependencies
RUN apt-get update && \
    apt-get install -y nginx curl && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /app/logs /tmp /run/nginx /usr/share/nginx/html

# Copy backend dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
RUN find backend -type d -exec touch {}/__init__.py \; 2>/dev/null || true

# ============================================
# ✅ Copy frontend build vào nginx
# ============================================
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

# ✅ Kiểm tra sau khi copy
RUN echo "=== After copy to /usr/share/nginx/html ===" && \
    ls -la /usr/share/nginx/html/ && \
    echo "=== index.html content (first 5 lines) ===" && \
    head -5 /usr/share/nginx/html/index.html

# Cleanup nginx default
RUN rm -f /etc/nginx/sites-enabled/default /etc/nginx/conf.d/default.conf 2>/dev/null || true

# Copy nginx config
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 10000
CMD ["/start.sh"]
