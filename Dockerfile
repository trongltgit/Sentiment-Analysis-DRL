# ==================== STAGE 1: Build Frontend ====================
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copy package.json và package-lock.json (nếu có)
COPY frontend/package*.json ./

# Cài dependencies
# Dùng npm install thay vì npm ci vì chưa có package-lock.json
RUN npm install

# Copy toàn bộ source code frontend
COPY frontend/ ./

# Debug để kiểm tra file có được copy đúng không
RUN ls -la

# Kiểm tra xem index.html có tồn tại không
RUN ls -la index.html || echo "=== KHÔNG TÌM THẤY index.html ==="

# Build production
RUN npm run build
