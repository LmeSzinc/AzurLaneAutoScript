import {createApp} from 'vue';
import App from '/@/App.vue';
import router from '/@/router';
import {setupI18n} from '/@/locales/setupI18n';
import {setupThemeSetting} from '/@/settings/themeSetting';
import {setupStore} from '/@/store';
import './index.less';
import {initAppConfigStore} from '/@/logics/initAppConfigStore';

async function bootstrap() {
  const app = createApp(App);
  setupStore(app);

  await initAppConfigStore();

  await setupI18n(app);

  app.use(router);

  setupThemeSetting();

  app.mount('#app');
}

await bootstrap();
