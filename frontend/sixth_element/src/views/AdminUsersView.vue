<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  getUserList,
  getUserDetail,
  updateUserStatus,
  updateUserInfo,
  deleteUser,
  batchUpdateUserStatus,
  batchAdjustPoints,
  exportUsersData,
} from '@/utils/adminApi'
import { useAdminTheme } from '@/composables/useAdminTheme'

const router = useRouter()
const { initTheme, themeVars } = useAdminTheme()
const users = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const search = ref('')
const loading = ref(false)
const selectedUser = ref(null)
const showDetailModal = ref(false)
const selectedUsers = ref([])
const showBatchModal = ref(false)
const batchAction = ref('')
const showBatchPointsModal = ref(false)
const batchPointsForm = ref({ delta: 0, reason: '' })
const showEditModal = ref(false)
const editingUser = ref(null)
const editForm = ref({ nickname: '', email: '', points: 0 })
const showDeleteModal = ref(false)
const deletingUser = ref(null)
let searchTimer = null

const STORAGE_KEY = 'admin_user_filters'

function saveFilters() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({
    search: search.value,
    page: page.value,
  }))
}

function loadFilters() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const filters = JSON.parse(saved)
      search.value = filters.search || ''
      page.value = filters.page || 1
    }
  } catch (e) {
    console.error('Failed to load filters:', e)
  }
}

async function fetchUsers() {
  loading.value = true
  try {
    const data = await getUserList(page.value, pageSize.value, search.value)
    users.value = data.users || []
    total.value = data.total || 0
    saveFilters()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function handleSearch() {
  page.value = 1
  await fetchUsers()
}

function handleSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    handleSearch()
  }, 500)
}

async function changePage(newPage) {
  page.value = newPage
  await fetchUsers()
}

async function handleExport() {
  try {
    const data = await exportUsersData()
    if (data && data.data) {
      const csvHeader = Object.keys(data.data[0]).join(',')
      const csvRows = data.data.map(row => Object.values(row).join(','))
      const csvContent = [csvHeader, ...csvRows].join('\n')
      const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `users_export_${new Date().toISOString().slice(0,10)}.csv`
      link.click()
      URL.revokeObjectURL(url)
    }
  } catch (e) {
    console.error('Export failed:', e)
    alert('导出失败')
  }
}

function highlightText(text, keyword) {
  if (!keyword || !text) return text
  const regex = new RegExp(`(${keyword})`, 'gi')
  return text.replace(regex, '<mark class="search-highlight">$1</mark>')
}

async function viewUser(userId) {
  try {
    const data = await getUserDetail(userId)
    selectedUser.value = data
    showDetailModal.value = true
  } catch (e) {
    console.error(e)
  }
}

async function changeStatus(userId, newStatus) {
  try {
    await updateUserStatus(userId, newStatus)
    await fetchUsers()
    showDetailModal.value = false
  } catch (e) {
    console.error(e)
  }
}

async function handleBatchStatusChange() {
  if (selectedUsers.value.length === 0) return
  try {
    await batchUpdateUserStatus(selectedUsers.value, batchAction.value)
    await fetchUsers()
    showBatchModal.value = false
    selectedUsers.value = []
  } catch (e) {
    console.error(e)
  }
}

async function handleBatchPointsAdjust() {
  if (selectedUsers.value.length === 0) return
  if (batchPointsForm.value.delta === 0) {
    alert('积分调整值不能为0')
    return
  }
  try {
    await batchAdjustPoints(
      selectedUsers.value,
      batchPointsForm.value.delta,
      batchPointsForm.value.reason || '管理员批量调整'
    )
    await fetchUsers()
    showBatchPointsModal.value = false
    batchPointsForm.value = { delta: 0, reason: '' }
    selectedUsers.value = []
    alert('批量调整积分成功')
  } catch (e) {
    console.error(e)
    alert('批量调整积分失败')
  }
}

function openBatchPointsModal() {
  if (selectedUsers.value.length === 0) return
  batchPointsForm.value = { delta: 0, reason: '' }
  showBatchPointsModal.value = true
}

