<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const token = localStorage.getItem('access_token')

// State
const userBalance = ref(null)
const userCredit = ref(null)
const hasHonor = ref(false)
const activityPoints = ref(0)
const totalEarned = ref(0)

const selectedType = ref('all')
const logs = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const totalRecords = ref(0)
const loading = ref(false)
const showHonorTooltip = ref(false)

// Computed
const displayedLogs = computed(() => logs.value)
const hasMore = computed(() => currentPage.value * pageSize.value < totalRecords.value)

function formatDateTime(isoString) {
  const date = new Date(isoString)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

async function fetchPointsLogs() {
  if (!token) {
    alert('未登录，请先登录')
    router.push('/login')
    return
  }

  loading.value = true
  try {
    const typeParam = selectedType.value === 'all' ? '' : selectedType.value
    const url = new URL('/api/v1/points/logs', window.location.origin)
    url.searchParams.set('page', currentPage.value)
    url.searchParams.set('page_size', pageSize.value)
    if (typeParam) url.searchParams.set('type', typeParam)

    const res = await fetch(url.toString(), {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (!res.ok) {
      throw new Error(`API 错误: ${res.status}`)
    }

    const data = await res.json()

    if (currentPage.value === 1 && data.user) {
      userBalance.value = data.user.points
      userCredit.value = data.user.credit_score
      hasHonor.value = data.user.has_honor
      activityPoints.value = data.user.activity_points
      
      const earnedRecords = data.items.filter(item => item.delta > 0)
      totalEarned.value = earnedRecords.reduce((sum, item) => sum + item.delta, 0)
    }

    logs.value = data.items
    totalRecords.value = data.total
  } catch (err) {
    console.error('Failed to fetch points logs:', err)
    alert('获取积分记录失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

function changeType(newType) {
  selectedType.value = newType
  currentPage.value = 1
  logs.value = []
  fetchPointsLogs()
}

function loadMore() {
  if (!hasMore.value || loading.value) return
  currentPage.value += 1
  fetchPointsLogs()
}

function navigateToSurvey(log) {
  if (!log.related_id || !log.related_type) return

  if (log.related_type === 'survey_fill') {
    router.push({
      name: 'survey-fill',
      params: { id: log.related_id },
      query: { readonly: 'true' },
    })
  } else if (log.related_type === 'survey_publish') {
    router.push({
      name: 'survey-builder',
      params: { id: log.related_id },
    })
  }
}

function goBack() {
  router.back()
}

onMounted(() => {
  fetchPointsLogs()
})
</script>

<template>
  <div class="points-record">
    <header class="header">
      <button class="back-btn" @click="goBack">&larr; 返回</button>
      <h1>积分记录</h1>
      <button class="shop-btn" @click="router.push('/profile')">👤 个人</button>
    </header>

    <section class="honor-card">
      <div class="card-content">
        <div class="balance-section">
          <div class="balance">
            <p class="balance-label">当前余额</p>
            <p class="balance-value">{{ userBalance ?? '-' }}</p>
          </div>
          <div class="earned">
            <p class="earned-label">累计赚取</p>
            <p class="earned-value">{{ totalEarned }}</p>
          </div>
        </div>

        <div class="honor-badge" v-if="hasHonor">
          <span class="badge-icon">🎖️</span>
          <span class="badge-text">优质问卷填写者</span>
          <div
            class="tooltip"
            tabindex="0"
            @mouseenter="showHonorTooltip = true"
            @mouseleave="showHonorTooltip = false"
            @focus="showHonorTooltip = true"
            @blur="showHonorTooltip = false"
          >
            <span v-if="showHonorTooltip" class="tooltip-content">
              ✨ 您是优质填答者！由于您填写的问卷质量极高，发布问卷时将享受积分折扣优惠。
            </span>
          </div>
        </div>
        <div class="honor-badge disabled" v-else>
          <span class="badge-icon">☆</span>
          <span class="badge-text">升级中...</span>
        </div>
      </div>
    </section>

    <section class="filter-tabs">
      <button 
        v-for="tab in ['all', 'earn', 'spend']" 
        :key="tab"
        :class="['tab', selectedType === tab ? 'active' : '']"
        @click="changeType(tab)"
      >
        {{ tab === 'all' ? '全部' : tab === 'earn' ? '收入' : '支出' }}
      </button>
    </section>

    <section class="transaction-list">
      <div v-if="loading && currentPage === 1" class="loading">
        加载中...
      </div>
      
      <div v-else-if="logs.length === 0" class="empty">
        暂无记录
      </div>

      <div v-else class="list-items">
        <div 
          v-for="log in displayedLogs" 
          :key="log.id"
          :class="['list-item', { clickable: log.related_id }]"
          @click="navigateToSurvey(log)"
        >
          <div class="item-left">
            <p class="item-reason">{{ log.reason }}</p>
            <p class="item-time">{{ formatDateTime(log.created_at) }}</p>
          </div>
          <div :class="['item-right', log.delta > 0 ? 'earn' : 'spend']">
            {{ log.delta > 0 ? '+' : '' }}{{ log.delta }}
          </div>
        </div>
      </div>

      <div v-if="hasMore && !loading" class="load-more">
        <button @click="loadMore" class="load-more-btn">
          加载更多
        </button>
      </div>

      <div v-if="loading && currentPage > 1" class="loading-more">
        加载中...
      </div>
    </section>
  </div>
</template>

<style scoped>
.points-record {
  min-height: 100vh;
  background: radial-gradient(circle at top left, #edf3ff 0%, #f7f9ff 45%, #ffffff 100%);
  padding: 0;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #ffffff;
  border-bottom: 1px solid #e8eef5;
}

.back-btn,
.shop-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  color: #1e4fb4;
  font-weight: 600;
  padding: 8px 12px;
  transition: opacity 0.2s;
}

.back-btn:hover,
.shop-btn:hover {
  opacity: 0.7;
}

.header h1 {
  font-size: 20px;
  font-weight: 600;
  color: #1a202c;
  margin: 0;
  flex: 1;
  text-align: center;
}

.honor-card {
  margin: 24px;
  padding: 24px;
  background: linear-gradient(135deg, #0d47a1 0%, #1e4fb4 100%);
  border-radius: 12px;
  color: white;
  box-shadow: 0 4px 16px rgba(13, 71, 161, 0.15);
  position: relative;
  overflow: hidden;
}

.honor-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 50%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(255, 255, 255, 0.05) 0%, transparent 50%);
  pointer-events: none;
}

.card-content {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.balance-section {
  flex: 1;
}

.balance {
  margin-bottom: 16px;
}

.balance-label {
  font-size: 14px;
  opacity: 0.9;
  margin: 0;
}

.balance-value {
  font-size: 40px;
  font-weight: 700;
  margin: 4px 0 0 0;
}

.earned {
  margin-bottom: 0;
}

.earned-label {
  font-size: 12px;
  opacity: 0.85;
  margin: 0;
}

.earned-value {
  font-size: 18px;
  margin: 2px 0 0 0;
  opacity: 0.95;
}

.honor-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: linear-gradient(180deg, #fffdfa 0%, #fffef6 100%);
  border: 2px solid #ffd166; /* gold border */
  color: #0d1b37;
  border-radius: 10px;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
  position: relative;
  box-shadow: 0 0 0 0 rgba(255, 209, 102, 0.0);
  animation: gold-breathe 4s ease-in-out infinite;
}

.honor-badge:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(255, 209, 102, 0.18);
}

.honor-badge.disabled {
  opacity: 0.6;
  animation: none;
  border-color: #d9d9d9;
}

@keyframes gold-breathe {
  0%, 100% { box-shadow: 0 0 0 0 rgba(255, 197, 60, 0.0); }
  50% { box-shadow: 0 8px 30px 6px rgba(255, 197, 60, 0.08); }
}

.badge-icon {
  font-size: 20px;
}

.badge-text {
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
}

.tooltip {
  position: relative;
}

.tooltip-content {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.9);
  color: white;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  white-space: nowrap;
  margin-bottom: 8px;
  z-index: 100;
  animation: fadeIn 0.2s;
}

.tooltip-content::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 4px solid transparent;
  border-top-color: rgba(0, 0, 0, 0.9);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

.filter-tabs {
  display: flex;
  gap: 16px;
  padding: 16px 24px;
  background: #ffffff;
  border-bottom: 1px solid #e8eef5;
}

.tab {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  font-weight: 500;
  padding: 8px 0;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.tab.active {
  color: #1e4fb4;
  border-bottom-color: #1e4fb4;
}

.tab:hover {
  color: #1e4fb4;
}

.transaction-list {
  padding: 16px 24px;
}

.loading,
.empty {
  text-align: center;
  color: #999;
  padding: 32px 0;
  font-size: 14px;
}

.list-items {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 12px;
  border-bottom: 1px solid #e8eef5;
  background: #ffffff;
  transition: background 0.2s;
}

.list-item.clickable {
  cursor: pointer;
}

.list-item.clickable:hover {
  background: #f5f7ff;
}

.item-left {
  flex: 1;
}

.item-reason {
  font-size: 14px;
  font-weight: 500;
  color: #1a202c;
  margin: 0 0 4px 0;
}

.item-time {
  font-size: 12px;
  color: #999;
  margin: 0;
}

.item-right {
  font-size: 16px;
  font-weight: 600;
  width: 60px;
  text-align: right;
}

.item-right.earn {
  color: #1e4fb4;
}

.item-right.spend {
  color: #1a202c;
}

.load-more,
.loading-more {
  text-align: center;
  padding: 24px 0;
}

.load-more-btn {
  background: #1e4fb4;
  color: white;
  border: none;
  padding: 12px 32px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
}

.load-more-btn:hover {
  background: #1a3f8a;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(30, 79, 180, 0.2);
}

.loading-more {
  color: #999;
  font-size: 12px;
}

@media (max-width: 768px) {
  .points-record {
    margin-left: 0;
  }
}
</style>
