import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'katex/dist/katex.min.css'
import App from './App.vue'
import router from './router'
import './styles/main.css'

// 共享设计系统组件（全局注册，所有页面免 import 直接使用）
import PageHeader from './components/PageHeader.vue'
import GkCard from './components/GkCard.vue'
import EmptyState from './components/EmptyState.vue'
import GkSkeleton from './components/GkSkeleton.vue'

const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}
app.component('PageHeader', PageHeader)
app.component('GkCard', GkCard)
app.component('EmptyState', EmptyState)
app.component('GkSkeleton', GkSkeleton)

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })

app.mount('#app')
