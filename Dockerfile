# ==================== STAGE 1: Build Frontend ====================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund

COPY frontend/ ./
RUN npm run build

# ==================== STAGE 2: Python Backend + Nginx ====================
FROM python:3.11-slim

WORKDIR /app

# Cài system dependencies - SỬA LẠI CHO DEBIAN 12
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    curl \
    chromium \
    chromium-driver \
    # Core libs (sửa tên cho Debian 12)
    libglib2.0-0 \
    libnss3 \
    libfontconfig1 \
    libxss1 \
    libasound2 \
    libxtst6 \
    libgtk-3-0 \
    libgbm-dev \
    libxshmfence-dev \
    # Thêm libs cần thiết cho Chromium
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libxtst6 \
    libnss3 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxkbcommon0 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && mkdir -p /app/logs /tmp /run/nginx

# Cài Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# CÀI TORCH CPU
RUN pip install --no-cache-dir torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu 

# Cài transformers
RUN pip install --no-cache-dir transformers==4.35.0

# CÀI PLAYWRIGHT BROWSER
RUN playwright install chromium

# Copy backend code
COPY backend/ ./backend/

# Đảm bảo __init__.py
RUN find backend -type d -exec touch {}/__init__.py \; 2>/dev/null || true

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
