import Vue from 'vue';
import { createPinia, PiniaVuePlugin } from 'pinia';
import ElementUI from 'element-ui';
import 'element-ui/lib/theme-chalk/index.css';
import '../app/static/css/main.css'; // Import main styles
import App from './App.vue';

Vue.use(PiniaVuePlugin);
Vue.use(ElementUI);

const pinia = createPinia();

new Vue({
  el: '#app',
  pinia,
  render: h => h(App)
});
