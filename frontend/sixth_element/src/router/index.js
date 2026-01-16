import { createRouter, createWebHistory } from 'vue-router'

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
  ],
})

export default router
