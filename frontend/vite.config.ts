import { fileURLToPath, URL } from 'node:url'

import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),
    VitePWA({
      // 发新版后 SW 自动接管：下次访问即更新，家庭应用无需提示弹窗
      registerType: 'autoUpdate',
      injectRegister: 'auto',
      includeAssets: ['favicon.svg', 'favicon.ico', 'apple-touch-icon.png'],
      manifest: {
        name: '游迹 · Up Journey',
        short_name: '游迹',
        description: '全屏地图上的家庭足迹：家庭旅游记录',
        lang: 'zh-CN',
        theme_color: '#F8F6F2',
        background_color: '#F8F6F2',
        display: 'standalone',
        start_url: '/',
        icons: [
          { src: '/icons/pwa-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/pwa-512.png', sizes: '512x512', type: 'image/png' },
          { src: '/icons/pwa-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        // 预缓存整个应用外壳 + china.json（离线也能渲染地图底图）；照片等大媒体走 /api，不缓存
        globPatterns: ['**/*.{js,css,html,svg,png,ico,webmanifest,json}'],
        navigateFallbackDenylist: [/^\/api\//],
      },
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
  build: {
    chunkSizeWarningLimit: 2000, // echarts/wangeditor 体积可控（局域网部署，无需分包优化）
  },
})
