import { createRouter, createWebHistory } from 'vue-router'
import SurveyManagementView from '../views/SurveyManagementView.vue'
import TaskHallView from '../views/TaskHallView.vue'
import ProfileView from '../views/ProfileView.vue'
import SurveyBuilderView from '../views/SurveyBuilderView.vue'
import SurveyAnalyticsView from '../views/SurveyAnalyticsView.vue'
import SurveyEntryView from '../views/SurveyEntryView.vue'
import SurveyAiPromptView from '../views/SurveyAiPromptView.vue'
import PointsRecordView from '../views/PointsRecordView.vue'
import SurveyFillView from '../views/SurveyFillView.vue'
import AuthView from '../views/AuthView.vue'
import HelpCenterView from '../views/HelpCenterView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'auth',
      component: AuthView,
      meta: { requiresAuth: false },
    },
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
      meta: { requiresAuth: true },
    },
    {
      path: '/surveys',
      name: 'survey-management',
      component: SurveyManagementView,
      meta: { requiresAuth: true },
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
      meta: { requiresAuth: true },
    },
    {
      path: '/survey/:id',
      name: 'survey-builder',
      component: SurveyBuilderView,
      meta: { requiresAuth: true },
    },
    {
      path: '/survey/:id/fill',
      name: 'survey-fill',
      component: SurveyFillView,
      meta: { requiresAuth: true },
    },
    {
      path: '/survey/:id/analytics',
      name: 'survey-analytics',
      component: SurveyAnalyticsView,
      meta: { requiresAuth: true },
    },
    {
      path: '/points',
      name: 'points-record',
      component: PointsRecordView,
      meta: { requiresAuth: true },
    },
    {
      path: '/help',
      name: 'help-center',
      component: HelpCenterView,
      meta: { requiresAuth: true },
    },
  ],
})

// 全局路由守卫：检查认证状态
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  const requiresAuth = to.meta.requiresAuth !== false

  // 若需要认证但无token，重定向到登录页
  if (requiresAuth && !token) {
    next({ name: 'auth', query: { redirect: to.fullPath } })
    return
  }

  // 若在登录页且已认证，重定向到主页
  if (to.name === 'auth' && token) {
    next({ name: 'task-hall' })
    return
  }

  // 保存来源路径到帮助中心
  if (to.name === 'help-center' && from.name) {
    localStorage.setItem('help_center_referrer', from.fullPath)
  }

  next()
})

export default router
