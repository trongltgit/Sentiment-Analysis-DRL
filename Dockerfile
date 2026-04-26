# File: Dockerfile

# ============================================
# STAGE 1: Build Frontend
# ============================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# ✅ ARG này làm invalidate toàn bộ cache khi thay đổi
ARG CACHEBUST=2

COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund

COPY frontend/ ./

# Xóa dist cũ, build mới hoàn toàn
RUN rm -rf dist && npm run build

# Log để xác nhận build mới
RUN echo "=== Frontend build xong ===" && \
    ls -la /app/frontend/dist/assets/ && \
    echo "=== index.html content ===" && \
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

# Copy frontend build từ stage 1
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

RUN echo "=== /usr/share/nginx/html ===" && \
    ls -la /usr/share/nginx/html/ && \
    echo "=== assets ===" && \
    ls -la /usr/share/nginx/html/assets/

COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 10000
CMD ["/start.sh"]
