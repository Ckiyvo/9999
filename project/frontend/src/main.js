import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import './global.css'; // 引入全局 CSS 文件

const app = createApp(App);
app.use(router);
app.mount('#app');