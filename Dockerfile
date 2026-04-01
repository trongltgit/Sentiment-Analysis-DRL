# ==================== STAGE 1: Build Frontend ====================
FROM node:20-alpine AS frontend-builder
WORKDIR /app

# Copy package files trước để cache tốt hơn
COPY frontend/package*.json ./

# Cài dependencies (dùng ci để ổn định hơn)
RUN npm ci

# Copy toàn bộ source frontend (bao gồm index.html, vite.config, src, ...)
COPY frontend/ ./

# Debug: kiểm tra xem index.html có thực sự được copy không
RUN ls -la
RUN ls -la /app || echo "Không tìm thấy thư mục /app"
RUN find /app -name "index.html" || echo "Không tìm thấy index.html"

# Build production
RUN npm run build
