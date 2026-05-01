<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { Line, Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { getDashboardStats, getDashboardTrend, getRecommendAnalytics, getAiAnalytics, getRiskControl, adminLogout, getAdminUser, getNotificationList, markAllNotificationsRead } from '@/utils/adminApi'
import { useAdminTheme } from '@/composables/useAdminTheme'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const router = useRouter()
const stats = ref(null)
const trend = ref([])
const analytics = ref(null)
const riskData = ref(null)
const adminUser = ref(null)
const loading = ref(true)
const showUserMenu = ref(false)
const showNotifications = ref(false)
const animatedValues = ref({})
const cardAnimationComplete = ref({})
const notifications = ref([])
const overviewData = ref({})
const unreadCount = ref(0)
const notifLoading = ref(false)

const lineChartData = computed(() => ({
  labels: trend.value.map(t => t.date?.slice(5) || ''),
  datasets: [{
    label: '日活跃用户',
    data: trend.value.map(t => t.new_users),
    fill: true,
    borderColor: '#667eea',
    backgroundColor: 'rgba(102, 126, 234, 0.1)',
    tension: 0.4,
    pointBackgroundColor: '#667eea',
    pointBorderColor: '#fff',
    pointHoverRadius: 6,
  }]
}))

const lineChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#1a1a2e',
      titleColor: '#fff',
      bodyColor: '#fff',
      padding: 12,
      cornerRadius: 8,
      mode: 'index',
      intersect: false,
    }
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: { color: '#999' }
    },
    y: {
      grid: { color: 'rgba(0,0,0,0.05)' },
      ticks: { color: '#999' }
    }
  },
  animation: {
    duration: 1000,
    easing: 'easeOutQuart'
  },
  interaction: {
    mode: 'index',
    intersect: false,
  },
}

const lineChartPlugins = [{
  id: 'verticalLine',
  afterDraw: (chart) => {
    if (!chart.tooltip?.active || chart.tooltip.active.length === 0) return
    const ctx = chart.ctx
    const x = chart.tooltip.active[0].element.x
    const y = chart.tooltip.active[0].element.y
    ctx.save()
    ctx.beginPath()
    ctx.setLineDash([5, 5])
    ctx.moveTo(x, y)
    ctx.lineTo(x, chart.scales.y.bottom)
    ctx.strokeStyle = 'rgba(102, 126, 234, 0.6)'
    ctx.lineWidth = 1.5
    ctx.stroke()
    ctx.restore()
  }
}]

const doughnutChartData = computed(() => {
  const total = stats.value?.total_surveys || 1
  const completed = stats.value?.completed_surveys || 0
  const inProgress = stats.value?.published_surveys || 0
  const notStarted = Math.max(total - completed - inProgress, 0)
  return {
    labels: ['已完成', '进行中', '未开始'],
    datasets: [{
      data: [completed, inProgress, Math.max(notStarted, 0)],
      backgroundColor: ['#667eea', '#764ba2', '#e8ecf0'],
      borderWidth: 0,
      hoverOffset: 8,
    }]
  }
})

const doughnutChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        color: '#666',
        padding: 16,
        usePointStyle: true,
        pointStyle: 'circle'
      }
    },
    tooltip: {
      backgroundColor: '#1a1a2e',
      titleColor: '#fff',
      bodyColor: '#fff',
      padding: 12,
      cornerRadius: 8,
    }
  },
  cutout: '70%',
  animation: {
    animateRotate: true,
    animateScale: true,
    duration: 1000,
    easing: 'easeOutQuart'
  }
}

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
      { label: '7日活跃用户', value: stats.value.active_users_7d || 0, suffix: '人' },
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
      { label: '已发布', value: stats.value.published_surveys || 0, suffix: '份' },
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
    stats: analytics.value ? [
      { label: '推荐点击率', value: Math.round((analytics.value.ctr || 0) * 10) / 10, suffix: '%' },
      { label: 'AI生成率', value: Math.round((analytics.value.ai_rate || 0) * 10) / 10, suffix: '%' },
    ] : [],
    change: analytics.value ? { value: Math.round((analytics.value.ctr || 0) * 10) / 10 + '%', label: 'CTR' } : null,
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
    stats: riskData.value ? [
      { label: '异常用户', value: riskData.value.suspicious_users || 0, suffix: '人' },
      { label: '可疑问卷', value: riskData.value.abnormal_surveys || 0, suffix: '份' },
    ] : [],
    change: riskData.value ? { value: riskData.value.short_duration_count || 0, label: '疑似刷单' } : null,
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

    try {
      const statsData = await getDashboardStats()
      if (statsData) {
        stats.value = statsData
        overviewData.value = {
          totalUsers: statsData.total_users || 0,
          activeToday: statsData.today_new_users || 0,
          totalSurveys: statsData.total_surveys || 0,
          totalResponses: statsData.total_fills || 0,
        }
        initAnimations()
      }
    } catch (e) {
      console.error('Failed to load stats:', e)
    }

    try {
      const trendData = await getDashboardTrend(7)
      if (trendData && trendData.trend) {
        trend.value = trendData.trend
      }
    } catch (e) {
      console.error('Failed to load trend:', e)
    }

    try {
      const [recommendData, aiData] = await Promise.all([
        getRecommendAnalytics(7),
        getAiAnalytics(7),
      ])
      analytics.value = {
        ...(recommendData || {}),
        ...(aiData || {}),
      }
    } catch (e) {
      console.error('Failed to load analytics:', e)
    }

    try {
      const risk = await getRiskControl()
      if (risk) {
        riskData.value = risk
      }
    } catch (e) {
      console.error('Failed to load risk:', e)
    }

    await loadNotifications()
  } catch (err) {
    console.error('Failed to load data:', err)
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

function getChangeDirection(item) {
  if (!item.change) return 0
  if (typeof item.change.value === 'string') {
    return item.change.value.startsWith('+') ? 1 : item.change.value.startsWith('-') ? -1 : 0
  }
  return item.change.value > 0 ? 1 : -1
}

function getChangeText(item) {
  if (!item.change) return ''
  return typeof item.change.value === 'string' ? item.change.value : (item.change.value > 0 ? `+${item.change.value}` : item.change.value)
}

function getDisplayStats(item) {
  if (!item.stats || item.stats.length === 0) return []
  return item.stats.slice(0, 2).map(stat => ({
    value: getDisplayValue(item, stat) + (stat.suffix || ''),
    label: stat.label
  }))
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
  if (!event.target.closest('.user-dropdown')) {
    showUserMenu.value = false
  }
  if (!event.target.closest('.notification-dropdown')) {
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
        <span class="logo-text">第六元素</span>
      </div>
      <div class="nav-right">
        <button class="nav-small-btn" @click="router.push('/admin/announcements')" title="系统公告">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
            <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
            <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
          </svg>
        </button>
        <button class="nav-small-btn" @click="router.push('/admin/logs')" title="操作日志">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10 9 9 9 8 9"/>
          </svg>
        </button>
        <button class="nav-small-btn" @click.stop="toggleNotifications" title="通知">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
          <span v-if="unreadCount > 0" class="badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
        </button>
        <button class="nav-small-btn" @click.stop="toggleUserMenu" title="管理员">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
          </svg>
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
              <span class="notif-icon">
                <svg v-if="notif.message_type === 'system'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                  <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
                </svg>
                <svg v-else-if="notif.message_type === 'team_invite'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
                <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 16v-4"/>
                  <path d="M12 8h.01"/>
                </svg>
              </span>
              <div class="notif-content">
                <p class="notif-text">{{ notif.title }}</p>
                <span class="notif-time">{{ formatTime(notif.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-if="showUserMenu" class="user-dropdown">
          <div class="user-info">
            <div class="user-name">{{ adminUser?.nickname || '管理员' }}</div>
            <div class="user-role">系统管理员</div>
          </div>
          <div class="dropdown-divider"></div>
          <a class="dropdown-item" href="/admin/users" @click.prevent="router.push('/admin/users')">
            用户管理
          </a>
          <a class="dropdown-item" href="/admin/surveys" @click.prevent="router.push('/admin/surveys')">
            问卷管理
          </a>
          <div class="dropdown-divider"></div>
          <button class="dropdown-item logout" @click="handleLogout">
            退出登录
          </button>
        </div>
      </div>
    </header>

    <main class="main-content">
      <div class="platform-header">
        <h1 class="platform-title">第六元素智慧管理平台</h1>
        <p class="platform-subtitle">数据驱动 · 智能决策 · 高效管理</p>
      </div>

      <div class="charts-container">
        <div class="chart-card line-chart">
          <h3 class="chart-title">用户活跃趋势</h3>
          <div class="chart-wrapper">
            <Line :data="lineChartData" :options="lineChartOptions" :plugins="lineChartPlugins" />
          </div>
        </div>
        <div class="chart-card doughnut-chart">
          <h3 class="chart-title">问卷完成率</h3>
          <div class="chart-wrapper">
            <Doughnut :data="doughnutChartData" :options="doughnutChartOptions" />
          </div>
        </div>
      </div>

      <div class="quick-stats">
        <div class="quick-stat">
          <span class="quick-stat-value">{{ overviewData.totalUsers || 0 }}</span>
          <span class="quick-stat-label">总用户</span>
        </div>
        <div class="quick-stat">
          <span class="quick-stat-value">{{ overviewData.activeToday || 0 }}</span>
          <span class="quick-stat-label">今日活跃</span>
        </div>
        <div class="quick-stat">
          <span class="quick-stat-value">{{ overviewData.totalSurveys || 0 }}</span>
          <span class="quick-stat-label">问卷总数</span>
        </div>
        <div class="quick-stat">
          <span class="quick-stat-value">{{ overviewData.totalResponses || 0 }}</span>
          <span class="quick-stat-label">回收答卷</span>
        </div>
      </div>

      <div class="cards-grid">
        <div
          v-for="(item, index) in menuItems"
          :key="item.id"
          class="menu-card"
          :class="{ animated: cardAnimationComplete[item.id] }"
          :style="{ '--delay': index * 80 + 'ms' }"
          @click="goToPage(item.link)"
        >
          <div class="card-header">
            <div class="card-dot"></div>
            <span class="card-change" :class="{ positive: getChangeDirection(item) > 0 }">
              {{ getChangeText(item) }}
            </span>
          </div>
          <h2 class="card-title">{{ item.title }}</h2>
          <p class="card-subtitle">{{ item.subtitle }}</p>
          <div class="card-stats-row">
            <div v-for="(stat, idx) in getDisplayStats(item)" :key="idx" class="stat-mini">
              <span class="stat-mini-value">{{ stat.value }}</span>
              <span class="stat-mini-label">{{ stat.label }}</span>
            </div>
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
  color: var(--admin-text-primary, #1a1a2e);
  letter-spacing: 1px;
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
  color: var(--admin-text-primary, #333);
  transition: all 0.2s;
}

.nav-small-btn svg {
  stroke: currentColor;
}

.nav-small-btn:hover {
  background: var(--admin-accent-gradient);
  color: #fff;
  border-color: transparent;
  transform: scale(1.05);
}

.badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 16px;
  height: 16px;
  background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%);
  color: white;
  font-size: 10px;
  font-weight: 600;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
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

.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 180px;
  background: var(--admin-bg-primary, #ffffff);
  border: 1px solid var(--admin-border-color, #e8ecf0);
  border-radius: 8px;
  padding: 4px 0;
  animation: dropdown-enter 0.2s ease;
}

.user-info {
  padding: 12px 16px;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--admin-text-primary, #1a1a2e);
}

.user-role {
  font-size: 12px;
  color: var(--admin-text-muted, #999999);
  margin-top: 2px;
}

.dropdown-item {
  display: block;
  padding: 8px 16px;
  font-size: 13px;
  color: var(--admin-text-secondary, #666666);
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
}

.dropdown-item:hover {
  background: var(--admin-bg-secondary, #f5f7fa);
}

.dropdown-item.logout {
  color: #f5576c;
  font-size: 13px;
}

.dropdown-item.logout:hover {
  background: rgba(245, 87, 108, 0.1);
}

.dropdown-divider {
  height: 1px;
  background: var(--admin-border-color, #e8ecf0);
  margin: 4px 0;
}

/* 主内容区 */
.main-content {
  padding: 40px;
  max-width: 1400px;
  margin: 0 auto;
}

.platform-header {
  text-align: center;
  margin-bottom: 32px;
}

.platform-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--admin-text-primary, #1a1a2e);
  margin: 0 0 8px 0;
  letter-spacing: 2px;
}

.platform-subtitle {
  font-size: 14px;
  color: var(--admin-text-muted, #999999);
  margin: 0;
  letter-spacing: 4px;
}

.charts-container {
  display: flex;
  justify-content: center;
  gap: 40px;
  margin-bottom: 32px;
  flex-wrap: wrap;
  align-items: flex-start;
}

.chart-card {
  padding: 0;
}

.line-chart {
  flex: 1;
  min-width: 320px;
  max-width: 480px;
}

.doughnut-chart {
  flex: 0 0 200px;
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--admin-text-secondary, #666666);
  margin: 0;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.chart-wrapper {
  height: 240px;
  position: relative;
}

.quick-stats {
  display: flex;
  justify-content: center;
  gap: 32px;
  margin-bottom: 24px;
  padding: 16px 24px;
  background: var(--admin-bg-card, #ffffff);
  border-radius: 12px;
  border: 1px solid var(--admin-border-color, #e8ecf0);
}

.quick-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 80px;
}

.quick-stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--admin-text-primary, #1a1a2e);
}

.quick-stat-label {
  font-size: 12px;
  color: var(--admin-text-muted, #999999);
  margin-top: 4px;
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
  display: flex;
  justify-content: center;
  gap: 12px;
  padding: 0 40px;
  margin-top: 24px;
}

.menu-card {
  position: relative;
  background: var(--admin-bg-card, #ffffff);
  border-radius: 12px;
  padding: 14px 18px;
  cursor: pointer;
  transition: all 0.25s ease;
  opacity: 0;
  transform: translateY(20px);
  overflow: hidden;
  border: 1px solid var(--admin-border-color, #e8ecf0);
  min-width: 120px;
  max-width: 140px;
  flex: 1;
}

.menu-card:hover {
  transform: translateY(-2px);
  border-color: #667eea;
}

.menu-card.animated {
  animation: card-fade-in 0.4s ease forwards;
  animation-delay: var(--delay);
}

@keyframes card-fade-in {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.card-dot {
  width: 6px;
  height: 6px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 50%;
  flex-shrink: 0;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.card-change {
  font-size: 11px;
  font-weight: 600;
  color: #f5576c;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(245, 87, 108, 0.1);
}

.card-change.positive {
  color: #2ecc71;
  background: rgba(46, 204, 113, 0.1);
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--admin-text-primary, #1a1a2e);
  margin: 0 0 4px 0;
  white-space: nowrap;
}

.card-subtitle {
  font-size: 11px;
  color: var(--admin-text-muted, #999999);
  margin: 0 0 10px 0;
  white-space: nowrap;
}

.card-stats-row {
  display: flex;
  gap: 12px;
  padding-top: 8px;
  border-top: 1px solid var(--admin-border-color, #e8ecf0);
}

.stat-mini {
  display: flex;
  flex-direction: column;
}

.stat-mini-value {
  font-size: 14px;
  font-weight: 700;
  color: var(--admin-text-primary, #1a1a2e);
}

.stat-mini-label {
  font-size: 10px;
  color: var(--admin-text-muted, #999999);
}

.card-action {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 10px;
  font-size: 11px;
  color: #667eea;
  font-weight: 500;
}

.card-action .arrow {
  transition: transform 0.2s ease;
}

.menu-card:hover .card-action .arrow {
  transform: translateX(3px);
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

  .platform-header {
    margin-bottom: 20px;
  }

  .platform-title {
    font-size: 22px;
  }

  .charts-container {
    flex-direction: column;
    align-items: center;
  }

  .line-chart,
  .doughnut-chart {
    min-width: 100%;
    max-width: 100%;
  }

  .chart-wrapper {
    height: 200px;
  }

  .cards-grid {
    flex-direction: column;
    align-items: center;
    padding: 0;
    margin-top: 16px;
  }

  .menu-card {
    min-width: 100%;
    max-width: 100%;
  }

  .quick-stats {
    flex-wrap: wrap;
    gap: 16px;
  }

  .username {
    display: none;
  }
}
</style>
