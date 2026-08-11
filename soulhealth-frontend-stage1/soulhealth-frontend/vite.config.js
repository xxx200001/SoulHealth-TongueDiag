import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// /api 与 /health 均代理到本地 FastAPI（uvicorn pipeline:app --port 8001）
// 注意: 8000 已被 Moment3D 项目占用，SoulHealth 使用 8001
export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,
    port: 5173,
    allowedHosts: true,
    proxy: {
      '/api': 'http://localhost:8001',
      '/health': 'http://localhost:8001',
    },
  },
})

