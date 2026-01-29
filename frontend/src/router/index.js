import { createRouter, createWebHistory } from 'vue-router';
import EditCounts from '../views/EditCounts.vue';
import EditorCounts from '../views/EditorCounts.vue';
import ReviewerDashboard from '../views/ReviewerDashboard.vue';

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
  },
  {
    path: '/reviewer',
    name: 'ReviewerDashboard',
    component: ReviewerDashboard,
    meta: { requiresAuth: true }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
