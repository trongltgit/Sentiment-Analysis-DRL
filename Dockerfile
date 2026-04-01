# ==================== STAGE 1: Build Frontend ====================
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Cài dependencies
RUN npm install --no-audit --no-fund --prefer-offline

# Copy toàn bộ code frontend
COPY frontend/ ./

# Debug files
RUN echo "=== Files in /app ===" && ls -la

# Tạo index.html nếu chưa có (rất quan trọng vì repo của bạn đang thiếu file này)
RUN if [ ! -f index.html ]; then \
      echo "Creating index.html..."; \
      cat > index.html << 'EOF' && \
      echo "✅ index.html đã được tạo"; \
    else \
      echo "✅ index.html đã tồn tại"; \
    fi

<!DOCTYPE html>
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Sentiment Analysis</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
EOF

# Build production
RUN npm run build

# Kiểm tra kết quả
RUN echo "=== Build result ===" && ls -la dist || echo "❌ Không tìm thấy thư mục dist"
