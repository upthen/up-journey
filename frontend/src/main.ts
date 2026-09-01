import { createPinia } from 'pinia'
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import App from './App.vue'
import { router } from './router'
import './styles/index.css'
import './styles/flow.css'
import 'element-plus/dist/index.css'
import './styles/admin.css'
import '@wangeditor/editor/dist/css/style.css'

createApp(App).use(createPinia()).use(router).use(ElementPlus, { locale: zhCn }).mount('#app')
