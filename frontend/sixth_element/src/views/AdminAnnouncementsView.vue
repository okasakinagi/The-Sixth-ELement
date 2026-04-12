<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getAnnouncementList, createAnnouncement } from '@/utils/adminApi'
import { useAdminTheme } from '@/composables/useAdminTheme'

const router = useRouter()
const { initTheme } = useAdminTheme()
const announcements = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const showCreateModal = ref(false)
const createForm = ref({ title: '', content: '', target_type: 'all' })

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

async function fetchAnnouncements() {
  loading.value = true
  try {
    const data = await getAnnouncementList(page.value, pageSize.value)
    announcements.value = data.messages || []
    total.value = data.total || 0
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!createForm.value.title.trim() || !createForm.value.content.trim()) {
    alert('标题和内容不能为空')
    return
  }
  try {
    await createAnnouncement(createForm.value)
    showCreateModal.value = false
    await fetchAnnouncements()
  } catch (e) {
    console.error(e)
    alert('创建失败')
  }
}

async function changePage(newPage) {
  page.value = newPage
  await fetchAnnouncements()
}
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
          <span class="breadcrumb-current">系统公告</span>
        </div>
        <div class="header-top">
          <h1 class="page-title">系统公告</h1>
          <div class="header-right">
            <button class="create-btn" @click="showCreateModal = true">+ 发送公告</button>
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
                <th>标题</th>
                <th>内容摘要</th>
                <th>接收者</th>
                <th>发送时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in announcements" :key="item.id">
                <td>{{ item.id }}</td>
                <td>{{ item.title }}</td>
                <td class="content-cell">{{ item.content?.slice(0, 50) }}{{ item.content?.length > 50 ? '...' : '' }}</td>
                <td>{{ item.recipient }}</td>
                <td>{{ item.created_at?.slice(0, 19) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="announcements.length === 0" class="empty-state">
          暂无公告记录
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

    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal-content">
        <h3>发送系统公告</h3>
        <div class="form-group">
          <label>标题</label>
          <input v-model="createForm.title" type="text" placeholder="公告标题" />
        </div>
        <div class="form-group">
          <label>内容</label>
          <textarea v-model="createForm.content" placeholder="公告内容" rows="5"></textarea>
        </div>
        <div class="form-group">
          <label>发送范围</label>
          <select v-model="createForm.target_type">
            <option value="all">全部用户</option>
            <option value="active">活跃用户</option>
            <option value="inactive">非活跃用户</option>
          </select>
        </div>
        <div class="modal-actions">
          <button class="cancel-btn" @click="showCreateModal = false">取消</button>
          <button class="confirm-btn" @click="handleCreate">发送</button>
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

.create-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
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

.content-cell {
  max-width: 300px;
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
  margin: 0 0 20px;
  font-size: 18px;
  color: #333;
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

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
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
</style>
