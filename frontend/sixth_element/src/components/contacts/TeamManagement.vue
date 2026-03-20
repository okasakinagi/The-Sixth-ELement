
<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as teamApi from '@/utils/teamApi'

const route = useRoute()
const router = useRouter()
const teamId = route.params.teamId

// Loading and error states
const isLoading = ref(true)
const errorMessage = ref('')

// Team Data - Fetched from API
const teamInfo = reactive({
  id: teamId,
  title: '',
  description: '',
  icon: '',
  owner_id: null,
  created_at: '',
  max_members: 8
})

// Editing State
const isEditing = ref(false)
const editForm = reactive({
  title: '',
  description: '',
  icon: '',
  max_members: 8,
})

// Predefined icons for selection
const availableIcons = ['🚀', '🛡️', '⚔️', '💎', '🎮', '📚', '💼', '🎨', '🦁', '⚡']

// Members data from API
const members = reactive([])
const currentUserRole = ref('member')

// 邀请相关状态
const showInviteModal = ref(false)
const inviteEmail = ref('')
const inviteLoading = ref(false)
const inviteError = ref('')
const inviteTarget = ref(null)
const roleUpdatingUserId = ref(null)

// 初始化 - 加载团队信息和成员
onMounted(async () => {
  await loadTeamData()
})

// 加载团队数据
async function loadTeamData() {
  try {
    isLoading.value = true
    errorMessage.value = ''
    
    // 加载团队详情
    const teamResponse = await teamApi.getTeamDetail(teamId)
    Object.assign(teamInfo, {
      id: teamResponse.id,
      title: teamResponse.title,
      description: teamResponse.description,
      icon: teamResponse.icon || '🛡️',
      owner_id: teamResponse.owner_id,
      created_at: teamResponse.created_at,
      max_members: teamResponse.max_members,
    })

    const currentUserId = Number(localStorage.getItem('user_id'))
    
    // 加载团队成员
    const membersResponse = await teamApi.getTeamMembers(teamId)
    members.length = 0
    if (membersResponse.members && Array.isArray(membersResponse.members)) {
      members.push(...membersResponse.members.map((m) => ({
        ...m,
        id: m.id ?? m.user_id,
        user_nickname: m.user_nickname || m.nickname,
      })))
    }

    const me = members.find((m) => Number(m.user_id || m.id) === currentUserId)
    if (currentUserId && currentUserId === teamResponse.owner_id) {
      currentUserRole.value = 'owner'
    } else {
      currentUserRole.value = me?.role || 'member'
    }
  } catch (error) {
    errorMessage.value = error.message || '加载团队失败'
    console.error('加载团队数据错误:', error)
  } finally {
    isLoading.value = false
  }
}

function goBack() {
  router.back()
}

function startEdit() {
  editForm.title = teamInfo.title
  editForm.description = teamInfo.description
  editForm.icon = teamInfo.icon
  editForm.max_members = teamInfo.max_members
  isEditing.value = true
}

function cancelEdit() {
  isEditing.value = false
}

async function saveEdit() {
  if (!editForm.title.trim()) return
  
  try {
    const normalizedMaxMembers = Number(editForm.max_members)
    if (!Number.isFinite(normalizedMaxMembers) || normalizedMaxMembers < 2 || normalizedMaxMembers > 20) {
      errorMessage.value = '队伍人数上限必须在 2 到 20 之间'
      return
    }

    const data = {
      title: editForm.title,
      description: editForm.description,
      icon: editForm.icon,
      max_members: normalizedMaxMembers,
    }
    
    await teamApi.updateTeam(teamId, data)
    
    // 更新本地数据
    teamInfo.title = editForm.title
    teamInfo.description = editForm.description
    teamInfo.icon = editForm.icon
    teamInfo.max_members = normalizedMaxMembers
    isEditing.value = false
  } catch (error) {
    errorMessage.value = error.message || '保存失败'
    console.error('编辑团队错误:', error)
  }
}

