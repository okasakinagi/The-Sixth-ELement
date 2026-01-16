// import './assets/main.css' // 移除默认样式，避免宽度限制

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(router)

app.mount('#app')
