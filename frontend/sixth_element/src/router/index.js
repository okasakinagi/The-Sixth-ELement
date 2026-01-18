import { createRouter, createWebHistory } from 'vue-router'
import SurveyManagementView from '../views/SurveyManagementView.vue'
import TaskHallView from '../views/TaskHallView.vue'
import ProfileView from '../views/ProfileView.vue'
import SurveyBuilderView from '../views/SurveyBuilderView.vue'
import SurveyAnalyticsView from '../views/SurveyAnalyticsView.vue'
import PointsRecordView from '../views/PointsRecordView.vue'
import SurveyFillView from '../views/SurveyFillView.vue'
import AuthView from '../views/AuthView.vue'

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
      name: 'survey-new',
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
      path: '/profile',
      name: 'profile',
      component: ProfileView,
      meta: { requiresAuth: true },
    },
    {
      path: '/points',
      name: 'points-record',
      component: PointsRecordView,
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

  next()
})

export default router
