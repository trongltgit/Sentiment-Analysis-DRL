# File: Dockerfile
# ============================================
# STAGE 1: Build Frontend — LUÔN build mới
# ============================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files trước (layer cache npm install)
COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund

# ✅ CACHEBUST: thêm dòng này và tăng số mỗi lần muốn force rebuild
# Thay đổi số bên dưới = Docker bắt buộc chạy lại từ dòng này trở xuống
ARG CACHEBUST=10
RUN echo "Cache bust: $CACHEBUST"

# Copy toàn bộ source
COPY frontend/ ./

# Build
RUN rm -rf dist && npm run build && echo "BUILD DONE" && ls -la dist/ && ls -la dist/assets/

# ============================================
# STAGE 2: Python Backend
# ============================================
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
RUN find backend -type d -exec touch {}/__init__.py \; 2>/dev/null || true

RUN mkdir -p /usr/share/nginx/html
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

RUN echo "=== HTML dir ===" && ls -la /usr/share/nginx/html/ && \
    echo "=== assets ===" && ls -la /usr/share/nginx/html/assets/

COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 10000
CMD ["/start.sh"]
