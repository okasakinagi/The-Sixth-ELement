import { createRouter, createWebHistory } from 'vue-router'
import SurveyManagementView from '../views/SurveyManagementView.vue'
import TaskHallView from '../views/TaskHallView.vue'
import ProfileView from '../views/ProfileView.vue'
import SurveyBuilderView from '../views/SurveyBuilderView.vue'
import SurveyAnalyticsView from '../views/SurveyAnalyticsView.vue'
import SurveyEntryView from '../views/SurveyEntryView.vue'
import SurveyAiPromptView from '../views/SurveyAiPromptView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      redirect: '/profile',
    },
    {
      path: '/profile',
      name: 'userProfile',
      component: () => import('../views/UserProfileView.vue'),
    },
    {
      path: '/profile/edit',
      name: 'editProfile',
      component: () => import('../views/EditProfileView.vue'),
    },
    {
      path: '/task-hall',
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
      name: 'survey-entry',
      component: SurveyEntryView,
    },
    {
      path: '/survey/new/ai',
      name: 'survey-ai',
      component: SurveyAiPromptView,
    },
    {
      path: '/survey/new/editor',
      name: 'survey-editor',
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
