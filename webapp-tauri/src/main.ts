import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { connectWs, refreshStatus } from './api/store'

const app = createApp(App)
app.use(router)
app.mount('#app')

void refreshStatus()
connectWs()
