import './assets/main.css'

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { enableMockApi } from './utils/mockApi'

// 启用 Mock API（开发测试模式）
enableMockApi()

const app = createApp(App)

app.use(router)

app.mount('#app')
