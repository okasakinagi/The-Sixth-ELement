<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getRiskControl } from '@/utils/adminApi'
import { useAdminTheme } from '@/composables/useAdminTheme'

const router = useRouter()
const { initTheme, themeVars } = useAdminTheme()
const riskData = ref(null)
const loading = ref(true)
const currentType = ref('short_duration')
const riskTypes = [
  { key: 'short_duration', label: '短时长回答' },
  { key: 'suspicious_users', label: '可疑用户' },
  { key: 'abnormal_surveys', label: '异常问卷' },
]

async function fetchData() {
  loading.value = true
  try {
    const data = await getRiskControl(currentType.value)
    riskData.value = data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function changeType(type) {
  currentType.value = type
  await fetchData()
}

function getSeverityClass(severity) {
  if (severity === 'high') return 'severity-high'
  if (severity === 'medium') return 'severity-medium'
  if (severity === 'low') return 'severity-low'
  return ''
}

function formatDuration(seconds) {
  if (!seconds) return '-'
  return `${seconds}秒`
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
          <span class="breadcrumb-current">风控与异常监测</span>
        </div>
        <div class="header-top">
          <h1 class="page-title">风控与异常监测</h1>
        </div>
      </header>

      <div v-if="loading" class="loading">加载中...</div>
      <template v-else>
        <section class="section">
          <h2 class="section-title">异常行为统计</h2>
          <div class="stats-grid">
            <div class="stat-card warning">
              <div class="stat-icon">⏱️</div>
              <div class="stat-content">
                <div class="stat-value">{{ riskData?.short_duration_count || 0 }}</div>
                <div class="stat-label">填写时间异常（&lt;10秒）</div>
              </div>
            </div>
            <div class="stat-card danger">
              <div class="stat-icon">👤</div>
              <div class="stat-content">
                <div class="stat-value">{{ riskData?.suspicious_users || 0 }}</div>
                <div class="stat-label">可疑用户数量</div>
              </div>
            </div>
            <div class="stat-card danger">
              <div class="stat-icon">📝</div>
              <div class="stat-content">
                <div class="stat-value">{{ riskData?.abnormal_surveys || 0 }}</div>
                <div class="stat-label">可疑问卷数量</div>
              </div>
            </div>
          </div>
        </section>

        <section class="section">
          <h2 class="section-title">风控事件明细</h2>
          <div class="type-tabs">
            <button
              v-for="rt in riskTypes"
              :key="rt.key"
              :class="['tab-btn', { active: currentType === rt.key }]"
              @click="changeType(rt.key)"
            >
              {{ rt.label }}
            </button>
          </div>
          <div v-if="riskData?.items?.length > 0" class="event-list">
            <table class="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>用户</th>
                  <th v-if="currentType === 'short_duration'">问卷</th>
                  <th v-if="currentType === 'short_duration'">填写时长</th>
                  <th v-if="currentType === 'short_duration'">严重程度</th>
                  <th v-if="currentType === 'suspicious_users'">事件类型</th>
                  <th v-if="currentType === 'suspicious_users'">严重程度</th>
                  <th v-if="currentType === 'abnormal_surveys'">问卷</th>
                  <th v-if="currentType === 'abnormal_surveys'">发布者</th>
                  <th v-if="currentType === 'abnormal_surveys'">严重程度</th>
                  <th>时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in riskData.items" :key="item.id">
                  <td>{{ item.id }}</td>
                  <td>{{ item.user_nickname || '匿名' }}</td>
                  <td v-if="currentType === 'short_duration'">{{ item.survey_title || '-' }}</td>
                  <td v-if="currentType === 'short_duration'">{{ formatDuration(item.duration_seconds) }}</td>
                  <td v-if="currentType === 'short_duration'">
                    <span class="severity-badge" :class="getSeverityClass(item.severity)">{{ item.severity }}</span>
                  </td>
                  <td v-if="currentType === 'suspicious_users'">{{ item.event_type }}</td>
                  <td v-if="currentType === 'suspicious_users'">
                    <span class="severity-badge" :class="getSeverityClass(item.severity)">{{ item.severity }}</span>
                  </td>
                  <td v-if="currentType === 'abnormal_surveys'">{{ item.survey_title || '-' }}</td>
                  <td v-if="currentType === 'abnormal_surveys'">{{ item.owner_nickname || '-' }}</td>
                  <td v-if="currentType === 'abnormal_surveys'">
                    <span class="severity-badge" :class="getSeverityClass(item.severity)">{{ item.severity }}</span>
                  </td>
                  <td>{{ item.created_at?.slice(0, 19) }}</td>
                </tr>
              </tbody>
            </table>
            <div class="pagination-info">
              共 {{ riskData.total }} 条记录，第 {{ riskData.page }} / {{ Math.ceil(riskData.total / riskData.page_size) }} 页
            </div>
          </div>
          <div v-else class="empty-state">
            <p>暂无风控事件记录</p>
          </div>
        </section>

        <section class="section">
          <h2 class="section-title">风控说明</h2>
          <div class="info-cards">
            <div class="info-card">
              <h3>填写时间异常</h3>
              <p>用户在10秒内完成问卷填写，视为异常行为。可能是刷单、机器填写等行为。</p>
            </div>
            <div class="info-card">
              <h3>可疑用户</h3>
              <p>被标记为可疑状态的用户，需要管理员审核确认其行为是否违规。</p>
            </div>
            <div class="info-card">
              <h3>可疑问卷</h3>
              <p>存在异常数据的问卷，如完成率异常、答案模式异常等，需要管理员检查。</p>
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
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.stat-card {
  background: var(--admin-bg-secondary);
  border: 1px solid var(--admin-border-color);
  border-radius: 10px;
  padding: 20px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.stat-card.warning {
  background: #fff3e0;
  color: #e65100;
}

.stat-card.danger {
  background: #ffebee;
  color: #c62828;
}

.stat-icon {
  font-size: 32px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: var(--admin-text-primary);
}

.stat-label {
  font-size: 13px;
  color: var(--admin-text-secondary);
  margin-top: 4px;
}

.stat-card.warning .stat-value,
.stat-card.warning .stat-label {
  color: #e65100;
}

.stat-card.danger .stat-value,
.stat-card.danger .stat-label {
  color: #c62828;
}

.info-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.info-card {
  background: var(--admin-bg-secondary);
  border: 1px solid var(--admin-border-color);
  border-radius: 10px;
  padding: 20px;
}

.info-card h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--admin-text-primary);
  margin: 0 0 8px 0;
}

.info-card p {
  font-size: 13px;
  color: var(--admin-text-secondary);
  margin: 0;
  line-height: 1.5;
}

.type-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.tab-btn {
  padding: 8px 16px;
  background: var(--admin-bg-secondary);
  border: 1px solid var(--admin-border-color);
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: var(--admin-text-secondary);
  transition: all 0.2s;
}

.tab-btn:hover {
  background: var(--admin-bg-card);
  color: var(--admin-text-primary);
}

.tab-btn.active {
  background: var(--admin-accent-gradient);
  color: white;
  border-color: transparent;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 12px;
}

.data-table th {
  background: var(--admin-bg-secondary);
  padding: 12px 14px;
  text-align: left;
  font-weight: 600;
  font-size: 12px;
  color: var(--admin-text-primary);
  border-bottom: 1px solid var(--admin-border-color);
}

.data-table td {
  padding: 12px 14px;
  font-size: 13px;
  color: var(--admin-text-primary);
  border-bottom: 1px solid var(--admin-border-color);
}

.data-table tr:last-child td {
  border-bottom: none;
}

.severity-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}

.severity-badge.severity-high {
  background: #ffebee;
  color: #c62828;
}

.severity-badge.severity-medium {
  background: #fff3e0;
  color: #ef6c00;
}

.severity-badge.severity-low {
  background: #e8f5e9;
  color: #2e7d32;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--admin-text-muted);
}

.pagination-info {
  margin-top: 16px;
  text-align: center;
  font-size: 13px;
  color: var(--admin-text-secondary);
}
</style>
