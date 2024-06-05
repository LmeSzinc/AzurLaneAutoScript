import {createApp} from 'vue';
import App from '/@/App.vue';
import router from '/@/router';
import {setupI18n} from '/@/locales/setupI18n';
import {setupThemeSetting} from '/@/settings/themeSetting';
import {setupStore} from '/@/store';
import {initAppConfigStore} from '/@/logics/initAppConfigStore';
import './index.less';
import 'uno.css';

if (import.meta.env.DEV) {
  /**
   * Ensure that the style at development time is consistent with the style after packaging
   */
  import('@arco-design/web-vue/dist/arco.less');
}

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
