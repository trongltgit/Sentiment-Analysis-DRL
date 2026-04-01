# ==================== STAGE 1: Build Frontend ====================
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Cài dependencies
RUN npm install --no-audit --no-fund --prefer-offline

# Copy toàn bộ frontend code
COPY frontend/ ./

# Debug
RUN echo "=== Files in /app ===" && ls -la

# Tạo index.html nếu chưa có (dự án của bạn đang thiếu file này)
RUN test -f index.html || ( \
      echo "Creating index.html for Vite..." && \
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
      && echo "✅ index.html đã được tạo" )

# Build production
RUN npm run build

# Kiểm tra kết quả build
RUN echo "=== Build result ===" && ls -la dist || echo "❌ Không có thư mục dist"
