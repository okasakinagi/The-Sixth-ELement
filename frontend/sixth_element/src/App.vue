<script setup>
import { RouterView, useRouter, useRoute } from 'vue-router'
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import IntroModal from './components/IntroModal.vue'
import AppSidebar from './components/AppSidebar.vue'
import GlobalFloatingMenu from './components/GlobalFloatingMenu.vue'

const router = useRouter()
const route = useRoute()

// ---- IntroModal 状态 ----
const showIntroModal = ref(false)
const introShowLoginGuide = ref(false)
const introStartAtProfile = ref(false)
const globalMenuRef = ref(null)

// 将 GlobalFloatingMenu 中的介绍按钮 DOM 元素传给 IntroModal，用于关闭飞行动画
const introTargetEl = computed(() => globalMenuRef.value?.introButtonRef?.value || null)

function isAuthPage(name) {
  return name === 'auth' || name === 'forgot-password'
}

function tryShowIntro() {
  const name = route.name
  if (isAuthPage(name)) return

  const newUser = route.query.newUser === '1'
  const hasSeenIntro = !!localStorage.getItem('sixth_element_intro_shown')
  const token = localStorage.getItem('access_token')

  if (newUser) {
    // 新注册/首次登录用户：显示引导并定位到完善资料区域
    introShowLoginGuide.value = false
    introStartAtProfile.value = true
    showIntroModal.value = true
  } else if (!hasSeenIntro && !showIntroModal.value) {
    // 首次访问该设备：显示引导，未登录时附带注册按钮
    introShowLoginGuide.value = !token
    introStartAtProfile.value = false
    showIntroModal.value = true
  }
}

onMounted(() => {
  // 初始化时检查
  tryShowIntro()
})

// 路由变化时重新检查（如从登录页跳回来）
watch(() => route.name, (newName) => {
  if (isAuthPage(newName)) {
    showIntroModal.value = false
    return
  }
  tryShowIntro()
})

function handleIntroClose() {
  showIntroModal.value = false
  // 记录已阅读，后续不再自动弹出
  localStorage.setItem('sixth_element_intro_shown', '1')
  // 关闭后触发按钮闪光反馈
  nextTick(() => { globalMenuRef.value?.triggerFlash?.() })
  // 清理 newUser query 参数
  if (route.query.newUser) {
    const { newUser: _, ...rest } = route.query
    router.replace({ query: rest })
  }
}

function handleOpenIntro() {
  introShowLoginGuide.value = false
  introStartAtProfile.value = false
  showIntroModal.value = true
}

// ---- 侧边栏 & 浮动菜单显示逻辑 ----
const showSidebar = computed(() => !isAuthPage(route.name))
const showGlobalFloatingMenu = computed(() => !isAuthPage(route.name))
</script>

<template>
  <AppSidebar v-if="showSidebar">
    <RouterView :key="router.currentRoute.value.fullPath" />
  </AppSidebar>
  <template v-else>
    <RouterView :key="router.currentRoute.value.fullPath" />
  </template>
  <GlobalFloatingMenu
    v-if="showGlobalFloatingMenu"
    ref="globalMenuRef"
    @open-intro="handleOpenIntro"
  />
  <IntroModal
    :visible="showIntroModal"
    :show-login-guide="introShowLoginGuide"
    :start-at-profile="introStartAtProfile"
    :target-el="introTargetEl"
    @close="handleIntroClose"
  />
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
