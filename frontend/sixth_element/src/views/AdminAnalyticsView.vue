<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getRecommendAnalytics, getAiAnalytics } from '@/utils/adminApi'
import { useAdminTheme } from '@/composables/useAdminTheme'

const router = useRouter()
const { initTheme, themeVars } = useAdminTheme()
const recommendData = ref(null)
const aiData = ref(null)
const loading = ref(true)
const selectedDays = ref(7)

const daysOptions = [
  { label: '近7天', value: 7 },
  { label: '近14天', value: 14 },
  { label: '近30天', value: 30 },
]

async function fetchData() {
  loading.value = true
  try {
    const [recommend, ai] = await Promise.all([
      getRecommendAnalytics(selectedDays.value),
      getAiAnalytics(selectedDays.value),
    ])
    recommendData.value = recommend
    aiData.value = ai
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function changeDays(days) {
  selectedDays.value = days
  await fetchData()
}

onMounted(() => {
  initTheme()
  fetchData()
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
      
      <header class="page-header">
        <div class="breadcrumb">
          <router-link to="/admin" class="breadcrumb-item">🏠 管理首页</router-link>
          <span class="breadcrumb-sep">/</span>
          <span class="breadcrumb-current">AI与推荐系统分析</span>
        </div>
        <div class="header-top">
          <h1 class="page-title">AI与推荐系统分析</h1>
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
      </header>

      <div v-if="loading" class="loading">加载中...</div>
      <template v-else>
        <section class="section">
          <h2 class="section-title">推荐系统指标</h2>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-icon">👁️</div>
              <div class="stat-content">
                <div class="stat-value">{{ recommendData?.impressions || 0 }}</div>
                <div class="stat-label">推荐展示次数</div>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">🖱️</div>
              <div class="stat-content">
                <div class="stat-value">{{ recommendData?.clicks || 0 }}</div>
                <div class="stat-label">推荐点击次数</div>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">📊</div>
              <div class="stat-content">
                <div class="stat-value">{{ recommendData?.ctr || 0 }}%</div>
                <div class="stat-label">推荐点击率(CTR)</div>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">🔄</div>
              <div class="stat-content">
                <div class="stat-value">{{ recommendData?.refresh_count || 0 }}</div>
                <div class="stat-label">换一批点击次数</div>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">🗑️</div>
              <div class="stat-content">
                <div class="stat-value">{{ recommendData?.delete_count || 0 }}</div>
                <div class="stat-label">问卷删除次数</div>
              </div>
            </div>
          </div>
        </section>

        <section class="section">
          <h2 class="section-title">AI生成问卷指标</h2>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-icon">🤖</div>
              <div class="stat-content">
                <div class="stat-value">{{ aiData?.ai_surveys || 0 }}</div>
                <div class="stat-label">AI生成问卷数</div>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">📝</div>
              <div class="stat-content">
                <div class="stat-value">{{ aiData?.total_surveys || 0 }}</div>
                <div class="stat-label">总问卷数</div>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">%</div>
              <div class="stat-content">
                <div class="stat-value">{{ aiData?.ai_rate || 0 }}%</div>
                <div class="stat-label">AI生成占比</div>
              </div>
            </div>
          </div>
        </section>

        <section class="section">
          <h2 class="section-title">问卷难度分布</h2>
          <div class="difficulty-chart">
            <div
              v-for="(count, difficulty) in (aiData?.difficulty_distribution || {})"
              :key="difficulty"
              class="difficulty-bar"
            >
              <div class="difficulty-label">
                <span class="difficulty-level">难度 {{ difficulty }}</span>
                <span class="difficulty-count">{{ count }}</span>
              </div>
              <div class="difficulty-track">
                <div
                  class="difficulty-fill"
                  :style="{ width: (count / Math.max(...Object.values(aiData?.difficulty_distribution || {1:1}), 1) * 100) + '%' }"
                ></div>
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

.admin-sidebar {
  width: 240px;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  color: white;
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
}

.sidebar-header {
  padding: 24px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-title {
  font-size: 18px;
  font-weight: bold;
  margin: 0;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  transition: all 0.3s;
}

.nav-item:hover,
.nav-item.active {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-icon {
  font-size: 18px;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.admin-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.admin-name {
  font-size: 14px;
}

.logout-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: white;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.theme-toggle-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.theme-toggle-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: scale(1.1);
}

.admin-main {
  flex: 1;
  padding: 24px;
  background: var(--admin-bg-primary);
}

.floating-home-btn {
  position: fixed;
  top: 80px;
  left: 20px;
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 50%;
  font-size: 20px;
  cursor: pointer;
  z-index: 100;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  transition: transform 0.2s, box-shadow 0.2s;
}

.floating-home-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5);
}

.theme-toggle-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  width: 36px;
  height: 36px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  margin-left: 8px;
}

.theme-toggle-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.logout-btn {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
  border: none;
  color: white;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  margin-left: 8px;
}

.logout-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.page-header {
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

.day-btn.active {
  background: var(--admin-accent-gradient);
  color: white;
  border-color: transparent;
}

.loading {
  text-align: center;
  padding: 40px;
  color: var(--admin-text-secondary);
}

.section {
  background: var(--admin-bg-card);
  border: 1px solid var(--admin-border-color);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.section-title {
  font-size: 16px;
  font-weight: bold;
  color: var(--admin-text-primary);
  margin: 0 0 20px 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.stat-card {
  background: var(--admin-bg-secondary);
  border: 1px solid var(--admin-border-color);
  border-radius: 10px;
  padding: 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.stat-icon {
  font-size: 24px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: var(--admin-text-primary);
}

.stat-label {
  font-size: 12px;
  color: var(--admin-text-secondary);
  margin-top: 4px;
}

.difficulty-chart {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.difficulty-bar {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.difficulty-label {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.difficulty-level {
  color: var(--admin-text-secondary);
}

.difficulty-count {
  font-weight: 600;
  color: var(--admin-text-primary);
}

.difficulty-track {
  height: 8px;
  background: var(--admin-bg-secondary);
  border: 1px solid var(--admin-border-color);
  border-radius: 4px;
  overflow: hidden;
}

.difficulty-fill {
  height: 100%;
  background: var(--admin-accent-gradient);
  border-radius: 4px;
  transition: width 0.5s ease;
}
</style>
