<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getSurveyList, getSurveyDetail, exportSurveysData, createSurvey, updateSurvey, deleteSurvey, forceCloseSurvey } from '@/utils/adminApi'
import { useAdminTheme } from '@/composables/useAdminTheme'

const router = useRouter()
const { initTheme, themeVars } = useAdminTheme()
const surveys = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const status = ref('')
const search = ref('')
const loading = ref(false)
const selectedSurvey = ref(null)
const showDetailModal = ref(false)
const showEditModal = ref(false)
const editingSurvey = ref(null)
const editForm = ref({ title: '', description: '', difficulty: '', estimated_minutes: 0, target: 0, reward_points: 0 })
const showDeleteModal = ref(false)
const deletingSurvey = ref(null)
const showCreateModal = ref(false)
const createForm = ref({ title: '', description: '', difficulty: '', estimated_minutes: 0, target: 0, reward_points: 0 })
let searchTimer = null

const STORAGE_KEY = 'admin_survey_filters'

const statusOptions = [
  { label: '全部', value: '' },
  { label: '草稿', value: 'draft' },
  { label: '已发布', value: 'published' },
  { label: '已结束', value: 'completed' },
]

const startDate = ref('')
const endDate = ref('')

function saveFilters() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({
    status: status.value,
    search: search.value,
    page: page.value,
    startDate: startDate.value,
    endDate: endDate.value,
  }))
}

function loadFilters() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const filters = JSON.parse(saved)
      status.value = filters.status || ''
      search.value = filters.search || ''
      page.value = filters.page || 1
      startDate.value = filters.startDate || ''
      endDate.value = filters.endDate || ''
    }
  } catch (e) {
    console.error('Failed to load filters:', e)
  }
}

async function fetchSurveys() {
  loading.value = true
  try {
    const data = await getSurveyList(page.value, pageSize.value, status.value, search.value, startDate.value, endDate.value)
    surveys.value = data.surveys || []
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
  await fetchSurveys()
}

function handleSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    handleSearch()
  }, 500)
}

async function changeStatusFilter(newStatus) {
  status.value = newStatus
  page.value = 1
  await fetchSurveys()
}

async function resetDateFilter() {
  startDate.value = ''
  endDate.value = ''
  page.value = 1
  await fetchSurveys()
}

async function applyDateFilter() {
  page.value = 1
  await fetchSurveys()
}

async function changePage(newPage) {
  page.value = newPage
  await fetchSurveys()
}

async function handleExport() {
  try {
    const data = await exportSurveysData()
    if (data && data.data) {
      const csvHeader = Object.keys(data.data[0]).join(',')
      const csvRows = data.data.map(row => Object.values(row).join(','))
      const csvContent = [csvHeader, ...csvRows].join('\n')
      const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `surveys_export_${new Date().toISOString().slice(0,10)}.csv`
      link.click()
      URL.revokeObjectURL(url)
    }
  } catch (e) {
    console.error('Export failed:', e)
    alert('导出失败')
  }
}

async function viewSurvey(surveyId) {
  try {
    const data = await getSurveyDetail(surveyId)
    if (data && data.id) {
      selectedSurvey.value = data
      showDetailModal.value = true
    } else {
      console.error('Invalid survey data:', data)
      alert('获取问卷详情失败：无效的数据格式')
    }
  } catch (e) {
    console.error('viewSurvey error:', e)
    alert('获取问卷详情失败: ' + (e.message || '未知错误') + '\n\n请检查浏览器控制台获取更多详情')
  }
}

function closeModal() {
  showDetailModal.value = false
  selectedSurvey.value = null
}

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

function getStatusClass(status) {
  if (status === 'draft') return 'status-draft'
  if (status === 'published') return 'status-published'
  if (status === 'completed') return 'status-completed'
  if (status === 'abnormal') return 'status-abnormal'
  return ''
}

function getStatusText(status) {
  if (status === 'draft') return '草稿'
  if (status === 'published') return '已发布'
  if (status === 'completed') return '已结束'
  if (status === 'abnormal') return '异常'
  return status
}

function getDifficultyText(difficulty) {
  const map = { 1: '简单', 2: '较简单', 3: '中等', 4: '较难', 5: '困难' }
  return map[difficulty] || '中等'
}

onMounted(() => {
  initTheme()
  loadFilters()
  fetchSurveys()
})

function openCreateModal() {
  createForm.value = { title: '', description: '', difficulty: '', estimated_minutes: 0, target: 0, reward_points: 0 }
  showCreateModal.value = true
}

