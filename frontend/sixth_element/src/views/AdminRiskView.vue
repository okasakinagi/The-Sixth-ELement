<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getRiskControl } from '@/utils/adminApi'
import { useAdminTheme } from '@/composables/useAdminTheme'

const router = useRouter()
const { initTheme } = useAdminTheme()
const riskData = ref(null)
const loading = ref(true)

async function fetchData() {
  loading.value = true
  try {
    const data = await getRiskControl()
    riskData.value = data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  initTheme()
  fetchData()
})
</script>

<template>
  <div class="admin-dashboard">
    <main class="admin-main">
      <button class="floating-home-btn" @click="router.push('/admin')" title="返回主界面">
        🏠
      </button>
      
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
  background: #f5f7fa;
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
  color: #999;
}

.breadcrumb-current {
  color: #666;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 24px;
  font-weight: bold;
  color: #1a1a2e;
  margin: 0;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.section-title {
  font-size: 16px;
  font-weight: bold;
  color: #1a1a2e;
  margin: 0 0 20px 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.stat-card {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 20px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.stat-card.warning {
  background: #fff3e0;
}

.stat-card.danger {
  background: #ffebee;
}

.stat-icon {
  font-size: 32px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #1a1a2e;
}

.stat-label {
  font-size: 13px;
  color: #666;
  margin-top: 4px;
}

.info-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.info-card {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 20px;
}

.info-card h3 {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px 0;
}

.info-card p {
  font-size: 13px;
  color: #666;
  margin: 0;
  line-height: 1.5;
}
</style>
