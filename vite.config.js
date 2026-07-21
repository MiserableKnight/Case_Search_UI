import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 前端构建配置：
// - 开发：npm run dev，/api 代理到 Flask（127.0.0.1:5000）
// - 构建：npm run build，产物输出到 app/static/dist，由 Flask 直接托管；
//   固定文件名（不做哈希），便于模板引用与 git 提交
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:5000',
    },
  },
  build: {
    outDir: 'app/static/dist',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        entryFileNames: 'assets/[name].js',
        chunkFileNames: 'assets/[name].js',
        assetFileNames: 'assets/[name].[ext]',
      },
    },
  },
})
