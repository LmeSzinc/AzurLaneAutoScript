import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { loadI18n } from './api/i18n'
import { connectWs, refreshStatus } from './api/store'

async function bootstrap() {
  // Fetch status (theme/language) before mounting so i18n and the theme
  // initialize with the persisted settings.
  try {
    await refreshStatus()
  } catch {
    // backend not ready yet; the WS reconnection will refresh later
  }
  try {
    await loadI18n()
  } catch {
    // backend not ready yet
  }
  const app = createApp(App)
  app.use(router)
  app.mount('#app')
  connectWs()
}

void bootstrap()
