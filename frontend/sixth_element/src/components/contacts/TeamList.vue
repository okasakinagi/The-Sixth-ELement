
<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import * as teamApi from '@/utils/teamApi'

const router = useRouter()
const showCreateModal = ref(false)
const isLoading = ref(true)
const errorMessage = ref('')

// Form State
const startAnimation = ref(false)
const newTeamName = ref('')
const newTeamDescription = ref('')
const newTeamIcon = ref('🚀') // Default icon
const newTeamMaxMembers = ref(8)

// Predefined icons for selection
const availableIcons = ['🚀', '🛡️', '⚔️', '💎', '🎮', '📚', '💼', '🎨', '🦁', '⚡']

// Single team state loaded from API
const myTeam = ref(null)

// Members data for preview
const teamMembers = reactive([])

const canCreate = computed(() => {
  return newTeamName.value.trim().length > 0 && newTeamName.value.length <= 20
})

const isOwner = computed(() => {
  if (!myTeam.value) return false
  const currentUserId = Number(localStorage.getItem('user_id'))
  return myTeam.value.role === 'owner' || (currentUserId && currentUserId === myTeam.value.owner_id)
})
const isAdmin = computed(() => myTeam.value && (myTeam.value.role === 'admin' || myTeam.value.role === 'owner'))

// 加载我的团队信息
async function loadMyTeam() {
  try {
    isLoading.value = true
    errorMessage.value = ''
    const result = await teamApi.getMyTeam()
    
    // Phase 2: getMyTeam返回单个团队（或null）
    if (result.team) {
      myTeam.value = {
        ...result.team,
        role: result.my_role || 'member',
      }
      
      // 加载团队成员
      teamMembers.length = 0
      if (result.members && Array.isArray(result.members)) {
        teamMembers.push(...result.members)
      }
    } else {
      myTeam.value = null
      teamMembers.length = 0
    }
  } catch (error) {
    errorMessage.value = error.message || '加载团队失败'
    myTeam.value = null
    teamMembers.length = 0
  } finally {
    isLoading.value = false
  }
}

function handleTeamUpdated() {
  loadMyTeam()
}

// 初始化时加载数据
onMounted(() => {
  loadMyTeam()
  window.addEventListener('team:updated', handleTeamUpdated)
})

onBeforeUnmount(() => {
  window.removeEventListener('team:updated', handleTeamUpdated)
})

function openCreateModal() {
  showCreateModal.value = true
  setTimeout(() => { startAnimation.value = true }, 50)
  // Reset form
  newTeamName.value = ''
  newTeamDescription.value = ''
  newTeamIcon.value = availableIcons[Math.floor(Math.random() * availableIcons.length)]
  newTeamMaxMembers.value = 8
}

function closeCreateModal() {
  startAnimation.value = false
  setTimeout(() => { showCreateModal.value = false }, 300)
}

async function createTeam() {
  if (!canCreate.value) return
  
  try {
    const normalizedMaxMembers = Math.max(2, Math.min(20, Number(newTeamMaxMembers.value) || 8))
    const data = {
      title: newTeamName.value,
      description: newTeamDescription.value,
      icon: newTeamIcon.value,
      max_members: normalizedMaxMembers
    }
    
    const result = await teamApi.createTeam(data)
    
    // 更新本地UI
    myTeam.value = {
      id: result.id,
      title: result.title,
      description: result.description,
      icon: result.icon || newTeamIcon.value,
      role: 'owner',
      members_count: 1,
      max_members: result.max_members || normalizedMaxMembers,
      created_at: result.created_at
    }
    const currentUserId = Number(localStorage.getItem('user_id'))
    const currentNickname = localStorage.getItem('user_nickname') || '我'
    teamMembers.length = 0
    teamMembers.push({
      id: currentUserId || Date.now(),
      user_id: currentUserId || null,
      user_nickname: currentNickname,
      nickname: currentNickname,
      role: 'owner',
      status: 'joined',
      joined_at: result.created_at,
    })
    
    closeCreateModal()
    
    // 可选：显示成功提示
    console.log('团队创建成功:', myTeam.value.title)
  } catch (error) {
    errorMessage.value = error.message || '创建团队失败'
    console.error('创建团队错误:', error)
  }
}

function manageTeam() {
  if (myTeam.value) {
    router.push({ name: 'team-manage', params: { teamId: myTeam.value.id } })
  }
}