async function removeMember(memberId) {
  if (!confirm('确定要移除这位成员吗?')) return
  
  try {
    await teamApi.removeTeamMember(teamId, memberId)
    
    // 从本地列表中移除
    const index = members.findIndex(m => (m.user_id || m.id) === memberId)
    if (index !== -1) {
      members.splice(index, 1)
    }
  } catch (error) {
    errorMessage.value = error.message || '移除成员失败'
    console.error('移除成员错误:', error)
  }
}

function openInviteModal() {
  showInviteModal.value = true
  inviteEmail.value = ''
  inviteError.value = ''
  inviteTarget.value = null
}

function closeInviteModal() {
  showInviteModal.value = false
  inviteEmail.value = ''
  inviteError.value = ''
  inviteTarget.value = null
}

async function sendInvitation() {
  if (!inviteEmail.value.trim()) {
    inviteError.value = '请输入要邀请的邮箱地址'
    return
  }
  
  try {
    inviteLoading.value = true
    inviteError.value = ''
    inviteTarget.value = null

    const email = inviteEmail.value.trim()
    if (!email.includes('@')) {
      inviteError.value = '请输入正确的邮箱地址'
      return
    }

    const target = await teamApi.searchUserByEmail(email)
    const targetUserId = Number(target.id)

    if (members.some((member) => Number(member.user_id || member.id) === targetUserId)) {
      inviteError.value = '该用户已在队伍中，无需重复邀请'
      return
    }

    inviteTarget.value = {
      id: targetUserId,
      nickname: target.nickname,
      email: target.email,
    }
    
    await teamApi.sendTeamInvitation(teamId, targetUserId)
    
    closeInviteModal()
    alert(`已向 ${target.nickname} 发送队伍邀请`) 
    router.push({
      name: 'contacts',
      query: {
        openFriendId: String(targetUserId),
      },
    })
  } catch (error) {
    inviteError.value = error.message || '邀请失败'
    console.error('发送邀请错误:', error)
  } finally {
    inviteLoading.value = false
  }
}

async function setMemberRole(member, targetRole) {
  const memberUserId = Number(member.user_id || member.id)
  if (!memberUserId || targetRole === member.role) {
    return
  }

  try {
    roleUpdatingUserId.value = memberUserId
    await teamApi.setTeamMemberRole(teamId, memberUserId, targetRole)
    member.role = targetRole
  } catch (error) {
    errorMessage.value = error.message || '设置成员角色失败'
  } finally {
    roleUpdatingUserId.value = null
  }
}

</script>

