import { createApp } from 'vue';
import './style.css';
import App from './App.vue';
import router from './router';
import { createPinia } from "pinia";
import '@wikimedia/codex/dist/codex.style.css';
import i18n from './i18n';


const app = createApp(App);
app.use(createPinia());
app.use(router);
app.use(i18n)

app.mount('#app');

