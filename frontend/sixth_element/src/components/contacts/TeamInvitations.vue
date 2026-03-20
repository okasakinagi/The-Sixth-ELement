<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import * as teamApi from '@/utils/teamApi'

const router = useRouter()

// States
const isLoading = ref(true)
const errorMessage = ref('')
const invitations = reactive([])
const processingId = ref(null)
const currentTeamTitle = ref('')

const actionConfirm = reactive({
  visible: false,
  type: '',
  title: '',
  message: '',
  payload: null,
  loading: false,
  error: '',
})

const resultDialog = reactive({
  visible: false,
  title: '',
  message: '',
})

function showResult(title, message) {
  resultDialog.title = title
  resultDialog.message = message
  resultDialog.visible = true
}

function closeResult() {
  resultDialog.visible = false
  resultDialog.title = ''
  resultDialog.message = ''
}

function closeConfirm() {
  actionConfirm.visible = false
  actionConfirm.type = ''
  actionConfirm.title = ''
  actionConfirm.message = ''
  actionConfirm.payload = null
  actionConfirm.loading = false
  actionConfirm.error = ''
}

// 初始化时加载邀请
onMounted(async () => {
  await loadMyTeam()
  await loadInvitations()
})

async function loadMyTeam() {
  try {
    const result = await teamApi.getMyTeam()
    currentTeamTitle.value = result?.team?.title || ''
  } catch (_) {
    currentTeamTitle.value = ''
  }
}

// 加载待处理邀请列表
async function loadInvitations() {
  try {
    isLoading.value = true
    errorMessage.value = ''
    
    const result = await teamApi.getPendingInvitations()
    invitations.length = 0
    
    if (result.invitations && Array.isArray(result.invitations)) {
      invitations.push(...result.invitations)
    }
  } catch (error) {
    errorMessage.value = error.message || '加载邀请列表失败'
    console.error('加载邀请错误:', error)
  } finally {
    isLoading.value = false
  }
}

// 接受邀请
function openAcceptConfirm(invitation) {
  const hasCurrentTeam = !!currentTeamTitle.value
  actionConfirm.type = 'accept'
  actionConfirm.title = '确认接受邀请'
  actionConfirm.message = hasCurrentTeam
    ? `你当前在队伍「${currentTeamTitle.value}」。确认后将先退出当前队伍，再加入「${invitation.team_title}」；后续填写问卷获得的积分将自动记录到新队长统计。`
    : `确认加入「${invitation.team_title}」吗？加入后你填写问卷获得的积分将自动记录到队长统计。`
  actionConfirm.payload = invitation
  actionConfirm.error = ''
  actionConfirm.visible = true
}

function openRejectConfirm(invitation) {
  actionConfirm.type = 'reject'
  actionConfirm.title = '确认拒绝邀请'
  actionConfirm.message = `确认拒绝来自 ${invitation.inviter_nickname} 的邀请吗？`
  actionConfirm.payload = invitation
  actionConfirm.error = ''
  actionConfirm.visible = true
}

async function runConfirmedAction() {
  if (!actionConfirm.payload) {
    closeConfirm()
    return
  }

  try {
    actionConfirm.loading = true
    const invitationId = actionConfirm.payload.invitation_id
    processingId.value = invitationId

    if (actionConfirm.type === 'accept') {
      await teamApi.acceptInvitation(invitationId)
      const index = invitations.findIndex(inv => inv.invitation_id === invitationId)
      if (index !== -1) {
        invitations.splice(index, 1)
      }
      window.dispatchEvent(new CustomEvent('team:updated'))
      currentTeamTitle.value = actionConfirm.payload.team_title || currentTeamTitle.value
      closeConfirm()
      showResult('已加入队伍', '加入成功。后续你填写问卷获得的积分将自动记录到队长统计。')
      return
    }

    await teamApi.rejectInvitation(invitationId)
    const index = invitations.findIndex(inv => inv.invitation_id === invitationId)
    if (index !== -1) {
      invitations.splice(index, 1)
    }
    window.dispatchEvent(new CustomEvent('team:updated'))
    closeConfirm()
    showResult('已拒绝邀请', '邀请状态已更新。')
  } catch (error) {
    actionConfirm.error = error.message || '操作失败'
    console.error('邀请操作错误:', error)
  } finally {
    actionConfirm.loading = false
    processingId.value = null
  }
}

function goBack() {
  router.back()
}
</script>

