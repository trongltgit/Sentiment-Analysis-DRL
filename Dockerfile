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

# Cài system dependencies (non-interactive)
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

# Setup nginx: xóa default, copy config mới
RUN rm -f /etc/nginx/sites-enabled/default /etc/nginx/conf.d/default.conf /etc/nginx/nginx.conf.default
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

EXPOSE 10000

CMD ["/start.sh"]
