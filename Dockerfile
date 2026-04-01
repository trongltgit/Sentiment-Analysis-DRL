# ==================== STAGE 1: Build Frontend ====================
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copy package files trước để cache
COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund --prefer-offline

# Copy toàn bộ source frontend
COPY frontend/ ./

# Tạo index.html (vì repo của bạn chưa có file này)
RUN echo "Creating index.html..." && \
    cat > index.html << 'EOT'
<!DOCTYPE html>
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="AI Sentiment Analysis using Deep Reinforcement Learning" />
    <title>AI Sentiment Analysis DRL</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
EOT

RUN echo "✅ index.html đã được tạo"

# Build production
RUN npm run build

# Kiểm tra kết quả
RUN echo "=== Build result ===" && ls -la dist

# ==================== STAGE 2: Nginx Production ====================
FROM nginx:alpine

# Copy build output
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Copy nginx config (bạn đã có file này trong frontend/)
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
