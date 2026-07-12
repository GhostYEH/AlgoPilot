import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import 'element-plus/theme-chalk/dark/css-vars.css'
import '@/assets/styles/global.css'
import { initTheme } from '@/composables/useTheme'

initTheme()

const app = createApp(App)
app.use(createPinia())
app.use(router)

// 全局错误处理：防止未捕获的异常导致白屏
app.config.errorHandler = (err, _instance, info) => {
  // eslint-disable-next-line no-console
  console.error('[app]', info, err)
}

app.mount('#app')