<template>
  <div class="invitations-page">
    <!-- Header -->
    <div class="page-header">
      <button class="back-btn" @click="goBack">
        <span class="icon">←</span> 返回
      </button>
      <h1>待处理邀请</h1>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <!-- Error State -->
    <div v-if="errorMessage && !isLoading" class="error-message">
      ⚠️ {{ errorMessage }}
      <button @click="loadInvitations" class="retry-btn">重试</button>
    </div>

    <!-- Empty State -->
    <div v-if="!isLoading && !errorMessage && invitations.length === 0" class="empty-state">
      <div class="empty-icon">📬</div>
      <h3>暂无邀请</h3>
      <p>当有人邀请你加入队伍时，邀请会显示在这里</p>
      <button class="back-to-teams" @click="goBack">返回</button>
    </div>

    <!-- Invitations List -->
    <div v-if="!isLoading && !errorMessage && invitations.length > 0" class="invitations-list">
      <div v-for="invitation in invitations" :key="invitation.invitation_id" class="invitation-card">
        <div class="card-header">
          <div class="team-info">
            <h3 class="team-name">{{ invitation.team_title }}</h3>
            <p class="inviter-info">由 <strong>{{ invitation.inviter_nickname }}</strong> 邀请</p>
          </div>
          <div class="invite-time">
            {{ new Date(invitation.created_at).toLocaleDateString('zh-CN') }}
          </div>
        </div>

        <div class="card-actions">
          <button 
            class="btn accept-btn" 
            :disabled="processingId === invitation.invitation_id"
            @click="openAcceptConfirm(invitation)"
          >
            {{ processingId === invitation.invitation_id ? '处理中...' : '✅ 接受' }}
          </button>
          <button 
            class="btn reject-btn" 
            :disabled="processingId === invitation.invitation_id"
            @click="openRejectConfirm(invitation)"
          >
            {{ processingId === invitation.invitation_id ? '处理中...' : '❌ 拒绝' }}
          </button>
        </div>
      </div>
    </div>

    <transition name="modal-fade">
      <div v-if="actionConfirm.visible" class="modal-overlay" @click.self="closeConfirm">
        <div class="modal-card">
          <h3>{{ actionConfirm.title }}</h3>
          <p>{{ actionConfirm.message }}</p>
          <p v-if="actionConfirm.error" class="modal-error">⚠️ {{ actionConfirm.error }}</p>
          <div class="modal-actions">
            <button class="btn reject-btn" @click="closeConfirm" :disabled="actionConfirm.loading">取消</button>
            <button class="btn accept-btn" @click="runConfirmedAction" :disabled="actionConfirm.loading">
              {{ actionConfirm.loading ? '处理中...' : '确认' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="modal-fade">
      <div v-if="resultDialog.visible" class="modal-overlay" @click.self="closeResult">
        <div class="modal-card">
          <h3>{{ resultDialog.title }}</h3>
          <p>{{ resultDialog.message }}</p>
          <div class="modal-actions">
            <button class="btn accept-btn" @click="closeResult">我知道了</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
/* Page Layout */
.invitations-page {
  max-width: 600px;
  margin: 0 auto;
  padding: 24px;
  min-height: 100vh;
}

/* Header */
.page-header {
  margin-bottom: 32px;
}

.back-btn {
  background: none;
  border: none;
  font-size: 14px;
  color: #64748b;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 16px;
  padding: 0;
  font-weight: 500;
}
.back-btn:hover { color: #475569; }

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #1e293b;
  font-weight: 700;
}

/* Loading State */
.loading-container {
  text-align: center;
  padding: 48px 24px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  margin: 0 auto 16px;
  border: 3px solid #e2e8f0;
  border-top-color: #4f46e5;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-container p {
  color: #64748b;
  font-size: 14px;
}

/* Error State */
.error-message {
  background: #fee2e2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.retry-btn {
  background: #dc2626;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.retry-btn:hover {
  background: #b91c1c;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 64px 24px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-state h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #1e293b;
  font-weight: 600;
}

.empty-state p {
  margin: 0 0 24px 0;
  color: #64748b;
  font-size: 14px;
}

.back-to-teams {
  background: #4f46e5;
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.back-to-teams:hover {
  background: #4338ca;
}

/* Invitations List */
.invitations-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.invitation-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  transition: all 0.2s;
}

.invitation-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f1f5f9;
}

.team-info {
  flex: 1;
}

.team-name {
  margin: 0 0 6px 0;
  font-size: 16px;
  color: #1e293b;
  font-weight: 600;
}

.inviter-info {
  margin: 0;
  font-size: 13px;
  color: #64748b;
}

.invite-time {
  font-size: 12px;
  color: #94a3b8;
  white-space: nowrap;
  margin-left: 16px;
}

/* Card Actions */
.card-actions {
  display: flex;
  gap: 12px;
}

.btn {
  flex: 1;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.accept-btn {
  background: #dcfce7;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.accept-btn:hover:not(:disabled) {
  background: #bbf7d0;
}

.reject-btn {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.reject-btn:hover:not(:disabled) {
  background: #fecaca;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1200;
  padding: 16px;
}

.modal-card {
  width: min(520px, 100%);
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.2);
}

.modal-card h3 {
  margin: 0 0 10px 0;
  color: #0f172a;
}

.modal-card p {
  margin: 0;
  color: #334155;
  line-height: 1.6;
}

.modal-error {
  margin-top: 10px !important;
  color: #b91c1c !important;
}

.modal-actions {
  margin-top: 16px;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
