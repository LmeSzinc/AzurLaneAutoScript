import {createRouter, createWebHashHistory} from 'vue-router';
import Home from '/@/components/Home.vue';

const routes = [
  {path: '/', name: 'Home', component: Home},
  {path: '/about', name: 'About', component: () => import('/@/components/About.vue')}, // Lazy load route component
];

export default createRouter({
  routes,
  history: createWebHashHistory(),
});