<template>
  <div class="management-page">
    <!-- Loading State -->
    <div v-if="isLoading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <!-- Error State -->
    <div v-if="errorMessage && !isLoading" class="error-message">
      ⚠️ {{ errorMessage }}
      <button @click="loadTeamData" class="retry-btn">重试</button>
    </div>

    <div v-if="!isLoading && !errorMessage" class="management-page-content">
      <div class="page-header">
        <button class="back-btn" @click="goBack">
          <span class="icon">←</span> 返回
        </button>
        <div class="header-title">
          <span class="team-icon-large">{{ teamInfo.icon }}</span>
          <h1>{{ teamInfo.title }} <span class="subtitle">管理面板</span></h1>
        </div>
      </div>

      <div class="content-grid">
        <!-- Team Info Card -->
        <div class="card info-card">
          <div class="card-header-row">
            <h3>基本信息</h3>
            <button v-if="!isEditing && currentUserRole === 'owner'" @click="startEdit" class="edit-btn">
              ✎ 编辑
            </button>
          </div>

          <!-- View Mode -->
          <div v-if="!isEditing" class="info-view">
            <div class="info-row">
              <span class="label">队伍名称</span>
              <span class="value main">{{ teamInfo.title }}</span>
            </div>
             <div class="info-row">
              <span class="label">队徽</span>
              <span class="value icon">{{ teamInfo.icon }}</span>
            </div>
            <div class="info-row">
              <span class="label">简介</span>
              <span class="value desc">{{ teamInfo.description || '暂无简介' }}</span>
            </div>
            <div class="info-row">
              <span class="label">创建时间</span>
              <span class="value">{{ new Date(teamInfo.created_at).toLocaleDateString('zh-CN') }}</span>
            </div>
            <div class="info-row">
              <span class="label">最多人数</span>
              <span class="value">{{ teamInfo.max_members }}</span>
            </div>
          </div>

          <!-- Edit Mode -->
          <div v-else class="info-edit">
            <div class="create-form">
              <!-- Icon Selector -->
              <div class="form-group">
                 <label>选择队徽</label>
                 <div class="icon-selector">
                  <div 
                    v-for="icon in availableIcons" 
                    :key="icon"
                    class="icon-option"
                    :class="{ active: editForm.icon === icon }"
                    @click="editForm.icon = icon"
                  >
                    {{ icon }}
                  </div>
                </div>
              </div>

              <div class="form-group">
                <label>队伍名称</label>
                <input v-model="editForm.title" maxlength="20" />
              </div>

              <div class="form-group">
                <label>简介</label>
                <textarea v-model="editForm.description" rows="3"></textarea>
              </div>

              <div class="form-group">
                <label>人数上限（2-20）</label>
                <input v-model.number="editForm.max_members" type="number" min="2" max="20" />
              </div>

              <div class="edit-actions">
                <button @click="cancelEdit" class="cancel-btn">取消</button>
                <button @click="saveEdit" class="save-btn">保存更改</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Members List -->
        <div class="card members-card">
          <div class="card-header-row">
            <h3>成员列表 <span class="count">({{ members.length }}/{{ teamInfo.max_members }})</span></h3>
            <button v-if="currentUserRole === 'owner' || currentUserRole === 'admin'" class="invite-btn" @click="openInviteModal">+ 邀请</button>
          </div>
          
          <div v-if="members.length === 0" class="no-members">
            暂无成员
          </div>

          <div v-else class="members-grid">
            <div v-for="member in members" :key="member.user_id || member.id" class="member-card">
              <div class="card-top-actions">
                 <button 
                  v-if="(currentUserRole === 'owner' || currentUserRole === 'admin') && member.role !== 'owner'"
                  class="remove-icon-btn" 
                  @click="removeMember(member.user_id || member.id)"
                  title="移除成员"
                >
                  ×
                </button>
              </div>

              <div class="avatar-circle-large">{{ member.user_nickname?.charAt(0) || '用户' }}</div>
              
              <div class="member-info">
                <span class="nickname">{{ member.user_nickname }}</span>
                <span class="role-badge" :class="member.role.toLowerCase()">
                  {{ member.role === 'owner' ? '队长' : (member.role === 'admin' ? '管理员' : '队员') }}
                </span>
                <span class="join-date">加入于 {{ new Date(member.joined_at).toLocaleDateString('zh-CN') }}</span>
              </div>

              <div v-if="currentUserRole === 'owner' && member.role !== 'owner'" class="member-role-actions">
                <button
                  class="member-role-btn"
                  :disabled="roleUpdatingUserId === (member.user_id || member.id) || member.role === 'admin'"
                  @click="setMemberRole(member, 'admin')"
                >
                  {{ roleUpdatingUserId === (member.user_id || member.id) ? '处理中...' : '设为管理员' }}
                </button>
                <button
                  class="member-role-btn secondary"
                  :disabled="roleUpdatingUserId === (member.user_id || member.id) || member.role === 'member'"
                  @click="setMemberRole(member, 'member')"
                >
                  {{ roleUpdatingUserId === (member.user_id || member.id) ? '处理中...' : '设为队员' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Invite Modal -->
      <Transition name="modal-fade">
        <div v-if="showInviteModal" class="modal-overlay" @click.self="closeInviteModal">
          <div class="modal-card">
            <div class="modal-header">
              <h3>邀请成员</h3>
              <button class="close-btn" @click="closeInviteModal">×</button>
            </div>
            
            <div class="modal-body">
              <p class="modal-desc">请输入要邀请用户的邮箱地址：</p>
              
              <div v-if="inviteError" class="error-message">
                ⚠️ {{ inviteError }}
              </div>
              
              <input 
                v-model="inviteEmail" 
                placeholder="例如：friend@example.com"
                class="invite-input"
              />

              <div v-if="inviteTarget" class="invite-target-preview">
                将邀请：{{ inviteTarget.nickname }}（{{ inviteTarget.email }}）
              </div>
            </div>
            
            <div class="modal-footer">
              <button class="cancel-btn" @click="closeInviteModal">取消</button>
              <button 
                class="confirm-btn" 
                :disabled="inviteLoading || !inviteEmail.trim()"
                @click="sendInvitation"
              >
                {{ inviteLoading ? '邀请中...' : '发送邀请' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
/* Page Layout */
.management-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 32px 24px;
}

.management-page-content {
  /* Content wrapper when not loading */
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
  margin-bottom: 12px;
  padding: 0;
  font-weight: 500;
}
.back-btn:hover { color: #475569; }

.header-title {
  display: flex;
  align-items: center;
  gap: 16px;
}

.team-icon-large {
  font-size: 36px;
  background: white;
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
}

.header-title h1 {
  margin: 0;
  font-size: 24px;
  color: #0f172a;
  display: flex;
  flex-direction: column;
}

.header-title .subtitle {
  font-size: 14px;
  color: #94a3b8;
  font-weight: 400;
  margin-top: 4px;
}

/* Cards Common */
.card {
  background: white;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
  overflow: hidden;
  margin-bottom: 24px;
}

.card-header-row {
  padding: 20px 24px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header-row h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.edit-btn {
  font-size: 13px;
  color: #4f46e5;
  background: #e0e7ff;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}
.edit-btn:hover { background: #c7d2fe; }

/* Info View Styles */
.info-view {
  padding: 24px;
  display: grid; /* Use grid for layout */
  gap: 20px;
}

.info-row {
  display: flex;
  align-items: flex-start; /* Align smoothly */
}

.label {
  width: 100px;
  font-size: 13px;
  color: #64748b;
  flex-shrink: 0;
  padding-top: 2px; /* Visual adjustment */
}

.value {
  font-size: 14px;
  color: #334155;
  font-weight: 500;
}

.value.main {
  font-size: 16px;
  color: #0f172a;
  font-weight: 600;
}

.value.desc {
  color: #475569;
  line-height: 1.5;
}

.value.icon {
  font-size: 24px;
}

.tags-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tag-badge {
  font-size: 12px;
  background: #f1f5f9;
  color: #475569;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
}

/* Edit Form Styles */
.info-edit {
  padding: 24px;
  background: #f8fafc;
}

.create-form .form-group {
  margin-bottom: 16px;
}

.create-form label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 8px;
}

.create-form input,
.create-form textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
}

/* Icon Selector Reuse */
.icon-selector {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.icon-option {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  cursor: pointer;
  background: white;
  border: 1px solid #e2e8f0;
  font-size: 18px;
}

.icon-option:hover, .icon-option.active {
  background: #e0e7ff;
  border-color: #6366f1;
}

.tags-input-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 6px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: white;
}

.tag-chip {
  background: #f1f5f9;
  font-size: 13px;
  padding: 2px 8px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.tag-input {
  border: none !important;
  padding: 4px !important;
  flex: 1;
  min-width: 80px;
}
.tag-input:focus { outline: none; }

.edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.save-btn {
  background: #4f46e5;
  color: white;
  border: none;
  padding: 8px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.cancel-btn {
  background: white;
  border: 1px solid #cbd5e1;
  padding: 8px 16px;
  border-radius: 6px;
  color: #475569;
  cursor: pointer;
}

/* Members Grid */
.members-grid {
  padding: 24px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 20px;
}

.member-card {
  background: white;
  border: 1px solid #f1f5f9;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  transition: all 0.2s ease-in-out;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.member-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  border-color: #cbd5e1;
}

.card-top-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 24px;
  height: 24px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.remove-icon-btn {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: #cbd5e1;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  padding: 0;
  line-height: normal;
}

.member-card:hover .remove-icon-btn {
  color: #94a3b8;
}

.remove-icon-btn:hover {
  background: #fef2f2;
  color: #ef4444 !important;
}

.avatar-circle-large {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
  color: #0369a1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 28px;
  margin-bottom: 12px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.member-info {
  text-align: center;
  width: 100%;
  margin-bottom: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.nickname {
  font-weight: 600;
  color: #1e293b;
  font-size: 15px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.role-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  text-transform: uppercase;
  font-weight: 700;
  display: inline-block;
}
.role-badge.owner { background: #e0e7ff; color: #4338ca; }
.role-badge.admin { background: #dcfce7; color: #15803d; }
.role-badge.member { background: #f1f5f9; color: #64748b; }

.join-date {
  font-size: 11px;
  color: #94a3b8;
  margin-top: 2px;
}

.member-role-actions {
  width: 100%;
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.member-role-btn {
  flex: 1;
  border: none;
  border-radius: 8px;
  background: #4f46e5;
  color: #ffffff;
  font-size: 12px;
  font-weight: 600;
  padding: 7px 8px;
  cursor: pointer;
}

.member-role-btn.secondary {
  background: #e2e8f0;
  color: #334155;
}

.member-role-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.member-controls-card {
  width: 100%;
  margin-top: auto;
  border-top: 1px solid #f1f5f9;
  padding-top: 12px;
}

.role-select {
  width: 100%;
  padding: 6px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  font-size: 12px;
  color: #475569;
  background: #f8fafc;
  cursor: pointer;
  text-align: center;
}
.role-select:focus { outline: none; border-color: #6366f1; }

.invite-btn {
  font-size: 13px;
  color: #4f46e5;
  background: white;
  border: 1px solid #e0e7ff;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}
.invite-btn:hover { background: #eef2ff; border-color: #c7d2fe; }

.no-members {
  text-align: center;
  color: #94a3b8;
  padding: 48px 24px;
  font-size: 14px;
}

/* Modal Styles */
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
  z-index: 2000;
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  width: 90%;
  max-width: 400px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 16px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  color: #94a3b8;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.close-btn:hover {
  color: #64748b;
}

.modal-body {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
}

.modal-desc {
  margin: 0 0 16px 0;
  font-size: 13px;
  color: #475569;
}

.invite-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.2s;
}

.invite-input:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.invite-target-preview {
  margin-top: 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #f8fafc;
  color: #334155;
  font-size: 13px;
  padding: 10px 12px;
}

.modal-footer {
  padding: 12px 16px;
  background: #f8fafc;
  border-top: 1px solid #f1f5f9;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.confirm-btn {
  padding: 8px 16px;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.confirm-btn:hover:not(:disabled) {
  background: #4338ca;
}

.confirm-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
  opacity: 0.6;
}

@media (max-width: 768px) {
  .management-page {
    padding: 16px 12px;
  }

  .header-title {
    align-items: flex-start;
    gap: 10px;
  }

  .team-icon-large {
    width: 52px;
    height: 52px;
    font-size: 28px;
  }

  .header-title h1 {
    font-size: 20px;
  }

  .card-header-row {
    padding: 14px 12px;
    flex-wrap: wrap;
    row-gap: 8px;
  }

  .info-view,
  .info-edit,
  .members-grid {
    padding: 12px;
  }

  .members-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .member-role-actions {
    flex-direction: column;
  }

  .modal-card {
    width: calc(100% - 20px);
    max-height: calc(100vh - 24px);
  }

  .modal-body {
    padding: 14px;
  }

  .modal-footer {
    flex-direction: column;
  }

  .cancel-btn,
  .confirm-btn {
    width: 100%;
  }
}
</style>
