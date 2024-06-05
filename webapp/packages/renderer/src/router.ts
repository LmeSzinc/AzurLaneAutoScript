import {createRouter, createWebHashHistory} from 'vue-router';
import Alas from '/@/components/Alas.vue';

const routes = [
<<<<<<< HEAD
  {path: '/', name: 'Loading', component: () => import('./views/LoadingPage.vue')},
  {path: '/Install', name: 'InstallPage', component: () => import('./views/InstallAlas.vue')},
  {path: '/Launch', name: 'LaunchPage', component: () => import('./views/Launch.vue')},
  {path: '/Import', name: 'ImportConfig', component: () => import('./views/ImportConfig.vue')},
  {path: '/Alas', name: 'Alas', component: Alas},
=======
  {path: '/', name: 'Alas', component: Alas},
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
];

export default createRouter({
  routes,
  history: createWebHashHistory(),
});
