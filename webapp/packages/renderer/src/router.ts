import {createRouter, createWebHashHistory} from 'vue-router';
import Alas from '/@/components/Alas.vue';

const routes = [
  {path: '/', name: 'Alas', component: Alas},
];

export default createRouter({
  routes,
  history: createWebHashHistory(),
});
