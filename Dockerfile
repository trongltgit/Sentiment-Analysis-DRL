# ==================== STAGE 1: Build Frontend ====================
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copy package files và cài dependencies
COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund --prefer-offline

# Copy toàn bộ code frontend
COPY frontend/ ./

# Debug files
RUN echo "=== Files in /app ===" && ls -la

# Tạo index.html nếu chưa có (dự án của bạn đang thiếu)
RUN if [ ! -f index.html ]; then \
      echo "Creating index.html for Vite..."; \
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
      echo "✅ index.html đã được tạo"; \
    fi

# Build production
RUN npm run build

# Kiểm tra build
RUN echo "=== Build result ===" && ls -la dist

# ==================== STAGE 2: Production ====================
FROM nginx:alpine

# Copy build output từ stage 1
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
