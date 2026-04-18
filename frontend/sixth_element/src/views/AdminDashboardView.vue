<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  getDashboardStats,
  getDashboardTrend,
  exportDashboard,
} from '@/utils/adminApi'
import { useAdminTheme } from '@/composables/useAdminTheme'

const router = useRouter()
const { initTheme, themeVars } = useAdminTheme()
const stats = ref(null)
const trend = ref([])
const loading = ref(true)
const error = ref('')
const selectedDays = ref(7)

const daysOptions = [
  { label: '近7天', value: 7 },
  { label: '近14天', value: 14 },
  { label: '近30天', value: 30 },
]

async function fetchStats() {
  try {
    const data = await getDashboardStats()
    stats.value = data
  } catch (e) {
    error.value = e.message
  }
}

async function fetchTrend() {
  try {
    const data = await getDashboardTrend(selectedDays.value)
    trend.value = data.trend || []
  } catch (e) {
    error.value = e.message
  }
}

async function changeDays(days) {
  selectedDays.value = days
  await fetchTrend()
}

async function handleExport() {
  try {
    const data = await exportDashboard(selectedDays.value)
    if (data && data.trend) {
      const csvHeader = ['日期', '新增用户', '新增问卷', '新增填写']
      const csvRows = data.trend.map(row => [
        row.date,
        row.new_users,
        row.new_surveys,
        row.new_fills
      ].join(','))
      const csvContent = [csvHeader.join(','), ...csvRows].join('\n')
      const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `dashboard_export_${new Date().toISOString().slice(0,10)}.csv`
      link.click()
      URL.revokeObjectURL(url)
    }
  } catch (e) {
    console.error('Export failed:', e)
    alert('导出失败')
  }
}

onMounted(async () => {
  initTheme()
  await Promise.all([fetchStats(), fetchTrend()])
  loading.value = false
})

const maxUsers = computed(() => {
  if (!trend.value.length) return 1
  return Math.max(...trend.value.map(t => t.new_users), 1)
})

const maxSurveys = computed(() => {
  if (!trend.value.length) return 1
  return Math.max(...trend.value.map(t => t.new_surveys), 1)
})

const maxFills = computed(() => {
  if (!trend.value.length) return 1
  return Math.max(...trend.value.map(t => t.new_fills), 1)
})
</script>

