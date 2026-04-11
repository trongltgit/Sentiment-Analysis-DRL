# ==================== STAGE 1: Build Frontend ====================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# FIX: Dùng npm install thay vì npm ci với --only (npm ci không hỗ trợ --only)
RUN npm install --omit=dev --no-audit --no-fund

# Copy source và build
COPY frontend/ ./
RUN npm run build

# ==================== STAGE 2: Python Backend + Nginx ====================
FROM python:3.11-slim

WORKDIR /app

# Cài system dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    curl \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && mkdir -p /app/logs /tmp /run/nginx

# Cài Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Đảm bảo __init__.py tồn tại
RUN touch backend/__init__.py 2>/dev/null || true && \
    find backend -type d -exec touch {}/__init__.py \; 2>/dev/null || true

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

# Setup nginx
RUN rm -f /etc/nginx/sites-enabled/default /etc/nginx/conf.d/default.conf 2>/dev/null || true
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 10000

CMD ["/start.sh"]