async function handleCreate() {
  try {
    await createSurvey(createForm.value)
    showCreateModal.value = false
    await fetchSurveys()
  } catch (e) {
    console.error(e)
    alert('创建失败')
  }
}

function openEditModal(survey) {
  editingSurvey.value = survey
  editForm.value = {
    title: survey.title,
    description: survey.description || '',
    difficulty: survey.difficulty || '',
    estimated_minutes: survey.estimated_minutes || 0,
    target: survey.target || 0,
    reward_points: survey.reward_points || 0
  }
  showEditModal.value = true
}

async function handleEdit() {
  try {
    await updateSurvey(editingSurvey.value.id, editForm.value)
    showEditModal.value = false
    await fetchSurveys()
  } catch (e) {
    console.error(e)
    alert('编辑失败')
  }
}

function openDeleteModal(survey) {
  deletingSurvey.value = survey
  showDeleteModal.value = true
}

async function handleDelete() {
  try {
    await deleteSurvey(deletingSurvey.value.id)
    showDeleteModal.value = false
    deletingSurvey.value = null
    await fetchSurveys()
  } catch (e) {
    console.error(e)
    alert('删除失败')
  }
}

function openCloseModal(survey) {
  if (confirm(`确定要强制结束问卷「${survey.title}」吗？`)) {
    forceCloseSurvey(survey.id).then(() => fetchSurveys()).catch(e => {
      console.error(e)
      alert('操作失败')
    })
  }
}

