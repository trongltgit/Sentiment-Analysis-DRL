# ==================== STAGE 1: Build Frontend ====================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci --only=production --no-audit --no-fund

COPY frontend/ ./
RUN npm run build

# ==================== STAGE 2: Python Backend + Nginx ====================
FROM python:3.11-slim

WORKDIR /app

# Cài system dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /app/logs /tmp

# Cài Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Đảm bảo có __init__.py cho tất cả packages
RUN find backend -type d -exec touch {}/__init__.py \; 2>/dev/null || true

# Copy frontend build vào nginx
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

# Copy nginx config (xóa default trước để tránh conflict)
RUN rm -f /etc/nginx/sites-enabled/default /etc/nginx/conf.d/default.conf 2>/dev/null || true
COPY frontend/nginx.conf /etc/nginx/conf.d/app.conf

# Copy start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 10000

CMD ["/start.sh"]
