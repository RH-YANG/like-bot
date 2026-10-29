import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'



// 브라우저의 /api/* 요청은 back으로, /vnc/* 요청(웹소켓 포함)은 worker의 noVNC로 넘기고 접두어를 제거한다
export default defineConfig({
  plugins: [react()],
  server: {
    watch: { usePolling: true },
    proxy: {
      '/api': {
        target: process.env.API_URL ?? 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/vnc': {
        target: process.env.VNC_URL ?? 'http://localhost:6080',
        ws: true,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/vnc/, ''),
      },
    },
  },
})
