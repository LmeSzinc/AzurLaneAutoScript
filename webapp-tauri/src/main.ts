import { mount } from 'svelte'
import App from './App.svelte'
import { initRouter } from './router.svelte'
import { loadI18n } from './api/i18n.svelte'
import { connectWs, refreshStatus } from './api/store.svelte'

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
  initRouter()
  mount(App, { target: document.getElementById('app')! })
  connectWs()
}

void bootstrap()
