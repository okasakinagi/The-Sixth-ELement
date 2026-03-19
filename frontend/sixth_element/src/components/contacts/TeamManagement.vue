
<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const teamId = route.params.teamId

// Mock Data - In reality, fetch based on teamId
const teamInfo = reactive({
  id: teamId,
  name: 'Alpha Squad',
  description: '专注于高回报问卷的小队。',
  icon: '🛡️',
  ownerId: 101,
  createdAt: '2023-10-01'
})

// Editing State
const isEditing = ref(false)
const editForm = reactive({
  name: '',
  description: '',
  icon: ''
})

// Predefined icons for selection
const availableIcons = ['🚀', '🛡️', '⚔️', '💎', '🎮', '📚', '💼', '🎨', '🦁', '⚡']

const members = reactive([
  { id: 101, nickname: '我', role: 'Member', avatar: 'M', joinedAt: '2023-10-01' },
  { id: 2, nickname: 'Captain Alice', role: 'Owner', avatar: 'A', joinedAt: '2023-10-02' },
  { id: 3, nickname: 'Bob', role: 'Member', avatar: 'B', joinedAt: '2023-10-05' },
])

const currentUserRole = ref('Member') // Mock current user is member

function goBack() {
  router.back()
}

function startEdit() {
  editForm.name = teamInfo.name
  editForm.description = teamInfo.description
  editForm.icon = teamInfo.icon
  isEditing.value = true
}

function cancelEdit() {
  isEditing.value = false
}

function saveEdit() {
  if (!editForm.name.trim()) return
  
  teamInfo.name = editForm.name
  teamInfo.description = editForm.description
  teamInfo.icon = editForm.icon
  isEditing.value = false
}

function removeMember(memberId) {
  if (confirm('确定要移除这位成员吗?')) {
    const index = members.findIndex(m => m.id === memberId)
    if (index !== -1) {
      members.splice(index, 1)
    }
  }
}

function inviteMember() {
  alert('邀请功能即将上线！您目前可以从联系人页面添加好友。')
}
</script>

<template>
  <div class="management-page">
    <div class="page-header">
      <button class="back-btn" @click="goBack">
        <span class="icon">←</span> 返回
      </button>
      <div class="header-title">
        <span class="team-icon-large">{{ teamInfo.icon }}</span>
        <h1>{{ teamInfo.name }} <span class="subtitle">管理面板</span></h1>
      </div>
    </div>

    <div class="content-grid">
      <!-- Team Info Card -->
      <div class="card info-card">
        <div class="card-header-row">
          <h3>基本信息</h3>
          <button v-if="!isEditing && currentUserRole === 'Owner'" @click="startEdit" class="edit-btn">
            ✎ 编辑
          </button>
        </div>

        <!-- View Mode -->
        <div v-if="!isEditing" class="info-view">
          <div class="info-row">
            <span class="label">队伍名称</span>
            <span class="value main">{{ teamInfo.name }}</span>
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
            <span class="value">{{ teamInfo.createdAt }}</span>
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
              <input v-model="editForm.name" maxlength="20" />
            </div>

            <div class="form-group">
              <label>简介</label>
              <textarea v-model="editForm.description" rows="3"></textarea>
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
          <h3>成员列表 <span class="count">({{ members.length }})</span></h3>
          <button class="invite-btn" @click="inviteMember">+ 邀请</button>
        </div>
        
        <div class="members-grid">
          <div v-for="member in members" :key="member.id" class="member-card">
            <div class="card-top-actions">
               <button 
                v-if="(currentUserRole === 'Owner' || currentUserRole === 'Admin') && member.role !== 'Owner'"
                class="remove-icon-btn" 
                @click="removeMember(member.id)"
                title="移除成员"
              >
                ×
              </button>
            </div>

            <div class="avatar-circle-large">{{ member.avatar }}</div>
            
            <div class="member-info">
              <span class="nickname">{{ member.nickname }}</span>
              <span class="role-badge" :class="member.role.toLowerCase()">
                {{ member.role === 'Owner' ? '队长' : (member.role === 'Admin' ? '管理员' : '队员') }}
              </span>
              <span class="join-date">加入于 {{ member.joinedAt }}</span>
            </div>

            <div class="member-controls-card" v-if="currentUserRole === 'Owner' && member.role !== 'Owner'">
              <select 
                v-model="member.role"
                class="role-select"
              >
                <option value="Admin">管理员</option>
                <option value="Member">队员</option>
              </select>
            </div>
          </div>
        </div>
      </div>
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
</style>