function closeModal() {
  showDetailModal.value = false
  selectedUser.value = null
}

function openEditModal(user) {
  editingUser.value = user
  editForm.value = {
    nickname: user.nickname,
    email: user.email,
    points: user.points
  }
  showEditModal.value = true
}

async function handleEdit() {
  try {
    await updateUserInfo(editingUser.value.id, {
      nickname: editForm.value.nickname,
      email: editForm.value.email,
      points: editForm.value.points
    })
    showEditModal.value = false
    await fetchUsers()
  } catch (e) {
    console.error(e)
    alert('编辑失败')
  }
}

function openDeleteModal(user) {
  deletingUser.value = user
  showDeleteModal.value = true
}

async function handleDelete() {
  try {
    await deleteUser(deletingUser.value.id)
    showDeleteModal.value = false
    deletingUser.value = null
    await fetchUsers()
  } catch (e) {
    console.error(e)
    alert('删除失败')
  }
}

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

onMounted(() => {
  initTheme()
  loadFilters()
  fetchUsers()
})

function getStatusClass(status) {
  if (status === 'normal') return 'status-normal'
  if (status === 'suspicious') return 'status-suspicious'
  if (status === 'restricted') return 'status-restricted'
  return ''
}

function getStatusText(status) {
  if (status === 'normal') return '正常'
  if (status === 'suspicious') return '异常'
  if (status === 'restricted') return '受限'
  return status
}

function toggleSelect(userId) {
  const idx = selectedUsers.value.indexOf(userId)
  if (idx === -1) {
    selectedUsers.value.push(userId)
  } else {
    selectedUsers.value.splice(idx, 1)
  }
}

function toggleSelectAll() {
  if (selectedUsers.value.length === users.value.length) {
    selectedUsers.value = []
  } else {
    selectedUsers.value = users.value.map(u => u.id)
  }
}