async function handleLeaveOrDisband() {
  if (!myTeam.value) return
  
  const confirmMsg = isOwner.value 
    ? '确定要【解散】队伍吗？此操作不可逆，队伍所有数据将被清除。'
    : '确定要退出队伍吗？'
  
  if (!confirm(confirmMsg)) return
  
  try {
    if (isOwner.value) {
      // 队长删除队伍
      await teamApi.deleteTeam(myTeam.value.id)
    } else {
      // 普通成员退出队伍
      await teamApi.removeTeamMember(myTeam.value.id, Number(getCurrentUserId()))
    }
    
    myTeam.value = null
    teamMembers.length = 0
    errorMessage.value = ''
    window.dispatchEvent(new CustomEvent('team:updated'))
  } catch (error) {
    errorMessage.value = error.message || (isOwner.value ? '解散队伍失败' : '退出队伍失败')
    console.error('队伍操作错误:', error)
  }
}

// 获取当前用户ID（从localStorage）
function getCurrentUserId() {
  return localStorage.getItem('user_id') || ''
}
</script>

<template>
  <div class="team-section">
    <div class="header">
      <h2>我的队伍</h2>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <!-- Error State -->
    <div v-if="errorMessage && !isLoading" class="error-message">
      ⚠️ {{ errorMessage }}
      <button @click="loadMyTeam" class="retry-btn">重试</button>
    </div>

    <!-- Empty State: Enhanced Dashed Box -->
    <div v-if="!myTeam && !isLoading && !errorMessage" class="empty-team-state" @click="openCreateModal">
      <div class="empty-content">
        <div class="empty-illustration">
          <div class="circle-bg"></div>
          <span class="main-icon">👥</span>
          <span class="plus-icon">+</span>
        </div>
        <h3>您还没有加入任何队伍</h3>
        <p>创建一个新队伍来协作完成问卷，或等待好友邀请。</p>
        <button class="create-link">
          <span class="btn-icon">✨</span> 创建新队伍
        </button>
      </div>
    </div>

    <!-- Single Team Card -->
    <div v-else-if="myTeam && !isLoading" class="team-card single-view">
      <div class="card-content">
        <div class="card-header">
          <div class="team-identity">
            <div class="team-avatar">{{ myTeam.icon || '🛡️' }}</div>
            <div>
              <div class="name-row">
                <h3 class="team-name">{{ myTeam.title }}</h3>
                <span class="role-badge" :class="myTeam.role.toLowerCase()">
                  {{ myTeam.role === 'owner' ? '队长' : (myTeam.role === 'admin' ? '管理员' : '队员') }}
                </span>
              </div>
            </div>
          </div>
          
          <div class="top-actions">
             <button class="manage-icon-btn" @click="manageTeam" title="队伍详情">
               ⚙️
             </button>
          </div>
        </div>
        
        <div class="stats-grid">
          <div class="stat-item">
            <span class="val">{{ teamMembers.length }}</span>
            <span class="lbl">成员</span>
          </div>
          <div class="stat-item">
            <span class="val">{{ myTeam.max_members }}</span>
            <span class="lbl">最多人数</span>
          </div>
        </div>

        <div class="points-notice">
          <span class="icon">📈</span>
          队员加入后，其后续填写问卷获得的积分会计入队长的账户中。
        </div>

        <!-- Inline Members Display -->
        <div class="members-preview-section">
          <h4>队伍成员</h4>
          <div class="members-grid-mini">
            <div v-if="teamMembers.length === 0" class="no-members">
              暂无成员
            </div>
            <div v-for="member in teamMembers" :key="member.user_id || member.id" class="member-card-mini">
              <div class="avatar-mini">{{ (member.user_nickname || member.nickname)?.charAt(0) || '用户' }}</div>
              <div class="info-mini">
                  <span class="name">{{ member.user_nickname || member.nickname }}</span>
                  <span class="role-badge-mini" :class="member.role.toLowerCase()">
                    {{ member.role === 'owner' ? '队长' : (member.role === 'admin' ? '管理' : '队员') }}
                  </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="card-actions">
        <!-- Members just see the list above, no button needed -->
        
        <button 
          class="action-btn leave" 
          :class="{ 'danger': isOwner }"
          @click="handleLeaveOrDisband" 
          :title="isOwner ? '解散队伍' : '退出队伍'"
        >
          <span class="icon">{{ isOwner ? '❌' : '🚪' }}</span>
          <span class="label">{{ isOwner ? '解散' : '退出' }}</span>
        </button>
      </div>
    </div>

    <!-- Enhanced Create Team Modal -->
    <Transition name="modal-fade">
      <div v-if="showCreateModal" class="modal-overlay" @click.self="closeCreateModal">
        <div class="modal-card" :class="{ 'show': startAnimation }">
          <div class="modal-header">
            <h3>创建新队伍</h3>
            <button class="close-btn" @click="closeCreateModal">×</button>
          </div>
          
          <div class="modal-body">
            <!-- Icon Selection -->
            <div class="form-section icon-section">
              <label>选择队徽</label>
              <div class="icon-selector">
                <div 
                  v-for="icon in availableIcons" 
                  :key="icon"
                  class="icon-option"
                  :class="{ active: newTeamIcon === icon }"
                  @click="newTeamIcon = icon"
                >
                  {{ icon }}
                </div>
              </div>
            </div>

            <!-- Team Name -->
            <div class="form-group">
              <label>队伍名称 <span class="required">*</span></label>
              <div class="input-wrapper">
                <div class="prefix-icon">{{ newTeamIcon }}</div>
                <input 
                  v-model="newTeamName" 
                  placeholder="给队伍起个响亮的名字 (2-20字)" 
                  maxlength="20"
                  autofocus
                />
              </div>
              <span class="char-count">{{ newTeamName.length }}/20</span>
            </div>

            <!-- Description -->
            <div class="form-group">
              <label>简介 (可选)</label>
              <textarea 
                v-model="newTeamDescription" 
                placeholder="简单描述一下队伍的目标..."
                rows="3"
              ></textarea>
            </div>

            <div class="form-group">
              <label>人数上限 (2-20)</label>
              <input
                v-model.number="newTeamMaxMembers"
                type="number"
                min="2"
                max="20"
                placeholder="默认 8"
              />
            </div>
          </div>

          <div class="modal-footer">
            <button class="cancel-btn" @click="closeCreateModal">取消</button>
            <button 
              class="confirm-btn" 
              :disabled="!canCreate"
              @click="createTeam"
            >
              立即创建
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
/* Main Layout */
.team-section {
  padding: 24px;
  max-width: 800px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header h2 {
  font-size: 20px;
  color: #1e293b;
  margin: 0;
  font-weight: 700;
}

.invitations-link {
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #fde68a;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.invitations-link:hover {
  background: #fcd34d;
  border-color: #f59e0b;
}

.invitations-link .badge {
  background: #f59e0b;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 700;
}

/* Empty State Enhanced */
.empty-team-state {
  border: 2px dashed #cbd5e1;
  border-radius: 16px;
  padding: 48px 24px;
  text-align: center;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.empty-team-state:hover {
  border-color: #6366f1;
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.empty-illustration {
  position: relative;
  width: 80px;
  height: 80px;
  margin: 0 auto 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.circle-bg {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: #e0e7ff;
  opacity: 0.5;
  transition: all 0.3s;
}

.empty-team-state:hover .circle-bg {
  transform: scale(1.1);
  background: #c7d2fe;
}

.main-icon {
  font-size: 40px;
  z-index: 2;
}

.plus-icon {
  position: absolute;
  top: 0;
  right: 0;
  background: #4f46e5;
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: bold;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  z-index: 3;
}

.empty-content h3 {
  color: #1e293b;
  font-size: 18px;
  margin-bottom: 8px;
  font-weight: 600;
}

.empty-content p {
  color: #64748b;
  margin-bottom: 24px;
  font-size: 14px;
}

.create-link {
  background: #4f46e5;
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: 20px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.create-link:hover {
  background: #4338ca;
  box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2);
}

/* Team Card Enhanced */
.team-card.single-view {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  flex-direction: column; /* Changed to column to stack inline projects */
  gap: 20px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  transition: all 0.2s;
}

.card-content {
    /* Allow it to take full width */
    width: 100%;
}

.team-card:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}

.team-identity {
  display: flex;
  align-items: center;
  gap: 16px;
}

.team-avatar {
  min-width: 56px;
  height: 56px;
  background: #f1f5f9;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.team-name {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
}

.role-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
  text-transform: uppercase;
}
.role-badge.owner { background: #e0e7ff; color: #4f46e5; }
.role-badge.admin { background: #dcfce7; color: #166534; }
.role-badge.member { background: #f1f5f9; color: #64748b; }

.manage-icon-btn {
    background: transparent;
    border: none;
    font-size: 18px;
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    transition: background 0.2s;
}
.manage-icon-btn:hover { background: #f1f5f9; }

.stats-grid {
  display: flex;
  gap: 24px;
  margin-top: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-item .val {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
}

.stat-item .lbl {
  font-size: 11px;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.points-notice {
  margin-top: 16px;
  padding: 8px 12px;
  background: #f0f9ff;
  border-radius: 8px;
  font-size: 12px;
  color: #0369a1;
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #bae6fd;
}

.points-notice .icon {
  font-size: 14px;
}

/* Inline Members Grid */
.members-preview-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #f1f5f9;
}

.members-preview-section h4 {
  font-size: 14px;
  margin: 0 0 16px 0;
  color: #1e293b;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}
.members-preview-section h4::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #f1f5f9;
}

.members-grid-mini {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 12px;
}

.member-card-mini {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
  transition: all 0.2s;
  box-shadow: 0 1px 2px 0 rgba(0,0,0,0.02);
}

.member-card-mini:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    border-color: #cbd5e1;
}

.avatar-mini {
  width: 42px;
  height: 42px;
  background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
  color: #0369a1;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 600;
}

.info-mini {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
}

.info-mini .name {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.role-badge-mini {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  align-self: center;
  font-weight: 700;
  text-transform: uppercase;
}
.role-badge-mini.owner { background: #e0e7ff; color: #4338ca; }
.role-badge-mini.admin { background: #dcfce7; color: #15803d; }
.role-badge-mini.member { background: #f1f5f9; color: #64748b; }

.card-actions {
  display: flex;
  gap: 10px;
  border-top: 1px solid #f1f5f9;
  padding-top: 16px;
  justify-content: flex-end;
  width: 100%;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid transparent;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn.primary {
  background: white;
  border-color: #cbd5e1;
  color: #475569;
}
.action-btn.primary:hover { border-color: #6366f1; color: #6366f1; background: #f8fafc; }

.action-btn.leave {
  padding: 8px 12px;
  background: transparent;
  color: #94a3b8;
  border: 1px solid transparent;
}
.action-btn.leave:hover { color: #f59e0b; background: #fffbeb; }

.action-btn.leave.danger {
  color: #ef4444;
}
.action-btn.leave.danger:hover {
  background: #fef2f2;
  border-color: #fca5a5;
}

.action-btn.leave .label {
  font-size: 12px;
  margin-left: 4px;
}

/* Modal & Form Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-card {
  background: white;
  width: 100%;
  max-width: 480px;
  border-radius: 16px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  opacity: 0;
  transform: scale(0.95);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.modal-card.show {
  opacity: 1;
  transform: scale(1);
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  line-height: 1;
  color: #94a3b8;
  cursor: pointer;
  padding: 0;
}
.close-btn:hover { color: #64748b; }

.modal-body {
  padding: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 8px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.prefix-icon {
  position: absolute;
  left: 12px;
  font-size: 18px;
  pointer-events: none;
}

input, textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.2s;
}

.input-wrapper input {
  padding-left: 40px;
}

input:focus, textarea:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.char-count {
  font-size: 11px;
  color: #94a3b8;
  float: right;
  margin-top: 4px;
}

.icon-selector {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
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
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  font-size: 18px;
  transition: all 0.2s;
}

.icon-option:hover, .icon-option.active {
  background: #e0e7ff;
  border-color: #6366f1;
  transform: scale(1.1);
}

.modal-footer {
  padding: 16px 24px;
  background: #f8fafc;
  border-top: 1px solid #f1f5f9;
  border-bottom-left-radius: 16px;
  border-bottom-right-radius: 16px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.cancel-btn {
  padding: 8px 16px;
  background: white;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  color: #475569;
  font-weight: 500;
  cursor: pointer;
}
.cancel-btn:hover { background: #f1f5f9; }

.confirm-btn {
  padding: 8px 24px;
  background: #4f46e5;
  border: none;
  border-radius: 6px;
  color: white;
  font-weight: 500;
  cursor: pointer;
}
.confirm-btn:hover { background: #4338ca; }
.confirm-btn:disabled { background: #cbd5e1; cursor: not-allowed; }

/* Transitions */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
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

/* No Members State */
.no-members {
  color: #94a3b8;
  font-size: 13px;
  padding: 24px;
  text-align: center;
  grid-column: 1 / -1;
}

@media (max-width: 768px) {
  .team-section {
    padding: 16px 12px;
  }

  .team-card.single-view {
    padding: 14px;
    gap: 14px;
  }

  .card-header {
    gap: 10px;
  }

  .team-identity {
    gap: 10px;
  }

  .team-avatar {
    min-width: 44px;
    height: 44px;
    font-size: 22px;
  }

  .team-name {
    font-size: 17px;
  }

  .name-row {
    flex-wrap: wrap;
  }

  .stats-grid {
    gap: 14px;
  }

  .members-grid-mini {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .card-actions {
    justify-content: stretch;
  }

  .action-btn.leave {
    width: 100%;
    justify-content: center;
  }

  .modal-card {
    width: calc(100% - 16px);
    max-height: calc(100vh - 16px);
    overflow-y: auto;
  }

  .modal-body,
  .modal-header,
  .modal-footer {
    padding-left: 14px;
    padding-right: 14px;
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
