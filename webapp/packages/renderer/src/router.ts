import {createRouter, createWebHashHistory} from 'vue-router';
import Alas from '/@/components/Alas.vue';

const routes = [
  {path: '/', name: 'Loading', component: () => import('./views/LoadingPage.vue')},
  {path: '/Install', name: 'InstallPage', component: () => import('./views/InstallAlas.vue')},
  {path: '/Launch', name: 'LaunchPage', component: () => import('./views/Launch.vue')},
  {path: '/Import', name: 'ImportConfig', component: () => import('./views/ImportConfig.vue')},
  {path: '/Alas', name: 'Alas', component: Alas},
];

export default createRouter({
  routes,
  history: createWebHashHistory(),
});
