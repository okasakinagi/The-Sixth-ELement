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

// 判断是否需要显示侧边栏（登录页和忘记密码页不显示）
const showSidebar = computed(() => {
  const routeName = router.currentRoute.value.name
  return routeName !== 'auth' && routeName !== 'forgot-password'
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

html {
  width: 100%;
  height: 100%;
  overflow-x: hidden;
  scroll-behavior: smooth;
}

body {
  width: 100%;
  height: 100%;
  overflow-x: hidden;
  font-family: 'Segoe UI','Helvetica Neue', Tahoma, Geneva, Verdana, sans-serif, -apple-system, BlinkMacSystemFont;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  width: 100%;
  min-height: 100vh;
  overflow-x: hidden;
  position: relative;
}

/* 防止移动端双击缩放 */
button, a {
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
}

/* 移动端输入框优化 */
input, select, textarea {
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
}

/* 滚动条美化（仅 webkit 浏览器） */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #2196f3;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #1976d2;
}
</style>
