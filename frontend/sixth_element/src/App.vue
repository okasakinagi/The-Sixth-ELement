<script setup>
import { RouterView, useRouter } from 'vue-router'
import { ref, computed, watch } from 'vue'
import ProfileCompletionModal from './components/ProfileCompletionModal.vue'
import AppSidebar from './components/AppSidebar.vue'

const router = useRouter()

const showModal = ref(false)
const hasShownModal = ref(false)

// 监听路由变化，登录后显示弹窗
watch(
  () => router.currentRoute.value.name,
  (newRouteName) => {
    const token = localStorage.getItem('access_token')
    const justLoggedIn = router.currentRoute.value.query.justLoggedIn === 'true'

    // 仅在从登录页跳转到主页且未显示过时，才显示弹窗
    if (newRouteName === 'task-hall' && token && justLoggedIn && !hasShownModal.value) {
      showModal.value = true
      hasShownModal.value = true
    }
  }
)

function handleModalClose() {
  showModal.value = false
}

// 判断是否需要显示侧边栏（登录页不显示）
const showSidebar = computed(() => {
  return router.currentRoute.value.name !== 'auth'
})
</script>

<template>
  <AppSidebar v-if="showSidebar">
    <RouterView />
  </AppSidebar>
  <template v-else>
    <RouterView />
  </template>
  <ProfileCompletionModal :visible="showModal" @close="handleModalClose" />
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
}
</style>
