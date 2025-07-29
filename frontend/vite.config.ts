import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

export default defineConfig({
  plugins: [vue(), vueDevTools()],
  resolve: {
    alias: {
      '@': new URL('./src', import.meta.url).pathname
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'https://pww22u41ud.execute-api.us-east-1.amazonaws.com/Prod',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})