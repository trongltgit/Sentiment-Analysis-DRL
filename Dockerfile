# ==================== STAGE 1: Build Frontend ====================
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copy package.json trước
COPY frontend/package*.json ./

# Cài dependencies
RUN npm install

# Copy toàn bộ frontend
COPY frontend/ ./

# === DEBUG quan trọng ===
RUN echo "=== Danh sách file trong /app ==="
RUN ls -la
RUN echo "=== Kiểm tra index.html ==="
RUN ls -la index.html || echo "❌ KHÔNG TÌM THẤY index.html"

# Vite mặc định cần index.html ở root → tạo file index.html đơn giản
RUN if [ ! -f index.html ]; then \
      echo '<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8"><title>Sentiment Analysis</title></head><body><div id="root"></div><script type="module" src="/src/main.tsx"></script></body></html>' > index.html; \
      echo "✅ Đã tạo file index.html tạm thời"; \
    fi

# Build
RUN npm run build
