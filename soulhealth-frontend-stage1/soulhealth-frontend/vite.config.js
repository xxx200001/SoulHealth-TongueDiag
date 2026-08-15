import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 所有 /api 与 /health 均代理到统一 FastAPI 后端 (server.py:9000)
export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,
    port: 5173,
    allowedHosts: true,
    proxy: {
      '/api': 'http://localhost:9000',
      '/health': 'http://localhost:9000',
      '/bio': 'http://localhost:9000',
    },
  },
})