function openBatchModal(action) {
  if (selectedUsers.value.length === 0) return
  batchAction.value = action
  showBatchModal.value = true
}
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
          <span class="breadcrumb-current">用户管理</span>
        </div>
        <div class="header-top">
          <h1 class="page-title">用户管理</h1>
          <div class="header-right">
            <span class="total-count">共 {{ total }} 位用户</span>
            <button class="export-btn" @click="handleExport">📥 导出</button>
          </div>
        </div>
      </header>

      <div class="search-bar">
        <input
          v-model="search"
          type="text"
          class="search-input"
          placeholder="搜索用户名或邮箱..."
          @input="handleSearchInput"
          @keyup.enter="handleSearch"
        />
        <button class="search-btn" @click="handleSearch">搜索</button>
      </div>

      <div v-if="selectedUsers.length > 0" class="batch-actions">
        <span class="selected-count">已选择 {{ selectedUsers.length }} 项</span>
        <button class="batch-btn batch-normal" @click="openBatchModal('normal')">设为正常</button>
        <button class="batch-btn batch-suspicious" @click="openBatchModal('suspicious')">设为异常</button>
        <button class="batch-btn batch-restricted" @click="openBatchModal('restricted')">设为受限</button>
        <button class="batch-btn batch-points" @click="openBatchPointsModal">批量调整积分</button>
        <button class="batch-btn batch-clear" @click="selectedUsers = []">清除选择</button>
      </div>

      <div v-if="loading" class="loading">加载中...</div>
      <template v-else>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th class="checkbox-col">
                  <input
                    type="checkbox"
                    :checked="selectedUsers.length === users.length && users.length > 0"
                    :indeterminate="selectedUsers.length > 0 && selectedUsers.length < users.length"
                    @change="toggleSelectAll"
                  />
                </th>
                <th>ID</th>
                <th>用户</th>
                <th>等级</th>
                <th>积分</th>
                <th>发布/填写</th>
                <th>状态</th>
                <th>注册时间</th>
                <th>最近活跃</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in users" :key="user.id">
                <td class="checkbox-col">
                  <input
                    type="checkbox"
                    :checked="selectedUsers.includes(user.id)"
                    @change="toggleSelect(user.id)"
                  />
                </td>
                <td>{{ user.id }}</td>
                <td>
                  <div class="user-cell">
                    <span class="nickname" v-html="highlightText(user.nickname, search)"></span>
                    <span class="email" v-html="highlightText(user.email, search)"></span>
                  </div>
                </td>
                <td>
                  <span class="level-badge">Lv{{ user.level }}</span>
                  <span class="title-text">{{ user.title }}</span>
                </td>
                <td>{{ user.points }}</td>
                <td>
                  <span class="count-text">{{ user.surveys_published }}</span> /
                  <span class="count-text">{{ user.fills_count }}</span>
                </td>
                <td>
                  <span class="status-badge" :class="getStatusClass(user.status)">
                    {{ getStatusText(user.status) }}
                  </span>
                </td>
                <td>{{ user.created_at?.slice(0, 10) }}</td>
                <td>{{ user.last_active_at?.slice(0, 10) || '从未' }}</td>
                <td>
                  <button class="action-btn" @click="viewUser(user.id)">详情</button>
                  <button class="action-btn edit-btn" @click="openEditModal(user)">编辑</button>
                  <button class="action-btn delete-btn" @click="openDeleteModal(user)">删除</button>
                </td>
              </tr>
            </tbody>
          </table>
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

    <div v-if="showDetailModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>用户详情</h3>
          <button class="close-btn" @click="closeModal">×</button>
        </div>
        <div v-if="selectedUser" class="modal-body">
          <div class="detail-grid">
            <div class="detail-item">
              <label>用户ID</label>
              <span>{{ selectedUser.id }}</span>
            </div>
            <div class="detail-item">
              <label>昵称</label>
              <span>{{ selectedUser.nickname }}</span>
            </div>
            <div class="detail-item">
              <label>邮箱</label>
              <span>{{ selectedUser.email }}</span>
            </div>
            <div class="detail-item">
              <label>等级</label>
              <span>Lv{{ selectedUser.level }} - {{ selectedUser.title }}</span>
            </div>
            <div class="detail-item">
              <label>经验值</label>
              <span>{{ selectedUser.exp }} EXP ({{ selectedUser.exp_in_level }}/{{ selectedUser.exp_to_next }})</span>
            </div>
            <div class="detail-item">
              <label>积分</label>
              <span>{{ selectedUser.points }}</span>
            </div>
            <div class="detail-item">
              <label>获积分总计</label>
              <span>{{ selectedUser.total_earned }}</span>
            </div>
            <div class="detail-item">
              <label>消耗积分总计</label>
              <span>{{ selectedUser.total_consumed }}</span>
            </div>
            <div class="detail-item">
              <label>发布问卷数</label>
              <span>{{ selectedUser.surveys_published }}</span>
            </div>
            <div class="detail-item">
              <label>填写问卷数</label>
              <span>{{ selectedUser.fills_count }}</span>
            </div>
            <div class="detail-item">
              <label>注册时间</label>
              <span>{{ selectedUser.created_at?.slice(0, 19) }}</span>
            </div>
            <div class="detail-item">
              <label>最近活跃</label>
              <span>{{ selectedUser.last_active_at?.slice(0, 19) || '从未活跃' }}</span>
            </div>
            <div class="detail-item">
              <label>状态</label>
              <span class="status-badge" :class="getStatusClass(selectedUser.status)">
                {{ getStatusText(selectedUser.status) }}
              </span>
            </div>
          </div>

          <div class="status-actions">
            <span class="action-label">修改状态：</span>
            <button
              v-if="selectedUser.status !== 'normal'"
              class="status-btn normal"
              @click="changeStatus(selectedUser.id, 'normal')"
            >
              设为正常
            </button>
            <button
              v-if="selectedUser.status !== 'suspicious'"
              class="status-btn suspicious"
              @click="changeStatus(selectedUser.id, 'suspicious')"
            >
              标记异常
            </button>
            <button
              v-if="selectedUser.status !== 'restricted'"
              class="status-btn restricted"
              @click="changeStatus(selectedUser.id, 'restricted')"
            >
              限制使用
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showBatchModal" class="modal-overlay" @click.self="showBatchModal = false">
      <div class="modal-content batch-modal">
        <h3>批量操作确认</h3>
        <p>确定要将选中的 {{ selectedUsers.length }} 位用户状态改为 <strong>{{ getStatusText(batchAction) }}</strong> 吗？</p>
        <div class="modal-actions">
          <button class="cancel-btn" @click="showBatchModal = false">取消</button>
          <button class="confirm-btn" @click="handleBatchStatusChange">确定</button>
        </div>
      </div>
    </div>

    <div v-if="showBatchPointsModal" class="modal-overlay" @click.self="showBatchPointsModal = false">
      <div class="modal-content batch-modal">
        <h3>批量调整积分</h3>
        <p>将为选中的 {{ selectedUsers.length }} 位用户调整积分</p>
        <div class="form-group">
          <label>积分调整值（正数增加，负数减少）</label>
          <input v-model.number="batchPointsForm.delta" type="number" placeholder="例如：100 或 -50" />
        </div>
        <div class="form-group">
          <label>调整原因（可选）</label>
          <input v-model="batchPointsForm.reason" type="text" placeholder="例如：活动奖励" />
        </div>
        <div class="modal-actions">
          <button class="cancel-btn" @click="showBatchPointsModal = false">取消</button>
          <button class="confirm-btn" @click="handleBatchPointsAdjust">确定</button>
        </div>
      </div>
    </div>

    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal-content">
        <h3>编辑用户</h3>
        <div class="form-group">
          <label>昵称</label>
          <input v-model="editForm.nickname" type="text" />
        </div>
        <div class="form-group">
          <label>邮箱</label>
          <input v-model="editForm.email" type="email" />
        </div>
        <div class="form-group">
          <label>积分</label>
          <input v-model.number="editForm.points" type="number" min="0" />
        </div>
        <div class="modal-actions">
          <button class="cancel-btn" @click="showEditModal = false">取消</button>
          <button class="confirm-btn" @click="handleEdit">保存</button>
        </div>
      </div>
    </div>

    <div v-if="showDeleteModal" class="modal-overlay" @click.self="showDeleteModal = false">
      <div class="modal-content">
        <h3>删除用户</h3>
        <p>确定要删除用户 <strong>{{ deletingUser?.nickname }}</strong> 吗？此操作不可恢复！</p>
        <div class="modal-actions">
          <button class="cancel-btn" @click="showDeleteModal = false">取消</button>
          <button class="confirm-btn danger" @click="handleDelete">删除</button>
        </div>
      </div>
    </div>
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

