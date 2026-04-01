# ==================== STAGE 1: Build Frontend ====================
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copy package files trước
COPY frontend/package*.json ./

# Cài dependencies với timeout và không audit để nhanh hơn
RUN npm install --no-audit --no-fund --prefer-offline

# Copy toàn bộ source code
COPY frontend/ ./

# === DEBUG RẤT QUAN TRỌNG ===
RUN echo "=== Files in /app ===" && ls -la
RUN echo "=== Checking index.html ===" && ls -la index.html || echo "❌ KHÔNG TÌM THẤY index.html !!!"

# Nếu vẫn chưa có index.html → tạo tạm (dành cho dự án Vite React)
RUN if [ ! -f index.html ]; then \
      echo 'Creating missing index.html...'; \
      cat > index.html << 'EOF'
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Sentiment Analysis</title>
</head>
<body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
</body>
</html>
EOF
    fi

# Build production
RUN npm run build

# Kiểm tra kết quả build
RUN echo "=== Build output ===" && ls -la dist || echo "❌ Không có thư mục dist"
