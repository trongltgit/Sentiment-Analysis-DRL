# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app

# Copy từ thư mục frontend (vì context là root)
COPY frontend/package*.json ./

# Cài dependencies
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copy toàn bộ source từ frontend/
COPY frontend/ .

# Build
RUN npm run build

# Stage 2: Production với Nginx
FROM nginx:alpine

# Copy build output
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Copy nginx config từ frontend/
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
