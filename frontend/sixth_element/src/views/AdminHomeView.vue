<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getDashboardStats, adminLogout, getAdminUser, getNotificationList, markAllNotificationsRead } from '@/utils/adminApi'
import { useAdminTheme } from '@/composables/useAdminTheme'

const router = useRouter()
const stats = ref(null)
const adminUser = ref(null)
const loading = ref(true)
const showUserMenu = ref(false)
const showNotifications = ref(false)
const animatedValues = ref({})
const cardAnimationComplete = ref({})
const notifications = ref([])
const unreadCount = ref(0)
const notifLoading = ref(false)

const { isDark, themeVars, initTheme, toggleTheme } = useAdminTheme()

const menuItems = computed(() => [
  {
    id: 'dashboard',
    icon: '📊',
    title: '总览仪表盘',
    subtitle: '核心数据一目了然',
    link: '/admin/dashboard',
    stats: stats.value ? [
      { label: '总用户', value: stats.value.total_users, suffix: '人' },
      { label: '总问卷', value: stats.value.total_surveys, suffix: '份' },
    ] : [],
    change: stats.value ? { value: stats.value.today_new_users, label: '今日新增用户' } : null,
    gradient: isDark.value
      ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      : 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
  },
  {
    id: 'users',
    icon: '👥',
    title: '用户管理',
    subtitle: '查看/编辑用户信息',
    link: '/admin/users',
    stats: stats.value ? [
      { label: '总用户', value: stats.value.total_users, suffix: '人' },
      { label: '活跃用户', value: Math.round(stats.value.total_users * 0.7), suffix: '人' },
    ] : [],
    change: stats.value ? { value: stats.value.today_new_users, label: '今日新增' } : null,
    gradient: isDark.value
      ? 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
      : 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',
  },
  {
    id: 'surveys',
    icon: '📝',
    title: '问卷管理',
    subtitle: '查看/编辑问卷',
    link: '/admin/surveys',
    stats: stats.value ? [
      { label: '总问卷', value: stats.value.total_surveys, suffix: '份' },
      { label: '已发布', value: Math.round(stats.value.total_surveys * 0.6), suffix: '份' },
    ] : [],
    change: stats.value ? { value: stats.value.today_new_surveys, label: '今日新增' } : null,
    gradient: isDark.value
      ? 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
      : 'linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%)',
  },
  {
    id: 'analytics',
    icon: '🤖',
    title: 'AI与推荐分析',
    subtitle: '推荐效果与AI统计',
    link: '/admin/analytics',
    stats: stats.value ? [
      { label: '推荐点击率', value: '67.8', suffix: '%' },
      { label: 'AI生成率', value: '45.2', suffix: '%' },
    ] : [],
    change: { value: '+2.3%', label: 'CTR提升' },
    gradient: isDark.value
      ? 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)'
      : 'linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%)',
  },
  {
    id: 'risk',
    icon: '⚠️',
    title: '风控监测',
    subtitle: '异常检测与安全预警',
    link: '/admin/risk',
    stats: stats.value ? [
      { label: '异常用户', value: '23', suffix: '人' },
      { label: '可疑问卷', value: '5', suffix: '份' },
    ] : [],
    change: { value: '5', label: '疑似异常' },
    gradient: isDark.value
      ? 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
      : 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)',
  },
])

onMounted(() => {
  initTheme()
  loadData()
})

async function loadData() {
  try {
    adminUser.value = getAdminUser()
    const data = await getDashboardStats()
    if (data) {
      stats.value = data
      initAnimations()
    }
    await loadNotifications()
  } catch (err) {
    console.error('Failed to load stats:', err)
  } finally {
    loading.value = false
    setTimeout(() => {
      menuItems.value.forEach((item, index) => {
        setTimeout(() => {
          cardAnimationComplete.value[item.id] = true
        }, index * 100)
      })
    }, 100)
  }
}

async function loadNotifications() {
  notifLoading.value = true
  try {
    const data = await getNotificationList(1, 10, 'unread')
    if (data) {
      notifications.value = data.messages || []
      unreadCount.value = data.total || 0
    }
  } catch (err) {
    console.error('Failed to load notifications:', err)
  } finally {
    notifLoading.value = false
  }
}

async function handleMarkAllRead() {
  try {
    await markAllNotificationsRead()
    unreadCount.value = 0
    notifications.value = []
    await loadNotifications()
  } catch (err) {
    console.error('Failed to mark all as read:', err)
  }
}