function highlightText(text, keyword) {
  if (!keyword || !text) return text
  const regex = new RegExp(`(${keyword})`, 'gi')
  return text.replace(regex, '<mark class="search-highlight">$1</mark>')
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
          <span class="breadcrumb-current">问卷管理</span>
        </div>
        <div class="header-top">
          <h1 class="page-title">问卷管理</h1>
          <div class="header-right">
            <span class="total-count">共 {{ total }} 份问卷</span>
            <button class="export-btn" @click="handleExport">📄 导出</button>
            <button class="create-btn" @click="openCreateModal">+ 新建问卷</button>
          </div>
        </div>
      </header>

      <div class="filters-bar">
        <input
          v-model="search"
          type="text"
          class="search-input"
          placeholder="搜索问卷标题..."
          @input="handleSearchInput"
          @keyup.enter="handleSearch"
        />
        <button class="search-btn" @click="handleSearch">搜索</button>
        <div class="status-filters">
          <button
            v-for="opt in statusOptions"
            :key="opt.value"
            class="filter-btn"
            :class="{ active: status === opt.value }"
            @click="changeStatusFilter(opt.value)"
          >
            {{ opt.label }}
          </button>
        </div>
        <div class="date-filters">
          <span class="date-label">创建时间：</span>
          <input v-model="startDate" type="date" class="date-input" placeholder="开始日期" />
          <span class="date-sep">至</span>
          <input v-model="endDate" type="date" class="date-input" placeholder="结束日期" />
          <button class="date-btn" @click="applyDateFilter">应用</button>
          <button v-if="startDate || endDate" class="date-btn reset" @click="resetDateFilter">重置</button>
        </div>
      </div>

      <div v-if="loading" class="loading">加载中...</div>
      <template v-else>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>问卷标题</th>
                <th>创建者</th>
                <th>状态</th>
                <th>难度</th>
                <th>完成/目标</th>
                <th>发布时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="survey in surveys" :key="survey.id">
                <td>{{ survey.id }}</td>
                <td class="title-cell"><span v-html="highlightText(survey.title, search)"></span></td>
                <td>
                  <span class="owner-name">{{ survey.owner_nickname }}</span>
                </td>
                <td>
                  <span class="status-badge" :class="getStatusClass(survey.status)">
                    {{ getStatusText(survey.status) }}
                  </span>
                </td>
                <td>{{ getDifficultyText(survey.difficulty) }}</td>
                <td>
                  <span class="count-text">{{ survey.completed }}</span> /
                  <span class="target-text">{{ survey.target }}</span>
                </td>
                <td>{{ survey.created_at?.slice(0, 10) }}</td>
                <td>
                  <button class="action-btn" @click="viewSurvey(survey.id)">详情</button>
                  <button class="action-btn edit-btn" @click="openEditModal(survey)">编辑</button>
                  <button class="action-btn delete-btn" @click="openDeleteModal(survey)">删除</button>
                  <button v-if="survey.status === 'published'" class="action-btn close-btn" @click="openCloseModal(survey)">结束</button>
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
          <h3>问卷详情</h3>
          <button class="modal-close-btn" @click="closeModal">×</button>
        </div>
        <div v-if="selectedSurvey" class="modal-body">
          <div class="detail-grid">
            <div class="detail-item full-width">
              <label>问卷标题</label>
              <span>{{ selectedSurvey.title }}</span>
            </div>
            <div class="detail-item full-width">
              <label>问卷描述</label>
              <span>{{ selectedSurvey.description || '无' }}</span>
            </div>
            <div class="detail-item">
              <label>问卷ID</label>
              <span>{{ selectedSurvey.id }}</span>
            </div>
            <div class="detail-item">
              <label>创建者</label>
              <span>{{ selectedSurvey.owner_nickname }}</span>
            </div>
            <div class="detail-item">
              <label>状态</label>
              <span class="status-badge" :class="getStatusClass(selectedSurvey.status)">
                {{ getStatusText(selectedSurvey.status) }}
              </span>
            </div>
            <div class="detail-item">
              <label>难度</label>
              <span>{{ getDifficultyText(selectedSurvey.difficulty) }}</span>
            </div>
            <div class="detail-item">
              <label>预估时间</label>
              <span>{{ selectedSurvey.estimated_minutes || 0 }} 分钟</span>
            </div>
            <div class="detail-item">
              <label>目标份数</label>
              <span>{{ selectedSurvey.target }}</span>
            </div>
            <div class="detail-item">
              <label>完成份数</label>
              <span>{{ selectedSurvey.completed }}</span>
            </div>
            <div class="detail-item">
              <label>奖励积分</label>
              <span>{{ selectedSurvey.reward_points }}</span>
            </div>
            <div class="detail-item">
              <label>发布消耗</label>
              <span>{{ selectedSurvey.publish_cost_points }}</span>
            </div>
            <div class="detail-item">
              <label>AI生成</label>
              <span>{{ selectedSurvey.ai_generated ? '是' : '否' }}</span>
            </div>
            <div class="detail-item">
              <label>填写次数</label>
              <span>{{ selectedSurvey.response_count }}</span>
            </div>
            <div class="detail-item">
              <label>平均填写时长</label>
              <span>{{ selectedSurvey.avg_duration_seconds }} 秒</span>
            </div>
            <div class="detail-item">
              <label>创建时间</label>
              <span>{{ selectedSurvey.created_at?.slice(0, 19) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>新建问卷</h3>
          <button class="modal-close-btn" @click="showCreateModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>标题</label>
            <input v-model="createForm.title" type="text" placeholder="问卷标题" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="createForm.description" placeholder="问卷描述" rows="3"></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>难度 (1-5)</label>
              <input v-model.number="createForm.difficulty" type="number" min="1" max="5" />
            </div>
            <div class="form-group">
              <label>预计时间(分钟)</label>
              <input v-model.number="createForm.estimated_minutes" type="number" min="0" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>目标回收</label>
              <input v-model.number="createForm.target" type="number" min="0" />
            </div>
            <div class="form-group">
              <label>奖励积分</label>
              <input v-model.number="createForm.reward_points" type="number" min="0" />
            </div>
          </div>
          <div class="modal-actions">
            <button class="cancel-btn" @click="showCreateModal = false">取消</button>
            <button class="confirm-btn" @click="handleCreate">创建</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>编辑问卷</h3>
          <button class="modal-close-btn" @click="showEditModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>标题</label>
            <input v-model="editForm.title" type="text" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="editForm.description" rows="3"></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>难度 (1-5)</label>
              <input v-model.number="editForm.difficulty" type="number" min="1" max="5" />
            </div>
            <div class="form-group">
              <label>预计时间(分钟)</label>
              <input v-model.number="editForm.estimated_minutes" type="number" min="0" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>目标回收</label>
              <input v-model.number="editForm.target" type="number" min="0" />
            </div>
            <div class="form-group">
              <label>奖励积分</label>
              <input v-model.number="editForm.reward_points" type="number" min="0" />
            </div>
          </div>
          <div class="modal-actions">
            <button class="cancel-btn" @click="showEditModal = false">取消</button>
            <button class="confirm-btn" @click="handleEdit">保存</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showDeleteModal" class="modal-overlay" @click.self="showDeleteModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>删除问卷</h3>
          <button class="modal-close-btn" @click="showDeleteModal = false">×</button>
        </div>
        <div class="modal-body">
          <p class="delete-confirm-text">确定要删除问卷 <strong>{{ deletingSurvey?.title }}</strong> 吗？此操作不可恢复！</p>
          <div class="modal-actions">
            <button class="cancel-btn" @click="showDeleteModal = false">取消</button>
            <button class="confirm-btn danger" @click="handleDelete">删除</button>
          </div>
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

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filters-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  align-items: center;
}

.search-input {
  flex: 1;
  min-width: 200px;
  padding: 6px 12px;
  border: 1px solid var(--admin-border-color);
  border-radius: 8px;
  font-size: 13px;
  height: 32px;
  box-sizing: border-box;
  background: var(--admin-bg-card);
  color: var(--admin-text-primary);
}

.export-btn {
  padding: 6px 12px;
  background: linear-gradient(135deg, #48c774 0%, #3c9d5b 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.create-btn {
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
}

.delete-confirm-text {
  font-size: 14px;
  color: var(--admin-text-primary);
  line-height: 1.6;
  margin-bottom: 20px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.cancel-btn {
  padding: 10px 20px;
  background: var(--admin-bg-secondary);
  color: var(--admin-text-primary);
  border: 1px solid var(--admin-border-color);
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.confirm-btn {
  padding: 10px 20px;
  background: var(--admin-accent-gradient);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.confirm-btn.danger {
  background: linear-gradient(135deg, #ef5350 0%, #c62828 100%);
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

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--admin-border-color);
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
  background: var(--admin-bg-secondary);
  color: var(--admin-text-primary);
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #667eea;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-row .form-group {
  flex: 1;
}

.date-filters {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 12px 16px;
  background: var(--admin-bg-secondary);
  border: 1px solid var(--admin-border-color);
  border-radius: 8px;
}

.date-label {
  font-size: 13px;
  color: var(--admin-text-secondary);
  font-weight: 500;
}

.date-input {
  padding: 4px 8px;
  border: 1px solid var(--admin-border-color);
  border-radius: 6px;
  font-size: 13px;
  width: 140px;
  height: 32px;
  box-sizing: border-box;
  background: var(--admin-bg-card);
  color: var(--admin-text-primary);
}

.date-sep {
  color: var(--admin-text-muted);
  font-size: 13px;
}

.date-btn {
  padding: 4px 12px;
  background: var(--admin-accent-gradient);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  height: 32px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
}

.date-btn.reset {
  background: var(--admin-text-muted);
}

.search-btn {
  padding: 6px 14px;
  background: var(--admin-accent-gradient);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  height: 32px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.search-highlight {
  background: #fff3cd;
  color: #856404;
  padding: 0 2px;
  border-radius: 2px;
}
.status-filters {
  display: flex;
  gap: 8px;
}

.filter-btn {
  padding: 6px 12px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
  height: 32px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
}

.filter-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
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
  padding: 14px 16px;
  text-align: left;
  font-weight: 600;
  font-size: 13px;
  color: #333;
  border-bottom: 1px solid #eee;
}

.data-table td {
  padding: 14px 16px;
  font-size: 13px;
  color: #333;
  border-bottom: 1px solid #f5f5f5;
}

.title-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.owner-name {
  font-weight: 500;
}

.count-text {
  color: #667eea;
  font-weight: 600;
}

.target-text {
  color: #888;
}

.status-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.status-draft {
  background: #f5f5f5;
  color: #666;
}

.status-published {
  background: #e3f2fd;
  color: #1565c0;
}

.status-completed {
  background: #e8f5e9;
  color: #2e7d32;
}

.status-abnormal {
  background: #ffebee;
  color: #c62828;
}

.action-btn {
  padding: 8px 14px;
  background: #f0f0f0;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
  margin-right: 6px;
}

.action-btn:hover {
  background: #e0e0e0;
}

.action-btn:last-child {
  margin-right: 0;
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
  border: 1px solid #ddd;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.page-btn:hover:not(:disabled) {
  background: #f5f5f5;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 13px;
  color: #666;
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
  width: 90%;
  max-width: 700px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

.modal-close-btn {
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  color: #999;
  line-height: 1;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.modal-close-btn:hover {
  background: #f0f0f0;
  color: #666;
}

.edit-btn {
  background: #e3f2fd;
  color: #1976d2;
}

.edit-btn:hover {
  background: #bbdefb;
}

.delete-btn {
  background: #ffebee;
  color: #c62828;
}

.delete-btn:hover {
  background: #ffcdd2;
}

.action-btn.close-btn {
  background: #fff3e0;
  color: #e65100;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 500;
}

.action-btn.close-btn:hover {
  background: #ffe0b2;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  max-height: calc(80vh - 60px);
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
}

.detail-item.full-width {
  grid-column: span 2;
}

.detail-item label {
  font-size: 12px;
  color: #888;
  font-weight: 500;
}

.detail-item span {
  font-size: 14px;
  color: #333;
  word-break: break-word;
}

.detail-item span {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}
</style>
