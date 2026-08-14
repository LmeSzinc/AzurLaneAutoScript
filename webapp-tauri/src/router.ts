import { createRouter, createWebHashHistory } from 'vue-router'
import Home from '@/views/Home.vue'
import Settings from '@/views/Settings.vue'
import DevTools from '@/views/DevTools.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'home', component: Home },
    { path: '/settings', name: 'settings', component: Settings },
    { path: '/devtools', name: 'devtools', component: DevTools },
  ],
})

export default router
