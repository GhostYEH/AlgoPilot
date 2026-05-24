import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backendPort = env.VITE_BACKEND_PORT || '9000'
  const backendTarget = `http://127.0.0.1:${backendPort}`

  return {
  plugins: [
    vue(),
    AutoImport({
      imports: ['vue', 'vue-router'],
      resolvers: [ElementPlusResolver()],
      dts: 'src/types/auto-imports.d.ts',
    }),
    Components({
      resolvers: [ElementPlusResolver({ importStyle: 'css' })],
      dts: 'src/types/components.d.ts',
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  optimizeDeps: {
    include: [
      '@element-plus/icons-vue',
      'element-plus/es/components/timeline/style/css',
      'element-plus/es/components/timeline-item/style/css',
      'element-plus/es/components/collapse/style/css',
      'element-plus/es/components/collapse-item/style/css',
    ],
  },
  server: {
    port: 5173,
    proxy: {
      // 可选：开发时代理到后端，避免浏览器 CORS；当前后端已开启 CORS，直连亦可
      '/api': {
        target: backendTarget,
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return
          if (id.includes('element-plus')) return 'element-plus'
          if (id.includes('codemirror') || id.includes('@codemirror')) return 'codemirror'
          if (id.includes('vue') || id.includes('vue-router')) return 'vue-vendor'
        },
      },
    },
  },
  }
})