.total-count {
  color: var(--admin-text-secondary);
  font-size: 14px;
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.search-input {
  flex: 1;
  padding: 10px 16px;
  border: 1px solid var(--admin-border-color);
  border-radius: 8px;
  font-size: 14px;
  background: var(--admin-bg-card);
  color: var(--admin-text-primary);
}

.export-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #48c774 0%, #3c9d5b 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  margin-left: 12px;
}

.search-btn {
  padding: 10px 24px;
  background: var(--admin-accent-gradient);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: var(--admin-text-secondary);
}

.table-container {
  background: var(--admin-bg-card);
  border: 1px solid var(--admin-border-color);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  background: var(--admin-bg-secondary);
  padding: 14px 16px;
  text-align: left;
  font-weight: 600;
  font-size: 13px;
  color: var(--admin-text-primary);
  border-bottom: 1px solid var(--admin-border-color);
}

.data-table td {
  padding: 14px 16px;
  font-size: 13px;
  color: var(--admin-text-primary);
  border-bottom: 1px solid var(--admin-border-color);
}

.data-table tr:last-child td {
  border-bottom: none;
}

.user-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nickname {
  font-weight: 600;
}

.email {
  font-size: 12px;
  color: var(--admin-text-muted);
}

.level-badge {
  display: inline-block;
  background: linear-gradient(135deg, #ffd700 0%, #ffb400 100%);
  color: #1a1a2e;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}

.title-text {
  margin-left: 8px;
  font-size: 12px;
  color: var(--admin-text-secondary);
}

.count-text {
  color: #667eea;
  font-weight: 600;
}

.status-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.status-normal {
  background: #e8f5e9;
  color: #2e7d32;
}

.status-suspicious {
  background: #fff3e0;
  color: #e65100;
}

.status-restricted {
  background: #ffebee;
  color: #c62828;
}

.action-btn {
  padding: 6px 12px;
  background: #f0f0f0;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.2s;
}

.action-btn:hover {
  background: #e0e0e0;
}

.edit-btn {
  background: #e3f2fd;
  color: #1976d2;
  margin-left: 4px;
}

.edit-btn:hover {
  background: #bbdefb;
}

.delete-btn {
  background: #ffebee;
  color: #c62828;
  margin-left: 4px;
}

.delete-btn:hover {
  background: #ffcdd2;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 20px;
}

.page-btn {
  padding: 8px 16px;
  border: 1px solid var(--admin-border-color);
  background: var(--admin-bg-secondary);
  color: var(--admin-text-secondary);
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  background: var(--admin-bg-card);
  color: var(--admin-text-primary);
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 13px;
  color: var(--admin-text-secondary);
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
  background: var(--admin-bg-card);
  border: 1px solid var(--admin-border-color);
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--admin-border-color);
  background: var(--admin-bg-secondary);
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: var(--admin-text-primary);
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--admin-text-muted);
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  max-height: calc(80vh - 60px);
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  color: var(--admin-text-primary);
}

