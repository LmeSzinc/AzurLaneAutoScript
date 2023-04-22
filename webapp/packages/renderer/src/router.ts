import {createRouter, createWebHashHistory} from 'vue-router';
import Alas from '/@/components/Alas.vue';

const routes = [
  {path: '/', name: 'InstallPage', component: () => import('./views/InstallAlas.vue')},
  {path: '/Lunch', name: 'LunchPage', component: () => import('./views/Launch.vue')},
  {path: '/Import', name: 'ImportConfig', component: () => import('./views/ImportConfig.vue')},
  {path: '/Alas', name: 'Alas', component: Alas},
];

export default createRouter({
  routes,
  history: createWebHashHistory(),
});
