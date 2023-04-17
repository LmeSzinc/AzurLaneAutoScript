import {createApp} from 'vue';
import App from '/@/App.vue';
import router from '/@/router';
import './index.css';
import {setupI18n} from '/@/locales/setupI18n';
import {setupThemeSetting} from '/@/setting/themeSetting';


async function bootstrap() {
    const app = createApp(App);

    app.use(router);

    setupThemeSetting();

    setupI18n(app);

    app.mount('#app');
}

await bootstrap();
