import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { usePatientStore } from './store/patient'
import './styles/theme.css'

const app = createApp(App)
app.use(createPinia()).use(router)

// 任何数据变动自动写入 localStorage（跨页面采集不丢失）
const store = usePatientStore()
store.$subscribe(() => store.persist())

app.mount('#app')
