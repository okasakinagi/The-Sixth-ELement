<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getOperationLogs } from '@/utils/adminApi'
import { useAdminTheme } from '@/composables/useAdminTheme'

const router = useRouter()
const { initTheme } = useAdminTheme()
const logs = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const actionFilter = ref('')
const targetTypeFilter = ref('')

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

const actionOptions = [
  { value: '', label: '全部操作' },
  { value: 'update_user', label: '更新用户' },
  { value: 'delete_user', label: '删除用户' },
  { value: 'create_survey', label: '创建问卷' },
  { value: 'delete_survey', label: '删除问卷' },
]

const targetTypeOptions = [
  { value: '', label: '全部类型' },
  { value: 'user', label: '用户' },
  { value: 'survey', label: '问卷' },
]

async function fetchLogs() {
  loading.value = true
  try {
    const data = await getOperationLogs(page.value, pageSize.value, actionFilter.value, targetTypeFilter.value)
    logs.value = data.logs || []
    total.value = data.total || 0
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function changePage(newPage) {
  page.value = newPage
  await fetchLogs()
}

async function applyFilters() {
  page.value = 1
  await fetchLogs()
}

onMounted(() => {
  initTheme()
  fetchLogs()
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
          <span class="breadcrumb-current">操作日志</span>
        </div>
        <div class="header-top">
          <h1 class="page-title">操作日志</h1>
          <div class="header-right">
            <span class="total-count">共 {{ total }} 条记录</span>
          </div>
        </div>
      </header>

      <div class="filters">
        <select v-model="actionFilter" @change="applyFilters" class="filter-select">
          <option v-for="opt in actionOptions" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>
        <select v-model="targetTypeFilter" @change="applyFilters" class="filter-select">
          <option v-for="opt in targetTypeOptions" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>
      </div>

      <div v-if="loading" class="loading">加载中...</div>
      <template v-else>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>操作类型</th>
                <th>操作对象</th>
                <th>操作人</th>
                <th>备注</th>
                <th>时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in logs" :key="item.id">
                <td>{{ item.id }}</td>
                <td>
                  <span class="action-tag" :class="item.action">{{ item.action }}</span>
                </td>
                <td>{{ item.target_type }} #{{ item.target_id }}</td>
                <td>{{ item.operator }}</td>
                <td class="note-cell">{{ item.note || '-' }}</td>
                <td>{{ item.created_at?.slice(0, 19) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="logs.length === 0" class="empty-state">
          暂无操作记录
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
  color: #666;
  font-size: 14px;
}

.filters {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  background: white;
  cursor: pointer;
}

.filter-select:focus {
  outline: none;
  border-color: #667eea;
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

.action-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.action-tag.update_user {
  background: #e3f2fd;
  color: #1976d2;
}

.action-tag.delete_user {
  background: #ffebee;
  color: #c62828;
}

.action-tag.create_survey {
  background: #e8f5e9;
  color: #2e7d32;
}

.action-tag.delete_survey {
  background: #fff3e0;
  color: #e65100;
}

.note-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
</style>
