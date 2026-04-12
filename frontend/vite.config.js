import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // ✅ ĐÃ THÊM: Ép serve SPA mode
  appType: 'spa',
  server: {
    port: 5173,
    host: true,
    strictPort: true, // Không đổi port nếu bị chiếm
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          charts: ['recharts'],
          utils: ['axios', 'framer-motion', 'lucide-react']
        }
      }
    }
  }
})