<template>
  <div class="admin-dashboard" :style="{
    '--admin-bg-primary': themeVars.bgPrimary,
    '--admin-bg-secondary': themeVars.bgSecondary,
    '--admin-bg-card': themeVars.bgCard,
    '--admin-text-primary': themeVars.textPrimary,
    '--admin-text-secondary': themeVars.textSecondary,
    '--admin-text-muted': themeVars.textMuted,
    '--admin-border-color': themeVars.borderColor,
    '--admin-accent-gradient': themeVars.accentGradient,
  }">
    <main class="admin-main">
      <header class="dashboard-header">
        <div class="breadcrumb">
          <router-link to="/admin" class="breadcrumb-item">🏠 管理首页</router-link>
          <span class="breadcrumb-sep">/</span>
          <span class="breadcrumb-current">总览仪表盘</span>
        </div>
        <div class="header-top">
          <h1 class="page-title">总览仪表盘</h1>
          <div class="header-right">
            <span class="welcome-text">欢迎</span>
            <button class="export-btn" @click="handleExport">📄 导出报表</button>
          </div>
        </div>
      </header>

      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <template v-else>
        <section class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon">👥</div>
            <div class="stat-content">
              <div class="stat-value">{{ stats?.total_users || 0 }}</div>
              <div class="stat-label">总用户数</div>
              <div class="stat-today">今日 +{{ stats?.today_new_users || 0 }}</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon">📝</div>
            <div class="stat-content">
              <div class="stat-value">{{ stats?.total_surveys || 0 }}</div>
              <div class="stat-label">总问卷数</div>
              <div class="stat-today">今日 +{{ stats?.today_new_surveys || 0 }}</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon">✅</div>
            <div class="stat-content">
              <div class="stat-value">{{ stats?.total_fills || 0 }}</div>
              <div class="stat-label">总填写次数</div>
              <div class="stat-today">今日 +{{ stats?.today_fills || 0 }}</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon">📈</div>
            <div class="stat-content">
              <div class="stat-value">{{ stats?.avg_surveys_per_user || 0 }}</div>
              <div class="stat-label">人均填写问卷</div>
              <div class="stat-today">完成率 {{ stats?.survey_completion_rate || 0 }}%</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon">🎁</div>
            <div class="stat-content">
              <div class="stat-value">{{ stats?.total_points_issued || 0 }}</div>
              <div class="stat-label">积分发放总量</div>
              <div class="stat-today">消耗 {{ stats?.total_points_consumed || 0 }}</div>
            </div>
          </div>
        </section>

        <section class="trend-section">
          <div class="section-header">
            <h2 class="section-title">趋势图</h2>
            <div class="days-selector">
              <button
                v-for="opt in daysOptions"
                :key="opt.value"
                class="day-btn"
                :class="{ active: selectedDays === opt.value }"
                @click="changeDays(opt.value)"
              >
                {{ opt.label }}
              </button>
            </div>
          </div>

          <div class="charts-container">
            <div class="chart-card">
              <h3 class="chart-title">新增用户趋势</h3>
              <div class="chart">
                <div class="bar-chart">
                  <div
                    v-for="(item, index) in trend"
                    :key="index"
                    class="bar-item"
                  >
                    <div class="bar-wrapper">
                      <div
                        class="bar user-bar"
                        :style="{ height: (item.new_users / maxUsers * 100) + '%' }"
                      >
                        <span class="bar-value">{{ item.new_users }}</span>
                      </div>
                    </div>
                    <span class="bar-label">{{ item.date?.slice(5) }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="chart-card">
              <h3 class="chart-title">问卷发布趋势</h3>
              <div class="chart">
                <div class="bar-chart">
                  <div
                    v-for="(item, index) in trend"
                    :key="index"
                    class="bar-item"
                  >
                    <div class="bar-wrapper">
                      <div
                        class="bar survey-bar"
                        :style="{ height: (item.new_surveys / maxSurveys * 100) + '%' }"
                      >
                        <span class="bar-value">{{ item.new_surveys }}</span>
                      </div>
                    </div>
                    <span class="bar-label">{{ item.date?.slice(5) }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="chart-card">
              <h3 class="chart-title">填写次数趋势</h3>
              <div class="chart">
                <div class="bar-chart">
                  <div
                    v-for="(item, index) in trend"
                    :key="index"
                    class="bar-item"
                  >
                    <div class="bar-wrapper">
                      <div
                        class="bar fill-bar"
                        :style="{ height: (item.new_fills / maxFills * 100) + '%' }"
                      >
                        <span class="bar-value">{{ item.new_fills }}</span>
                      </div>
                    </div>
                    <span class="bar-label">{{ item.date?.slice(5) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </template>
    </main>
  </div>
</template>

<style scoped>
.admin-dashboard {
  display: flex;
  min-height: 100vh;
  background: var(--admin-bg-primary);
}

.admin-main {
  flex: 1;
  padding: 24px;
  background: var(--admin-bg-primary);
}

.dashboard-header {
  margin-bottom: 24px;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 13px;
}

.breadcrumb-item {
  color: #667eea;
  text-decoration: none;
  transition: all 0.2s ease;
}

.breadcrumb-item:hover {
  color: #764ba2;
  text-decoration: underline;
}

.breadcrumb-sep {
  color: var(--admin-text-muted);
}

.breadcrumb-current {
  color: var(--admin-text-secondary);
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 24px;
  font-weight: bold;
  color: var(--admin-text-primary);
  margin: 0;
}

.welcome-text {
  color: var(--admin-text-secondary);
  font-size: 14px;
  margin-right: 16px;
}

.export-btn {
  padding: 6px 12px;
  background: var(--admin-accent-gradient);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: opacity 0.2s;
}

.export-btn:hover {
  opacity: 0.9;
}

.header-right {
  display: flex;
  align-items: center;
}

.loading,
.error {
  text-align: center;
  padding: 40px;
  color: var(--admin-text-secondary);
}

.error {
  color: #e74c3c;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  background: var(--admin-bg-card);
  border: 1px solid var(--admin-border-color);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.stat-icon {
  font-size: 32px;
  background: var(--admin-accent-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: var(--admin-text-primary);
}

.stat-label {
  font-size: 14px;
  color: var(--admin-text-secondary);
  margin-top: 4px;
}

.stat-today {
  font-size: 12px;
  color: var(--admin-text-muted);
  margin-top: 4px;
}

.trend-section {
  background: var(--admin-bg-card);
  border: 1px solid var(--admin-border-color);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-title {
  font-size: 18px;
  font-weight: bold;
  color: var(--admin-text-primary);
  margin: 0;
}

.days-selector {
  display: flex;
  gap: 8px;
}

.day-btn {
  padding: 6px 12px;
  border: 1px solid var(--admin-border-color);
  background: var(--admin-bg-secondary);
  color: var(--admin-text-secondary);
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s;
}

.day-btn:hover {
  background: var(--admin-bg-card);
  color: var(--admin-text-primary);
}

.day-btn.active {
  background: var(--admin-accent-gradient);
  color: white;
  border-color: transparent;
}

.charts-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.chart-card {
  border: 1px solid var(--admin-border-color);
  border-radius: 12px;
  padding: 24px;
  background: var(--admin-bg-secondary);
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--admin-text-primary);
  margin: 0 0 16px 0;
}

.chart {
  height: 280px;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  height: 100%;
  gap: 8px;
}

.bar-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}

.bar-wrapper {
  flex: 1;
  width: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.bar {
  width: 80%;
  max-width: 40px;
  min-height: 4px;
  border-radius: 4px 4px 0 0;
  position: relative;
  transition: height 0.5s ease;
}

.bar-item:hover .bar {
  transform: scaleY(1.05);
}

.bar-value {
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  color: var(--admin-text-secondary);
  white-space: nowrap;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.bar-item:hover .bar-value {
  opacity: 1;
}

.user-bar {
  background: var(--admin-accent-gradient);
}

.survey-bar {
  background: linear-gradient(180deg, #00f260 0%, #0575e6 100%);
}

.fill-bar {
  background: linear-gradient(180deg, #ffd700 0%, #ffb400 100%);
}

.bar-label {
  font-size: 10px;
  color: var(--admin-text-muted);
  margin-top: 8px;
}
</style>
