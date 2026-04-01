# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app

# Copy package files từ thư mục hiện tại
COPY package*.json ./

# Cài dependencies
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copy toàn bộ source
COPY . .

# Build
RUN npm run build

# Stage 2: Production với Nginx
FROM nginx:alpine

# Copy build output
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
