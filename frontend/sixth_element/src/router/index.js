import { createRouter, createWebHistory } from 'vue-router'
import SurveyManagementView from '../views/SurveyManagementView.vue'
import TaskHallView from '../views/TaskHallView.vue'
import ProfileView from '../views/ProfileView.vue'
import SurveyBuilderView from '../views/SurveyBuilderView.vue'
import SurveyAnalyticsView from '../views/SurveyAnalyticsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'task-hall',
      component: TaskHallView,
    },
    {
      path: '/surveys',
      name: 'survey-management',
      component: SurveyManagementView,
    },
    {
      path: '/survey/new',
      name: 'survey-new',
      component: SurveyBuilderView,
    },
    {
      path: '/survey/:id',
      name: 'survey-builder',
      component: SurveyBuilderView,
    },
    {
      path: '/survey/:id/analytics',
      name: 'survey-analytics',
      component: SurveyAnalyticsView,
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView,
    },
  ],
})

export default router
