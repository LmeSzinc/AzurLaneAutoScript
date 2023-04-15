import {createApp} from 'vue';
import App from '/@/App.vue';
import router from '/@/router';
import './index.css';

if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.documentElement.classList.add('dark');
} else {
    document.documentElement.classList.remove('dark');
}

async function bootstrap() {
    const app = createApp(App);
    app.use(router);
    app.mount('#app');
}

bootstrap();
