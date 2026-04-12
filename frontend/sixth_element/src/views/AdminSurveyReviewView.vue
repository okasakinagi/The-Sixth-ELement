<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getPendingSurveys, approveSurvey, rejectSurvey } from '@/utils/adminApi'
import { useAdminTheme } from '@/composables/useAdminTheme'

const router = useRouter()
const { initTheme } = useAdminTheme()
const surveys = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const showRejectModal = ref(false)
const rejectingSurvey = ref(null)
const rejectReason = ref('')

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

async function fetchSurveys() {
  loading.value = true
  try {
    const data = await getPendingSurveys(page.value, pageSize.value)
    surveys.value = data.surveys || []
    total.value = data.total || 0
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function handleApprove(surveyId) {
  if (!confirm('确认通过该问卷？')) return
  try {
    await approveSurvey(surveyId)
    alert('问卷已审核通过')
    await fetchSurveys()
  } catch (e) {
    console.error(e)
    alert('操作失败')
  }
}

function openRejectModal(survey) {
  rejectingSurvey.value = survey
  rejectReason.value = ''
  showRejectModal.value = true
}

async function handleReject() {
  if (!rejectReason.value.trim()) {
    alert('请输入拒绝原因')
    return
  }
  try {
    await rejectSurvey(rejectingSurvey.value.id, rejectReason.value)
    showRejectModal.value = false
    alert('问卷已拒绝')
    await fetchSurveys()
  } catch (e) {
    console.error(e)
    alert('操作失败')
  }
}

async function changePage(newPage) {
  page.value = newPage
  await fetchSurveys()
}

onMounted(() => {
  initTheme()
  fetchSurveys()
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
          <span class="breadcrumb-current">问卷审核</span>
        </div>
        <div class="header-top">
          <h1 class="page-title">问卷审核</h1>
          <div class="header-right">
            <span class="total-count">待审核: {{ total }} 份</span>
          </div>
        </div>
      </header>

      <div v-if="loading" class="loading">加载中...</div>
      <template v-else>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>问卷标题</th>
                <th>发布者</th>
                <th>奖励积分</th>
                <th>难度</th>
                <th>预计时间</th>
                <th>提交时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in surveys" :key="item.id">
                <td>{{ item.id }}</td>
                <td class="title-cell">{{ item.title }}</td>
                <td>{{ item.owner }}</td>
                <td>{{ item.reward_points }}</td>
                <td>{{ item.difficulty }}</td>
                <td>{{ item.estimated_minutes }}分钟</td>
                <td>{{ item.created_at?.slice(0, 19) }}</td>
                <td>
                  <button class="action-btn approve-btn" @click="handleApprove(item.id)">通过</button>
                  <button class="action-btn reject-btn" @click="openRejectModal(item)">拒绝</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="surveys.length === 0" class="empty-state">
          暂无待审核问卷
        </div>

        <div class="pagination">
          <button
            class="page-btn"
            :disabled="page === 1"
            @click="changePage(page - 1)"
          >
            上一页
          </button>
          <span class="page-info">{{ page }} / {{ totalPages }}</span>
          <button
            class="page-btn"
            :disabled="page >= totalPages"
            @click="changePage(page + 1)"
          >
            下一页
          </button>
        </div>
      </template>
    </main>

    <div v-if="showRejectModal" class="modal-overlay" @click.self="showRejectModal = false">
      <div class="modal-content">
        <h3>拒绝问卷</h3>
        <p class="modal-survey-title">{{ rejectingSurvey?.title }}</p>
        <div class="form-group">
          <label>拒绝原因</label>
          <textarea v-model="rejectReason" placeholder="请输入拒绝原因" rows="4"></textarea>
        </div>
        <div class="modal-actions">
          <button class="cancel-btn" @click="showRejectModal = false">取消</button>
          <button class="confirm-btn reject" @click="handleReject">确认拒绝</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-dashboard {
  display: flex;
  min-height: 100vh;
  background: #f5f7fa;
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
  transition: transform 0.2s;
}

.floating-home-btn:hover {
  transform: scale(1.1);
}

.page-header {
  margin-bottom: 24px;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 14px;
}

.breadcrumb-item {
  color: #667eea;
  text-decoration: none;
}

.breadcrumb-item:hover {
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
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.header-right {
  display: flex;
  gap: 12px;
}

.total-count {
  color: #e65100;
  font-size: 14px;
  font-weight: 500;
}

.loading {
  text-align: center;
  padding: 60px;
  color: #999;
  font-size: 16px;
}

.table-container {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  background: #f8f9fa;
  padding: 16px;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 1px solid #eee;
}

.data-table td {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  color: #666;
}

.title-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.action-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  margin-right: 4px;
}

.approve-btn {
  background: #e8f5e9;
  color: #2e7d32;
}

.approve-btn:hover {
  background: #c8e6c9;
}

.reject-btn {
  background: #ffebee;
  color: #c62828;
}

.reject-btn:hover {
  background: #ffcdd2;
}

.empty-state {
  text-align: center;
  padding: 60px;
  color: #999;
  background: white;
  border-radius: 12px;
  margin-top: 16px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 24px;
}

.page-btn {
  padding: 8px 16px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: #666;
  font-size: 14px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 24px;
  width: 500px;
  max-width: 90%;
}

.modal-content h3 {
  margin: 0 0 8px;
  font-size: 18px;
  color: #333;
}

.modal-survey-title {
  margin: 0 0 16px;
  color: #666;
  font-size: 14px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  color: #333;
}

.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  resize: vertical;
  box-sizing: border-box;
}

.form-group textarea:focus {
  outline: none;
  border-color: #667eea;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.cancel-btn {
  padding: 10px 20px;
  background: #f0f0f0;
  color: #333;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.confirm-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.confirm-btn.reject {
  background: #c62828;
}
</style>
