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
import ForgotPasswordView from '../views/ForgotPasswordView.vue'
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
      path: '/forgot-password',
      name: 'forgot-password',
      component: ForgotPasswordView,
      meta: { requiresAuth: false },
    },
    {
      path: '/contacts',
      name: 'contacts',
      component: () => import('../views/ContactsView.vue'),
      meta: { requiresAuth: false }, // Temporary: Allow access without login for testing
    },
    {
      path: '/team/:teamId/manage',
      name: 'team-manage',
      component: () => import('../components/contacts/TeamManagement.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/team/invitations',
      name: 'team-invitations',
      component: () => import('../components/contacts/TeamInvitations.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/',
      name: 'home',
      redirect: '/task-hall',
    },
    {
      path: '/profile',
      name: 'profile',
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
      meta: { requiresAuth: false },
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
    {
      path: '/admin/login',
      name: 'admin-login',
      component: () => import('../views/AdminLoginView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/admin',
      name: 'admin-home',
      component: () => import('../views/AdminHomeView.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/dashboard',
      name: 'admin-dashboard',
      component: () => import('../views/AdminDashboardView.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/users',
      name: 'admin-users',
      component: () => import('../views/AdminUsersView.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/surveys',
      name: 'admin-surveys',
      component: () => import('../views/AdminSurveysView.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/analytics',
      name: 'admin-analytics',
      component: () => import('../views/AdminAnalyticsView.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/risk',
      name: 'admin-risk',
      component: () => import('../views/AdminRiskView.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/announcements',
      name: 'admin-announcements',
      component: () => import('../views/AdminAnnouncementsView.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/logs',
      name: 'admin-logs',
      component: () => import('../views/AdminOperationLogsView.vue'),
      meta: { requiresAdmin: true },
    },

  ],
})

// 全局路由守卫：检查认证状态
router.beforeEach((to, from, next) => {
  let token = localStorage.getItem('access_token')
  if (token === 'null' || token === 'undefined') {
    token = null
    localStorage.removeItem('access_token')
  }
  let adminToken = localStorage.getItem('admin_token')
  if (adminToken === 'null' || adminToken === 'undefined') {
    adminToken = null
    localStorage.removeItem('admin_token')
  }
  const requiresAuth = to.meta.requiresAuth !== false
  const requiresAdmin = to.meta.requiresAdmin === true

  // 管理员路由检查
  if (requiresAdmin) {
    if (!adminToken) {
      next({ name: 'admin-login' })
      return
    }
    next()
    return
  }

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
