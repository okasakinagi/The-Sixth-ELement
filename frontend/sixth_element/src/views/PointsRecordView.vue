<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { handleTokenExpired } from '@/utils/authHelper'
import { getPointsLogs, getPointsSummary } from '@/utils/pointsApi'
import { updateUserPoints } from '@/utils/userPointsHelper'

const router = useRouter()

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

async function fetchPointsSummary() {
  try {
    const summaryData = await getPointsSummary()
    if (summaryData.user) {
      userBalance.value = summaryData.user.points
      userCredit.value = summaryData.user.credit_score || 0
      hasHonor.value = summaryData.user.has_honor || false
      activityPoints.value = summaryData.user.activity_points || 0
      
      // 同步更新localStorage
      updateUserPoints(summaryData.user.points)
    }
  } catch (err) {
    console.error('Failed to fetch points summary:', err)
    // 不阻止后续操作，继续获取积分记录
  }
}

async function fetchPointsLogs() {
  try {
    loading.value = true
    
    // 首次加载时获取积分汇总
    if (currentPage.value === 1) {
      await fetchPointsSummary()
    }
    
    const typeParam = selectedType.value === 'all' ? '' : selectedType.value
    const data = await getPointsLogs({
      type: typeParam,
      page: currentPage.value,
      page_size: pageSize.value
    })

    if (currentPage.value === 1) {
      // 计算累计赚取的积分
      const earnedRecords = data.items.filter(item => item.delta > 0)
      totalEarned.value = earnedRecords.reduce((sum, item) => sum + item.delta, 0)
      logs.value = data.items
    } else if (currentPage.value > 1) {
      logs.value = [...logs.value, ...data.items]
    }
    totalRecords.value = data.total
  } catch (err) {
    console.error('Failed to fetch points logs:', err)
    
    // 检查是否是登录过期
    if (err.message.includes('登录已过期')) {
      handleTokenExpired(router)
      return
    }
    
    alert(err.message || '获取积分记录失败，请稍后重试')
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
  if (!log.ref_id || !log.ref_type) return

  if (log.ref_type === 'survey_fill') {
    router.push({
      name: 'survey-fill',
      params: { id: log.ref_id },
      query: { readonly: 'true' },
    })
  } else if (log.ref_type === 'survey_publish') {
    router.push({
      name: 'survey-builder',
      params: { id: log.ref_id },
    })
  }
}

function goBack() {
  router.back()
}

onMounted(() => {
  fetchPointsLogs()
})

onUnmounted(() => {
  // cleanup if needed
})
</script>

<template>
  <div class="points-record">
    <div class="page-shell">
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
            :class="['list-item', { clickable: log.ref_id }]"
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
  </div>
</template>

<style scoped>
/* 可拖动悬浮菜单 */
.draggable-menu {
  position: fixed;
  z-index: 100;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(12px);
  border: 1px solid #e3e9f5;
  border-radius: 16px;
  padding: 8px 12px;
  box-shadow: 0 8px 24px rgba(0, 82, 217, 0.15);
  cursor: move;
  touch-action: none;
  user-select: none;
  transition: box-shadow 0.2s ease;
  display: flex;
  align-items: center;
  gap: 10px;
}

.draggable-menu:hover {
  box-shadow: 0 12px 32px rgba(0, 82, 217, 0.22);
}

.drag-handle {
  position: absolute;
  left: 4px;
  top: 50%;
  transform: translateY(-50%);
  color: #a0b0cc;
  font-size: 14px;
  letter-spacing: -2px;
  cursor: grab;
}

.drag-handle:active {
  cursor: grabbing;
}

.points-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: linear-gradient(135deg, #ffd700, #ffb400);
  color: #333;
  border-radius: 12px;
  text-decoration: none;
  font-weight: 700;
  font-size: 14px;
  box-shadow: 0 4px 12px rgba(255, 180, 0, 0.3);
  transition: transform 0.2s ease;
}

.points-badge:hover {
  transform: scale(1.05);
}

.points-icon {
  font-size: 16px;
}

.points-value {
  font-family: 'Courier New', monospace;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0052d9, #2f7bff);
  color: white;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  font-weight: 700;
  box-shadow: 0 6px 12px rgba(0, 82, 217, 0.16);
  transition: transform 0.2s ease;
}

.avatar:hover {
  transform: scale(1.1);
}

.avatar span {
  font-size: 16px;
}

.points-record {
  min-height: 100vh;
  background: radial-gradient(circle at top left, #edf3ff 0%, #f7f9ff 45%, #ffffff 100%);
  display: flex;
  justify-content: center;
  padding: 6px 0 18px;
}

.page-shell {
  width: 100%;
  max-width: 1100px;
  padding: 0 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
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
  width: 100%;
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
  font-size: 18px;
  opacity: 0.9;
  margin: 0;
}

.balance-value {
  font-size: 48px;
  font-weight: 700;
  margin: 4px 0 0 0;
}

.earned {
  margin-bottom: 0;
}

.earned-label {
  font-size: 16px;
  opacity: 0.85;
  margin: 0;
}

.earned-value {
  font-size: 22px;
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
  font-size: 24px;
}

.badge-text {
  font-size: 16px;
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
  gap: 12px;
  padding: 0 0 10px;
  background: transparent;
  border-bottom: none;
}

.tab {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 20px;
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
  padding: 10px 12px 14px;
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
  font-size: 16px;
  font-weight: 500;
  color: #1a202c;
  margin: 0 0 4px 0;
}

.item-time {
  font-size: 14px;
  color: #999;
  margin: 0;
}

.item-right {
  font-size: 18px;
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
    padding: 4px 0 12px;
  }

  .page-shell {
    padding: 0 8px;
  }

  .header {
    padding: 10px 12px;
  }

  .header h1 {
    font-size: 18px;
  }

  .back-btn,
  .shop-btn {
    font-size: 14px;
    padding: 6px 10px;
  }

  .honor-card {
    padding: 18px;
  }

  .card-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .balance-section {
    width: 100%;
  }

  .balance-value {
    font-size: 40px;
  }

  .earned-value {
    font-size: 20px;
  }

  .honor-badge {
    width: 100%;
    justify-content: center;
    padding: 8px 12px;
  }

  .badge-text {
    font-size: 15px;
  }

  .filter-tabs {
    padding: 0 8px 10px;
  }

  .tab {
    font-size: 18px;
  }

  .transaction-list {
    padding: 8px;
  }

  .list-item {
    padding: 14px 10px;
  }

  .item-reason {
    font-size: 15px;
  }

  .item-time {
    font-size: 13px;
  }

  .item-right {
    font-size: 17px;
    width: 55px;
  }

  .load-more-btn {
    padding: 10px 28px;
    font-size: 13px;
  }

  /* 移动端悬浮菜单优化 */
  .draggable-menu {
    top: 16px !important;
    left: auto !important;
    right: 16px;
    padding: 6px 10px;
    gap: 8px;
  }

  .points-badge {
    padding: 5px 10px;
    font-size: 13px;
  }

  .avatar {
    width: 32px;
    height: 32px;
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .points-record {
    padding: 2px 0 10px;
  }

  .page-shell {
    padding: 0 6px;
    gap: 10px;
  }

  .header {
    padding: 8px 10px;
  }

  .header h1 {
    font-size: 16px;
  }

  .back-btn,
  .shop-btn {
    font-size: 13px;
    padding: 5px 8px;
  }

  .honor-card {
    padding: 16px;
  }

  .balance-value {
    font-size: 28px;
  }

  .earned-value {
    font-size: 14px;
  }

  .badge-icon {
    font-size: 18px;
  }

  .badge-text {
    font-size: 12px;
  }

  .filter-tabs {
    padding: 0 6px 8px;
    gap: 8px;
  }

  .tab {
    font-size: 12px;
    padding: 6px 0;
  }

  .transaction-list {
    padding: 6px;
  }

  .list-item {
    padding: 12px 8px;
  }

  .item-reason {
    font-size: 12px;
  }

  .item-time {
    font-size: 10px;
  }

  .item-right {
    font-size: 14px;
    width: 50px;
  }

  .load-more-btn {
    padding: 8px 24px;
    font-size: 12px;
  }

  .tooltip-content {
    font-size: 11px;
    padding: 6px 10px;
    white-space: normal;
    max-width: 200px;
  }

  /* 移动端悬浮菜单进一步优化 */
  .draggable-menu {
    gap: 6px;
    padding: 5px 8px;
  }

  .points-badge {
    padding: 4px 8px;
    font-size: 12px;
  }

  .points-icon {
    font-size: 14px;
  }

  .avatar {
    width: 30px;
    height: 30px;
  }

  .avatar span {
    font-size: 14px;
  }

  .drag-handle {
    font-size: 12px;
  }
}
</style>
