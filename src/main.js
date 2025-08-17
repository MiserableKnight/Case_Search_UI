import { createApp } from 'vue';
import { createPinia } from 'pinia';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import '../app/static/css/main.css'; // Import main styles
import './styles/element-plus-overrides.css'; // Import Element Plus style overrides
import App from './App.vue';

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(ElementPlus);

app.mount('#app');
