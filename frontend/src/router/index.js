import { createRouter, createWebHistory } from 'vue-router';
import EditCounts from '../views/EditCounts.vue';
import EditorCounts from '../views/EditorCounts.vue';

const routes = [
  {
    path: '/',
    name: 'EditCounts',
    component: EditCounts
  },
  {
    path: '/editor-counts',
    name: 'EditorCounts',
    component: EditorCounts
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
