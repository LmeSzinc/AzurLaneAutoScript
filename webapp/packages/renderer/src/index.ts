import {createApp} from 'vue';
import App from '/@/App.vue';
import router from '/@/router';
import './index.css';
import {setupI18n} from '/@/locales/setupI18n';
import {setupThemeSetting} from '/@/setting/themeSetting';
import {setupStore} from '/@/store';

async function bootstrap() {
  const app = createApp(App);

  app.use(router);

  setupThemeSetting();

  setupStore(app);

  setupI18n(app);

  app.mount('#app');
}

await bootstrap();