function initAnimations() {
  menuItems.value.forEach(item => {
    animatedValues.value[item.id] = 0
    if (item.stats) {
      item.stats.forEach(stat => {
        const targetValue = typeof stat.value === 'number' ? stat.value : parseInt(stat.value) || 0
        animateValue(item.id, targetValue)
      })
    }
  })
}

function animateValue(cardId, targetValue) {
  const duration = 1500
  const startTime = performance.now()
  const startValue = 0

  function update(currentTime) {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / duration, 1)
    const easeProgress = 1 - Math.pow(1 - progress, 3)
    animatedValues.value[cardId] = Math.round(startValue + (targetValue - startValue) * easeProgress)

    if (progress < 1) {
      requestAnimationFrame(update)
    }
  }
  requestAnimationFrame(update)
}

function getDisplayValue(item, stat) {
  if (stat.suffix === '%') {
    return stat.value
  }
  return animatedValues.value[item.id] || stat.value || 0
}

function goToPage(link) {
  router.push(link)
}

function handleLogout() {
  adminLogout()
  router.push('/admin/login')
}

function toggleUserMenu() {
  showUserMenu.value = !showUserMenu.value
  showNotifications.value = false
}

function toggleNotifications() {
  showNotifications.value = !showNotifications.value
  showUserMenu.value = false
}

function handleClickOutside(event) {
  if (!event.target.closest('.user-menu-container')) {
    showUserMenu.value = false
  }
  if (!event.target.closest('.notification-container')) {
    showNotifications.value = false
  }
}

function handleToggleTheme() {
  toggleTheme()
  loadData()
}

