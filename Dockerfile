# ==========================================
# Dockerfile - Đặt ở ROOT của repo
# ==========================================

# Stage 1: Build React App
FROM node:18-alpine AS frontend-builder

WORKDIR /app

# Copy dependencies
COPY frontend/package*.json ./

# Cài dependencies (bỏ qua audit để nhanh hơn)
RUN npm install --legacy-peer-deps --no-audit

# Copy source code
COPY frontend/ ./

# Build production
RUN npm run build

# Stage 2: Nginx Server
FROM nginx:alpine

# Copy build output
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Tạo nginx.conf inline (không cần file riêng)
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    error_page 500 502 503 504 /50x.html; \
    location = /50x.html { \
        root /usr/share/nginx/html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
