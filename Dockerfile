# ==================== STAGE 1: Build Frontend ====================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy và build frontend
COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund

COPY frontend/ ./
RUN npm run build

# ==================== STAGE 2: Python Backend ====================
FROM python:3.11-slim

WORKDIR /app

# Cài system dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements và cài đặt
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy frontend build vào nginx
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

# 🔴 SỬA: Copy nginx.conf từ frontend/ thay vì root
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# 🔴 SỬA: Copy start.sh từ root (giả sử vẫn ở root)
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Expose port (Render sẽ set $PORT)
EXPOSE 10000

CMD ["/start.sh"]