function formatTime(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  const now = new Date()
  const diff = Math.floor((now - date) / 1000)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  if (diff < 604800) return `${Math.floor(diff / 86400)}天前`
  return date.toLocaleDateString('zh-CN')
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="admin-home" :class="{ dark: isDark }">
    <header class="top-nav">
      <div class="nav-left">
        <span class="logo-icon">🚀</span>
        <span class="logo-text">第六元素管理后台</span>
      </div>
      <div class="nav-right">
        <button class="nav-small-btn" @click="router.push('/admin/announcements')" title="系统公告">
          📢
        </button>
        <button class="nav-small-btn" @click="router.push('/admin/logs')" title="操作日志">
          📋
        </button>
        <div class="notification-container">
          <button class="notification-btn" @click.stop="toggleNotifications">
            <span class="bell-icon">🔔</span>
            <span v-if="unreadCount > 0" class="badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
          </button>
          <div v-if="showNotifications" class="notification-dropdown">
            <div class="notification-header">
              <span>通知</span>
              <button v-if="unreadCount > 0" class="mark-read" @click="handleMarkAllRead">全部已读</button>
            </div>
            <div v-if="notifLoading" class="notification-loading">加载中...</div>
            <div v-else-if="notifications.length === 0" class="notification-empty">暂无新通知</div>
            <div v-else class="notification-list">
              <div
                v-for="notif in notifications"
                :key="notif.id"
                class="notification-item unread"
              >
                <span class="notif-icon">{{ notif.message_type === 'system' ? '📢' : notif.message_type === 'team_invite' ? '👥' : '🎁' }}</span>
                <div class="notif-content">
                  <p class="notif-text">{{ notif.title }}</p>
                  <span class="notif-time">{{ formatTime(notif.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="user-menu-container">
          <button class="user-btn" @click.stop="toggleUserMenu">
            <span class="avatar">👤</span>
            <span class="username">{{ adminUser?.nickname || '管理员' }}</span>
            <span class="arrow">▼</span>
          </button>
          <div v-if="showUserMenu" class="user-dropdown">
            <div class="dropdown-item email">
              <span>📧</span> {{ adminUser?.email }}
            </div>
            <div class="dropdown-divider"></div>
            <button class="dropdown-item logout" @click="handleLogout">
              <span>🚪</span> 退出登录
            </button>
          </div>
        </div>
      </div>
    </header>

    <main class="main-content">
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>

      <div v-else class="cards-grid">
        <div
          v-for="(item, index) in menuItems"
          :key="item.id"
          class="menu-card"
          :class="{ animated: cardAnimationComplete[item.id] }"
          :style="{ '--delay': index * 100 + 'ms', '--gradient': item.gradient }"
          @click="goToPage(item.link)"
        >
          <div class="card-glow"></div>
          <div class="card-icon">{{ item.icon }}</div>
          <h2 class="card-title">{{ item.title }}</h2>
          <p class="card-subtitle">{{ item.subtitle }}</p>

          <div class="card-stats">
            <div v-for="(stat, idx) in item.stats" :key="idx" class="stat-item">
              <span class="stat-value">{{ getDisplayValue(item, stat) }}</span>
              <span class="stat-suffix">{{ stat.suffix }}</span>
              <span class="stat-label">{{ stat.label }}</span>
            </div>
          </div>

          <div v-if="item.change" class="card-change" :class="{ positive: item.change.value > 0 || typeof item.change.value === 'string' }">
            <span class="change-arrow">{{ typeof item.change.value === 'string' ? (item.change.value.startsWith('+') ? '↑' : '→') : (item.change.value > 0 ? '↑' : '↓') }}</span>
            <span class="change-value">{{ item.change.value }}</span>
            <span class="change-label">{{ item.change.label }}</span>
          </div>

          <div class="card-action">
            <span>▸ 进入{{ item.title.split(' ')[0] }}</span>
          </div>
        </div>
      </div>
    </main>

    <button class="theme-toggle-fixed" @click="handleToggleTheme" :title="isDark ? '切换到浅色模式' : '切换到深色模式'">
      <span class="theme-icon">{{ isDark ? '☀️' : '🌙' }}</span>
    </button>
  </div>
</template>

<style scoped>
.admin-home {
  min-height: 100vh;
  background: var(--admin-bg-secondary, #f5f7fa);
  transition: background 0.3s ease;
}

/* 顶部导航栏 */
.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 32px;
  background: var(--admin-bg-primary, #ffffff);
  border-bottom: 1px solid var(--admin-border-color, #e8ecf0);
  position: sticky;
  top: 0;
  z-index: 100;
  transition: all 0.3s ease;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  font-size: 28px;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  background: var(--admin-accent-gradient, linear-gradient(135deg, #667eea 0%, #764ba2 100%));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.theme-toggle {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--admin-bg-secondary, #f5f7fa);
  border: 1px solid var(--admin-border-color, #e8ecf0);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  z-index: 101;
}

.theme-toggle:hover {
  transform: rotate(15deg);
  background: var(--admin-accent-gradient);
}

.theme-icon {
  font-size: 18px;
}

.theme-toggle-fixed {
  position: fixed;
  bottom: 24px;
  left: 24px;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--admin-bg-primary, #ffffff);
  border: 1px solid var(--admin-border-color, #e8ecf0);
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.theme-toggle-fixed:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 30px rgba(102, 126, 234, 0.3);
  background: var(--admin-accent-gradient);
}

.notification-container {
  position: relative;
}

.nav-small-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--admin-bg-secondary, #f5f7fa);
  border: 1px solid var(--admin-border-color, #e8ecf0);
  border-radius: 8px;
  cursor: pointer;
  font-size: 18px;
  transition: all 0.2s;
}

.nav-small-btn:hover {
  background: var(--admin-accent-gradient);
  transform: scale(1.05);
}

.notification-btn {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--admin-bg-secondary, #f5f7fa);
  border: 1px solid var(--admin-border-color, #e8ecf0);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.notification-btn:hover {
  background: var(--admin-accent-gradient);
  transform: scale(1.05);
}

.bell-icon {
  font-size: 20px;
}

.badge {
  position: absolute;
  top: 4px;
  right: 4px;
  min-width: 18px;
  height: 18px;
  background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%);
  color: white;
  font-size: 11px;
  font-weight: 600;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 5px;
}

.notification-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 320px;
  background: var(--admin-bg-primary, #ffffff);
  border-radius: 16px;
  box-shadow: 0 10px 50px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  animation: dropdown-enter 0.25s ease;
}

@keyframes dropdown-enter {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--admin-border-color, #e8ecf0);
  font-weight: 600;
  color: var(--admin-text-primary, #1a1a2e);
}

.mark-read {
  background: none;
  border: none;
  color: #667eea;
  font-size: 13px;
  cursor: pointer;
}

.mark-read:hover {
  text-decoration: underline;
}

.notification-list {
  max-height: 300px;
  overflow-y: auto;
}

.notification-empty,
.notification-loading {
  padding: 40px 20px;
  text-align: center;
  color: #888;
  font-size: 14px;
}

.notification-item {
  display: flex;
  gap: 12px;
  padding: 14px 20px;
  border-bottom: 1px solid var(--admin-border-color, #e8ecf0);
  transition: background 0.2s ease;
  cursor: pointer;
}

.notification-item:hover {
  background: var(--admin-bg-secondary, #f5f7fa);
}

.notification-item.unread {
  background: rgba(102, 126, 234, 0.05);
}

.notification-item.unread:hover {
  background: rgba(102, 126, 234, 0.1);
}

.notif-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.notif-content {
  flex: 1;
}

.notif-text {
  margin: 0 0 4px 0;
  font-size: 14px;
  color: var(--admin-text-primary, #1a1a2e);
}

.notif-time {
  font-size: 12px;
  color: var(--admin-text-muted, #999999);
}

.user-menu-container {
  position: relative;
}

.user-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--admin-bg-secondary, #f5f7fa);
  border: 1px solid var(--admin-border-color, #e8ecf0);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.user-btn:hover {
  background: var(--admin-accent-gradient);
  transform: translateY(-2px);
}

.avatar {
  font-size: 20px;
}

.username {
  font-size: 14px;
  font-weight: 500;
  color: var(--admin-text-primary, #1a1a2e);
}

.arrow {
  font-size: 10px;
  color: var(--admin-text-muted, #999999);
  transition: transform 0.3s ease;
}

.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 220px;
  background: var(--admin-bg-primary, #ffffff);
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  padding: 8px;
  animation: dropdown-enter 0.2s ease;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 14px;
  color: var(--admin-text-secondary, #666666);
  cursor: pointer;
  transition: all 0.2s ease;
}

.dropdown-item:hover {
  background: var(--admin-bg-secondary, #f5f7fa);
}

.dropdown-item.email {
  color: var(--admin-text-muted, #999999);
  font-size: 13px;
  cursor: default;
}

.dropdown-item.logout {
  color: #f5576c;
}

.dropdown-item.logout:hover {
  background: rgba(245, 87, 108, 0.1);
}

.dropdown-divider {
  height: 1px;
  background: var(--admin-border-color, #e8ecf0);
  margin: 8px 0;
}

/* 主内容区 */
.main-content {
  padding: 40px;
  max-width: 1400px;
  margin: 0 auto;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 20px;
  color: var(--admin-text-secondary, #666666);
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--admin-border-color, #e8ecf0);
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 卡片网格 */
.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 28px;
}

.menu-card {
  position: relative;
  background: var(--admin-bg-card, #ffffff);
  border-radius: 20px;
  padding: 28px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  opacity: 0;
  transform: translateY(30px);
  overflow: hidden;
  border: 1px solid var(--admin-border-color, #e8ecf0);
}

.menu-card.animated {
  animation: card-enter 0.6s ease forwards;
  animation-delay: var(--delay);
}

@keyframes card-enter {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.menu-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 50px rgba(102, 126, 234, 0.2);
  border-color: transparent;
}

.menu-card:hover .card-glow {
  opacity: 1;
}

.menu-card:hover .card-icon {
  transform: scale(1.15);
}

.card-glow {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, var(--gradient) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.4s ease;
  pointer-events: none;
}

.card-icon {
  font-size: 56px;
  margin-bottom: 16px;
  transition: transform 0.3s ease;
}

.card-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--admin-text-primary, #1a1a2e);
  margin: 0 0 8px 0;
}

.card-subtitle {
  font-size: 14px;
  color: var(--admin-text-muted, #999999);
  margin: 0 0 20px 0;
}

.card-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  background: var(--admin-accent-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.2;
}

.stat-suffix {
  font-size: 14px;
  color: var(--admin-text-muted, #999999);
  margin-left: 2px;
}

.stat-label {
  font-size: 12px;
  color: var(--admin-text-muted, #999999);
  margin-top: 4px;
}

.card-change {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: var(--admin-bg-secondary, #f5f7fa);
  border-radius: 20px;
  font-size: 13px;
  color: var(--admin-text-secondary, #666666);
  margin-bottom: 16px;
}

.card-change.positive {
  background: rgba(67, 233, 123, 0.15);
  color: #2ecc71;
}

.card-change.negative {
  background: rgba(245, 87, 108, 0.15);
  color: #f5576c;
}

.change-arrow {
  font-weight: 600;
}

.change-value {
  font-weight: 600;
}

.change-label {
  color: var(--admin-text-muted, #999999);
  margin-left: 4px;
}

.card-action {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  background: var(--admin-accent-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  opacity: 0;
  transform: translateX(-10px);
  transition: all 0.3s ease;
}

.menu-card:hover .card-action {
  opacity: 1;
  transform: translateX(0);
}

/* 响应式 */
@media (max-width: 768px) {
  .top-nav {
    padding: 12px 16px;
  }

  .logo-text {
    font-size: 16px;
  }

  .main-content {
    padding: 20px;
  }

  .cards-grid {
    grid-template-columns: 1fr;
  }

  .username {
    display: none;
  }
}
</style>
