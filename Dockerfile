# ==========================================
# Dockerfile - Đặt ở ROOT của repo
# ==========================================

# Stage 1: Build React App
FROM node:18-alpine AS frontend-builder

WORKDIR /app

# Copy package.json trước
COPY frontend/package*.json ./

# Cài dependencies
RUN npm install --legacy-peer-deps --no-audit --progress=false

# Copy toàn bộ frontend (dùng .dockerignore để loại trừ node_modules)
COPY frontend/ ./

# Build production
RUN npm run build

# Stage 2: Nginx Server
FROM nginx:alpine

# Copy build output
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Tạo nginx.conf inline
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
