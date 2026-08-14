import { createRouter, createWebHashHistory } from 'vue-router'
import Home from '@/views/Home.vue'
import Develop from '@/views/Develop.vue'
import Manage from '@/views/Manage.vue'
import Settings from '@/views/Settings.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'home', component: Home },
    { path: '/develop', name: 'develop', component: Develop },
    { path: '/manage', name: 'manage', component: Manage },
    { path: '/settings', name: 'settings', component: Settings },
  ],
})

export default router
