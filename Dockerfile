# ==================== STAGE 1: Build Frontend ====================
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Cài dependencies
RUN npm install --no-audit --no-fund --prefer-offline

# Copy toàn bộ frontend code
COPY frontend/ ./

# Tạo index.html nếu thiếu (dự án của bạn chưa có)
RUN if [ ! -f index.html ]; then \
      echo "Creating index.html..."; \
      cat > index.html << 'EOF'
<!DOCTYPE html>
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Sentiment Analysis DRL</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
EOF
      echo "✅ index.html đã được tạo"; \
    else \
      echo "✅ index.html đã tồn tại"; \
    fi

# Build
RUN npm run build

# ==================== STAGE 2: Production with Nginx ====================
FROM nginx:alpine

# Copy build output từ stage 1
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Copy nginx config (nếu bạn có file nginx.conf trong frontend/)
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