.form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--admin-border-color);
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
  background: var(--admin-bg-secondary);
  color: var(--admin-text-primary);
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-item label {
  font-size: 12px;
  color: var(--admin-text-muted);
}

.detail-item span {
  font-size: 14px;
  color: var(--admin-text-primary);
  font-weight: 500;
}

.status-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--admin-border-color);
}

.action-label {
  font-size: 13px;
  color: var(--admin-text-secondary);
}

.status-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: opacity 0.2s;
}

.status-btn:hover {
  opacity: 0.8;
}

.status-btn.normal {
  background: #e8f5e9;
  color: #2e7d32;
}

.status-btn.suspicious {
  background: #fff3e0;
  color: #e65100;
}

.status-btn.restricted {
  background: #ffebee;
  color: #c62828;
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--admin-bg-secondary);
  border: 1px solid var(--admin-border-color);
  border-radius: 8px;
  margin-bottom: 16px;
}

.selected-count {
  font-size: 13px;
  color: #667eea;
  font-weight: 600;
  margin-right: 8px;
}

.batch-btn {
  padding: 6px 14px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.batch-btn:hover {
  opacity: 0.85;
  transform: translateY(-1px);
}

.batch-normal {
  background: #e8f5e9;
  color: #2e7d32;
}

.batch-suspicious {
  background: #fff3e0;
  color: #e65100;
}

.batch-restricted {
  background: #ffebee;
  color: #c62828;
}

.batch-points {
  background: linear-gradient(135deg, #ffd700 0%, #ffb400 100%);
  color: #1a1a2e;
}

.batch-clear {
  background: #f5f5f5;
  color: #666;
  margin-left: auto;
}

.batch-modal {
  max-width: 400px;
  padding: 24px;
}

.batch-modal h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
}

.batch-modal p {
  margin: 0 0 24px 0;
  color: #666;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.cancel-btn {
  padding: 10px 20px;
  background: #f5f5f5;
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

.confirm-btn.danger {
  background: linear-gradient(135deg, #ef5350 0%, #c62828 100%);
}

.search-highlight {
  background: #fff3cd;
  color: #856404;
  padding: 0 2px;
  border-radius: 2px;
}

.checkbox-col {
  width: 40px;
  text-align: center;
}

.checkbox-col input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #667eea;
}
</style>
