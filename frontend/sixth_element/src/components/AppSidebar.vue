<script setup>
import { useRouter, useRoute } from 'vue-router'
import { ref, onMounted } from 'vue'
import { getUserLevel } from '@/utils/levelApi'

const router = useRouter()
const route = useRoute()
const isMobileMenuOpen = ref(false)
const levelInfo = ref(null)

onMounted(async () => {
  if (localStorage.getItem('access_token')) {
    try {
      levelInfo.value = await getUserLevel(router)
    } catch (e) {
      // 非关键，静默失败
    }
  }
})

function isActive(routeName) {
  return route.name === routeName
}

function handleLogout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user_id')
  localStorage.removeItem('user_nickname')
  router.push('/login')
}

function closeMobileMenu() {
  isMobileMenuOpen.value = false
}

function toggleMobileMenu() {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}
</script>

<template>
  <div class="app-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ 'mobile-open': isMobileMenuOpen }">
      <div class="sidebar-brand">
        <div class="brand-icon">📚</div>
        <div class="brand-text">
          <p class="brand-title">第六元素</p>
          <p class="brand-subtitle">Survey Hub</p>
        </div>
        <div v-if="levelInfo" class="sidebar-level">
          <div class="level-badge" :title="levelInfo.title">
            <span class="level-icon">⭐</span>
            <span class="level-num">Lv{{ levelInfo.level }}</span>
          </div>
          <div class="level-label-sidebar">{{ levelInfo.title }}</div>
        </div>
      </div>

      <nav class="sidebar-menu">
        <RouterLink
          to="/"
          :class="['menu-item', { active: isActive('task-hall') }]"
          @click="closeMobileMenu"
        >
          <span class="menu-icon">📋</span>
          <span class="menu-label">任务大厅</span>
        </RouterLink>

        <RouterLink
          to="/contacts"
          :class="['menu-item', { active: isActive('contacts') }]"
          @click="closeMobileMenu"
        >
          <span class="menu-icon">👥</span>
          <span class="menu-label">伙伴与组队</span>
        </RouterLink>

        <RouterLink
          to="/surveys"
          :class="['menu-item', { active: isActive('survey-management') }]"
          @click="closeMobileMenu"
        >
          <span class="menu-icon">📝</span>
          <span class="menu-label">问卷管理</span>
        </RouterLink>

        <RouterLink
          to="/points"
          :class="['menu-item', { active: isActive('points-record') }]"
          @click="closeMobileMenu"
        >
          <span class="menu-icon">💰</span>
          <span class="menu-label">积分记录</span>
        </RouterLink>

        <RouterLink
          to="/help"
          :class="['menu-item', { active: isActive('help-center') }]"
          @click="closeMobileMenu"
        >
          <span class="menu-icon">❓</span>
          <span class="menu-label">帮助中心</span>
        </RouterLink>

        <RouterLink
          to="/profile"
          :class="['menu-item', { active: isActive('profile') }]"
          @click="closeMobileMenu"
        >
          <span class="menu-icon">👤</span>
          <span class="menu-label">个人资料</span>
        </RouterLink>
      </nav>

      <div class="sidebar-footer">
        <button class="logout-btn" @click="handleLogout">
          <span class="menu-icon">🚪</span>
          <span class="menu-label">登出</span>
        </button>
      </div>
    </aside>

    <!-- 移动端菜单按钮 -->
    <button class="mobile-menu-toggle" @click="toggleMobileMenu">
      <span></span>
      <span></span>
      <span></span>
    </button>

    <!-- 移动端遮罩 -->
    <div v-if="isMobileMenuOpen" class="mobile-overlay" @click="closeMobileMenu"></div>

    <!-- 主内容区域 -->
    <main class="main-content">
      <slot></slot>
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
  background: #f5f7fa;
}

/* ====== 侧边栏 ====== */
.sidebar {
  width: 260px;
  background: linear-gradient(135deg, #1e4fb4 0%, #1a3f8a 100%);
  color: white;
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  height: 100dvh;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
  z-index: 1000;
  transition: all 0.3s ease;
}

.sidebar-brand {
  padding: 24px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.brand-icon {
  font-size: 32px;
  font-weight: 700;
}

.brand-text {
  flex: 1;
}

.brand-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: white;
}

.brand-subtitle {
  margin: 2px 0 0 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.sidebar-level {
  display: flex;
  flex-direction: column;
  gap: 3px;
  align-items: flex-start;
  margin-top: 10px;
}

.level-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: linear-gradient(135deg, #ffd700, #ffb400);
  color: #1f1f1f;
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
  white-space: nowrap;
  box-shadow: 0 6px 18px rgba(255, 171, 0, 0.25);
}

.level-label-sidebar {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.85);
  max-width: 180px;
  line-height: 1.3;
}

.level-icon {
  font-size: 12px;
  transform: translateY(1px);
}

.sidebar-menu {
  flex: 1;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  border-radius: 8px;
  transition: all 0.2s ease;
  cursor: pointer;
  border: none;
  background: transparent;
  font-size: 14px;
  font-weight: 500;
}

.menu-item:hover {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.menu-item.active {
  background: rgba(255, 255, 255, 0.25);
  color: white;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.menu-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.menu-label {
  flex: 1;
}

.sidebar-footer {
  padding: 12px;
  padding-bottom: max(12px, env(safe-area-inset-bottom));
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.logout-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  color: rgba(255, 255, 255, 0.8);
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  font-weight: 500;
}

.logout-btn:hover {
  background: rgba(255, 0, 0, 0.3);
  color: white;
}

/* ====== 主内容区域 ====== */
.main-content {
  flex: 1;
  margin-left: 260px;
  width: calc(100% - 260px);
  min-height: 100vh;
  padding: 8px 10px 16px;
  overflow-y: auto;
  overflow-x: hidden;
  background: radial-gradient(circle at top left, #edf3ff 0%, #f7f9ff 45%, #ffffff 100%);
  transition: margin-left 0.3s ease;
}

/* ====== 移动端 ====== */
.mobile-menu-toggle {
  display: none;
  position: fixed;
  top: 16px;
  left: 16px;
  z-index: 1001;
  flex-direction: column;
  gap: 5px;
  background: white;
  border: none;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.mobile-menu-toggle span {
  width: 24px;
  height: 2px;
  background: #1e4fb4;
  border-radius: 2px;
  transition: all 0.3s ease;
}

.mobile-overlay {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 999;
}

@media (max-width: 768px) {
  .sidebar {
    width: 240px;
    left: -240px;
  }

  .sidebar.mobile-open {
    left: 0;
  }

  .main-content {
    margin-left: 0;
    width: 100%;
    padding: 8px 10px 14px;
  }

  .mobile-menu-toggle {
    display: flex;
  }

  .mobile-overlay {
    display: block;
  }

  .menu-label {
    font-size: 13px;
  }
}

@media (max-width: 480px) {
  .sidebar {
    width: 100%;
    left: -100%;
  }

  .sidebar.mobile-open {
    left: 0;
  }

  .brand-text {
    display: flex;
    flex-direction: column;
  }

  .brand-title {
    font-size: 14px;
  }

  .brand-subtitle {
    font-size: 10px;
  }

  .menu-item,
  .logout-btn {
    font-size: 13px;
    padding: 10px 14px;
  }

  .menu-icon {
    font-size: 16px;
  }
}

/* 滚动条美化 */
.sidebar::-webkit-scrollbar {
  width: 6px;
}

.sidebar::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
}

.sidebar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
}

.sidebar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}
</style>
