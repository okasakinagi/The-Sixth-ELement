<template>
  <div class="profile-container">
    <!-- 个人主页头部 -->
    <div class="profile-header">
      <div class="header-bg"></div>
      <div class="header-content">
        <div class="avatar-section">
          <div class="avatar">
            <span class="avatar-text">{{ userInitial }}</span>
          </div>
          <div class="user-basic-info">
            <h1 class="username">{{ userData.name || '未设置姓名' }}</h1>
            <p class="user-subtitle">{{ userData.college || '未设置学院' }} · {{ userData.major || '未设置专业' }}</p>
            <div class="status-row">
              <div
                class="status-pill"
                :class="{ empty: !userData.currentStatus }"
                @click="startStatusEdit"
              >
                <span class="status-dot"></span>
                <span class="status-text">{{ userData.currentStatus || '添加状态' }}</span>
                <span class="status-edit">✏️</span>
              </div>
              <div v-if="isEditingStatus" class="status-editor">
                <input
                  v-model="statusInput"
                  type="text"
                  class="status-input"
                  placeholder="例如：正在备战期末、度假中、找实习"
                  @keyup.enter="saveStatus"
                />
                <div class="status-actions">
                  <button class="status-save" @click="saveStatus">保存</button>
                  <button class="status-cancel" @click="cancelStatus">取消</button>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="header-actions">
          <button class="ghost-button" @click="goToTaskHall">
            返回任务大厅
          </button>
          <button class="edit-button" @click="goToEdit">
            <span class="edit-icon">✏️</span>
            编辑资料
          </button>
        </div>
      </div>
    </div>

    <!-- 个人信息卡片区域 -->
    <div class="profile-content">
      <!-- 基本信息卡片 -->
      <div class="info-card">
        <div class="card-header">
          <h3 class="card-title">
            <span class="card-icon">👤</span>
            基本信息
          </h3>
        </div>
        <div class="card-body">
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">性别</span>
              <span class="info-value">{{ userData.gender || '未设置' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">年龄</span>
              <span class="info-value">{{ userData.age ? userData.age + ' 岁' : '未设置' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">年级</span>
              <span class="info-value">{{ userData.grade || '未设置' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">MBTI</span>
              <span class="info-value" :class="{ 'highlight': userData.mbti }">
                {{ userData.mbti || '未测试' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 兴趣与特长卡片 -->
      <div class="info-card">
        <div class="card-header">
          <h3 class="card-title">
            <span class="card-icon">✨</span>
            兴趣与特长
          </h3>
        </div>
        <div class="card-body">
          <!-- 研究方向 -->
          <div class="detail-section" v-if="userData.interests">
            <div class="detail-label">
              <span class="label-icon">🔬</span>
              研究方向 / 兴趣课程
            </div>
            <div class="detail-content">{{ userData.interests }}</div>
          </div>

          <!-- 社团经历 -->
          <div class="detail-section" v-if="userData.organizations">
            <div class="detail-label">
              <span class="label-icon">🎭</span>
              社团 / 组织经历
            </div>
            <div class="detail-content">{{ userData.organizations }}</div>
          </div>

          <!-- 技能标签 -->
          <div class="detail-section" v-if="userData.skills && userData.skills.length > 0">
            <div class="detail-label">
              <span class="label-icon">🛠️</span>
              软硬技能
            </div>
            <div class="tag-list">
              <span class="tag skill-tag" v-for="skill in userData.skills" :key="skill">
                {{ skill }}
              </span>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-if="!userData.interests && !userData.organizations && (!userData.skills || userData.skills.length === 0)" class="empty-state">
            <p>还没有填写兴趣与特长信息</p>
            <button class="link-button" @click="goToEdit">去完善 →</button>
          </div>
        </div>
      </div>

      <!-- 消费与职业卡片 -->
      <div class="info-card">
        <div class="card-header">
          <h3 class="card-title">
            <span class="card-icon">🎯</span>
            偏好与规划
          </h3>
        </div>
        <div class="card-body">
          <!-- 消费偏好 -->
          <div class="detail-section" v-if="userData.consumptionPreferences && userData.consumptionPreferences.length > 0">
            <div class="detail-label">
              <span class="label-icon">🛍️</span>
              消费偏好
            </div>
            <div class="tag-list">
              <span class="tag consumption-tag" v-for="tag in userData.consumptionPreferences" :key="tag">
                {{ tag }}
              </span>
            </div>
          </div>

          <!-- 职业意向 -->
          <div class="detail-section" v-if="userData.careerIntention && userData.careerIntention.length > 0">
            <div class="detail-label">
              <span class="label-icon">💼</span>
              职业意向
            </div>
            <div class="tag-list">
              <span class="tag career-tag" v-for="tag in userData.careerIntention" :key="tag">
                {{ tag }}
              </span>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-if="(!userData.consumptionPreferences || userData.consumptionPreferences.length === 0) && (!userData.careerIntention || userData.careerIntention.length === 0)" class="empty-state">
            <p>还没有填写偏好与规划信息</p>
            <button class="link-button" @click="goToEdit">去完善 →</button>
          </div>
        </div>
      </div>

    </div>

    <!-- 悬浮画像完成度 -->
    <div class="floating-progress" :class="{ mobile: isMobile }">
      <div class="floating-header">
        <span class="floating-title">画像完成度</span>
        <button class="floating-action" @click="goToEdit">去完善</button>
      </div>
      <div class="floating-body">
        <div class="circular-progress small">
          <svg class="progress-ring" width="84" height="84">
            <circle
              class="progress-ring-circle-bg"
              stroke="#e3f2fd"
              stroke-width="8"
              fill="transparent"
              r="34"
              cx="42"
              cy="42"
            />
            <circle
              class="progress-ring-circle"
              stroke="url(#gradient-floating)"
              stroke-width="8"
              fill="transparent"
              r="34"
              cx="42"
              cy="42"
              :stroke-dasharray="floatingCircumference"
              :stroke-dashoffset="floatingOffset"
            />
            <defs>
              <linearGradient id="gradient-floating" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#42a5f5;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#1976d2;stop-opacity:1" />
              </linearGradient>
            </defs>
          </svg>
          <div class="progress-text small">
            <span class="progress-number">{{ completionRate }}%</span>
          </div>
        </div>
        <div class="floating-info">
          <p class="floating-sub">完善度越高，推荐越精准</p>
          <p class="floating-tip">{{ completionMessage }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const STORAGE_KEY = 'sixth_element_profile'
const defaultProfile = {
  name: '未设置姓名',
  gender: '',
  age: null,
  grade: '',
  college: '',
  major: '',
  mbti: '',
  interests: '',
  organizations: '',
  consumptionPreferences: [],
  careerIntention: [],
  skills: [],
  currentStatus: ''
}

const sampleProfile = {
  name: '张三',
  gender: '男',
  age: 20,
  grade: '大二',
  college: '计算机科学学院',
  major: '计算机科学与技术',
  mbti: 'INTJ',
  interests: '人工智能、机器学习、深度学习',
  organizations: '校学生会技术部、ACM竞赛队',
  consumptionPreferences: ['数码', '阅读', '游戏'],
  careerIntention: ['大厂', '考研'],
  skills: ['Python', 'Java', 'C++', '算法'],
  currentStatus: '正在准备期末考试，同时学习 Vue 3'
}

const userData = ref({ ...defaultProfile, ...sampleProfile })
const statusInput = ref('')
const isEditingStatus = ref(false)
const isMobile = ref(window.innerWidth <= 768)

const handleResize = () => {
  isMobile.value = window.innerWidth <= 768
}

const persistProfile = () => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(userData.value))
}

const loadProfile = () => {
  const cached = localStorage.getItem(STORAGE_KEY)
  if (cached) {
    try {
      const parsed = JSON.parse(cached)
      userData.value = { ...defaultProfile, ...sampleProfile, ...parsed }
    } catch (error) {
      console.warn('Failed to parse cached profile, fallback to defaults')
      userData.value = { ...defaultProfile, ...sampleProfile }
    }
  }
}

onMounted(() => {
  loadProfile()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})

// 计算用户名首字母
const userInitial = computed(() => {
  return userData.value.name ? userData.value.name.charAt(0).toUpperCase() : '?'
})

// 计算完成度
const completionRate = computed(() => {
  const fields = [
    userData.value.gender,
    userData.value.age,
    userData.value.grade,
    userData.value.college,
    userData.value.major,
    userData.value.mbti,
    userData.value.interests,
    userData.value.organizations,
    userData.value.consumptionPreferences?.length > 0,
    userData.value.careerIntention?.length > 0,
    userData.value.skills?.length > 0,
    userData.value.currentStatus
  ]
  
  const filledCount = fields.filter(field => field).length
  return Math.round((filledCount / fields.length) * 100)
})

// 完成度提示信息
const completionMessage = computed(() => {
  if (completionRate.value >= 80) return '画像非常完整！'
  if (completionRate.value >= 60) return '画像已基本完善'
  if (completionRate.value >= 40) return '继续完善画像'
  return '快来完善你的画像吧'
})

// 圆形进度条计算（悬浮）
const floatingCircumference = 2 * Math.PI * 34
const floatingOffset = computed(() => {
  return floatingCircumference - (completionRate.value / 100) * floatingCircumference
})

const startStatusEdit = () => {
  statusInput.value = userData.value.currentStatus || ''
  isEditingStatus.value = true
}

const saveStatus = () => {
  userData.value.currentStatus = statusInput.value.trim()
  persistProfile()
  isEditingStatus.value = false
}

const cancelStatus = () => {
  isEditingStatus.value = false
  statusInput.value = ''
}

// 跳转到编辑页面
const goToEdit = () => {
  router.push('/profile/edit')
}

const goToTaskHall = () => {
  router.push('/task-hall')
}
</script>

<style scoped>
.profile-container {
  min-height: 100vh;
  width: 100vw;
  background: linear-gradient(135deg, #e3f2fd 0%, #f5f9ff 100%);
  padding-bottom: 40px;
  overflow-x: hidden;
  position: relative;
}

/* 头部区域 */
.profile-header {
  position: relative;
  background: white;
  margin-bottom: 30px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  width: 100%;
}

.header-bg {
  height: 180px;
  background: linear-gradient(135deg, #42a5f5 0%, #2196f3 50%, #1976d2 100%);
}

.header-content {
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 0 30px;
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 20px;
  margin-top: 30px;
}

@media (max-width: 1024px) {
  .header-content {
    padding: 0 20px 30px;
  }
}

.avatar-section {
  display: flex;
  align-items: flex-end;
  gap: 20px;
  margin-top: -60px;
}

.avatar {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: linear-gradient(135deg, #64b5f6, #2196f3);
  border: 5px solid white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
}

.avatar-text {
  font-size: 48px;
  font-weight: bold;
  color: white;
}

.user-basic-info {
  padding-bottom: 10px;
}

.username {
  font-size: 28px;
  font-weight: bold;
  color: #1565c0;
  margin: 0 0 5px 0;
}

.user-subtitle {
  font-size: 16px;
  color: #757575;
  margin: 0;
}

.status-row {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: linear-gradient(135deg, #f8fbff, #eef4ff);
  border: 1px solid rgba(33, 150, 243, 0.2);
  border-radius: 999px;
  color: #1565c0;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: 0 6px 14px rgba(33, 150, 243, 0.1);
  width: fit-content;
}

.status-pill:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(33, 150, 243, 0.15);
}

.status-pill.empty {
  color: #7a8ca8;
  border-style: dashed;
  background: #f7f9fb;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #4caf50;
  box-shadow: 0 0 0 4px rgba(76, 175, 80, 0.15);
}

.status-pill.empty .status-dot {
  background: #b0bec5;
  box-shadow: none;
}

.status-text {
  font-size: 14px;
}

.status-edit {
  font-size: 13px;
  color: #5c7599;
}

.status-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #fff;
  border: 1px solid #e3e9f5;
  border-radius: 12px;
  padding: 10px 12px;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.06);
}

.status-input {
  padding: 10px 12px;
  border: 1px solid #cfd8e3;
  border-radius: 8px;
  font-size: 14px;
  width: 100%;
}

.status-actions {
  display: flex;
  gap: 10px;
}

.status-save,
.status-cancel {
  padding: 8px 14px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-weight: 600;
  font-size: 13px;
}

.status-save {
  background: linear-gradient(135deg, #42a5f5, #2196f3);
  color: #fff;
}

.status-cancel {
  background: #f1f5fb;
  color: #5c7599;
  border: 1px solid #e3e9f5;
}

.edit-button {
  padding: 8px 20px;
  background: linear-gradient(135deg, #2196f3, #1976d2);
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 6px rgba(33, 150, 243, 0.3);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ghost-button {
  padding: 8px 18px;
  background: #ffffff;
  color: #1565c0;
  border: 1px solid rgba(21, 101, 192, 0.2);
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.ghost-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.2);
}

.edit-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.4);
}

.edit-icon {
  font-size: 14px;
}

/* 内容区域 */
.profile-content {
  max-width: 1200px;
  width: calc(100% - 40px);
  margin: 0 auto;
  padding: 0 20px;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  box-sizing: border-box;
}

@media (max-width: 900px) {
  .profile-content {
    grid-template-columns: 1fr;
    width: calc(100% - 30px);
    padding: 0 15px;
  }
}

/* 信息卡片 */
.info-card {
  background: white;
  border-radius: 16px;
  padding: 25px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.info-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.completion-card {
  grid-column: 1 / -1;
  border: 2px solid #e3f2fd;
}

.status-card {
  grid-column: 1 / -1;
  background: linear-gradient(135deg, #fff9e6 0%, #fff 100%);
}

/* 卡片标题 */
.card-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #f5f5f5;
}

.card-title {
  font-size: 18px;
  font-weight: bold;
  color: #1565c0;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-icon {
  font-size: 22px;
}

/* 信息网格 */
.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-label {
  font-size: 13px;
  color: #9e9e9e;
  font-weight: 500;
}

.info-value {
  font-size: 16px;
  color: #424242;
  font-weight: 600;
}

.info-value.highlight {
  color: #2196f3;
  font-weight: bold;
  font-size: 18px;
}

/* 详细信息区域 */
.card-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-label {
  font-size: 14px;
  color: #757575;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.label-icon {
  font-size: 16px;
}

.detail-content {
  font-size: 15px;
  color: #424242;
  line-height: 1.6;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 8px;
  border-left: 3px solid #2196f3;
}

/* 标签列表 */
.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag {
  padding: 6px 14px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 500;
}

.skill-tag {
  background: linear-gradient(135deg, #e3f2fd, #bbdefb);
  color: #1976d2;
  border: 1px solid #90caf9;
}

.consumption-tag {
  background: linear-gradient(135deg, #f3e5f5, #e1bee7);
  color: #7b1fa2;
  border: 1px solid #ce93d8;
}

.career-tag {
  background: linear-gradient(135deg, #e8f5e9, #c8e6c9);
  color: #388e3c;
  border: 1px solid #81c784;
}

/* 当前状态 */
.status-content {
  font-size: 16px;
  color: #424242;
  line-height: 1.8;
  padding: 15px;
  background: white;
  border-radius: 12px;
  border-left: 4px solid #ffc107;
  font-style: italic;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 30px;
  color: #9e9e9e;
}

.empty-state p {
  margin: 0 0 15px 0;
  font-size: 15px;
}

.link-button {
  background: none;
  border: none;
  color: #2196f3;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.link-button:hover {
  color: #1976d2;
  transform: translateX(5px);
}

/* 完成度卡片 */
.completion-content {
  display: flex;
  align-items: center;
  gap: 40px;
  justify-content: center;
}

.circular-progress {
  position: relative;
}

.progress-ring {
  transform: rotate(-90deg);
}

.progress-ring-circle {
  transition: stroke-dashoffset 0.5s ease;
  stroke-linecap: round;
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.progress-number {
  font-size: 28px;
  font-weight: bold;
  color: #1976d2;
}

.completion-info {
  text-align: left;
}

.completion-title {
  font-size: 20px;
  font-weight: bold;
  color: #1565c0;
  margin: 0 0 8px 0;
}

.completion-subtitle {
  font-size: 14px;
  color: #757575;
  margin: 0 0 15px 0;
}

.improve-button {
  padding: 10px 24px;
  background: linear-gradient(135deg, #42a5f5, #2196f3);
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.improve-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
}

/* 悬浮画像进度 */
.floating-progress {
  position: fixed;
  right: 24px;
  bottom: 24px;
  width: 260px;
  background: #ffffff;
  border: 1px solid #e3e9f5;
  border-radius: 16px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.12);
  padding: 14px;
  z-index: 20;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.floating-progress.mobile {
  right: 14px;
  bottom: 14px;
  width: 220px;
}

.floating-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.floating-title {
  font-weight: 700;
  color: #0b2b66;
  font-size: 14px;
}

.floating-action {
  border: none;
  background: linear-gradient(135deg, #42a5f5, #2196f3);
  color: #fff;
  border-radius: 10px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.28);
}

.floating-body {
  display: flex;
  align-items: center;
  gap: 12px;
}

.circular-progress.small {
  width: 84px;
  height: 84px;
}

.progress-text.small .progress-number {
  font-size: 20px;
}

.floating-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.floating-sub {
  margin: 0;
  font-size: 13px;
  color: #5c7599;
}

.floating-tip {
  margin: 0;
  font-size: 14px;
  color: #1565c0;
  font-weight: 700;
}

@media (max-width: 640px) {
  .floating-progress {
    position: sticky;
    width: 100%;
    right: auto;
    bottom: auto;
    margin: 14px 0;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .profile-container {
    padding-bottom: 20px;
  }

  .profile-content {
    grid-template-columns: 1fr;
    padding: 0 15px;
  }

  .header-bg {
    height: 120px;
  }

  .header-content {
    flex-direction: column;
    align-items: center;
    gap: 15px;
    padding: 0 15px 20px;
    margin-top: 20px;
  }

  .avatar-section {
    flex-direction: column;
    align-items: center;
    text-align: center;
    margin-top: -40px;
  }

  .avatar {
    width: 100px;
    height: 100px;
  }

  .avatar-text {
    font-size: 40px;
  }

  .username {
    font-size: 24px;
  }

  .user-subtitle {
    font-size: 14px;
  }

  .edit-button {
    margin-bottom: 0;
    width: 100%;
    justify-content: center;
  }

  .header-actions {
    width: 100%;
    flex-direction: column;
  }

  .ghost-button {
    width: 100%;
    justify-content: center;
  }

  .info-card {
    padding: 20px;
  }

  .info-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }

  .completion-content {
    flex-direction: column;
    gap: 20px;
  }

  .completion-info {
    text-align: center;
  }

  .circular-progress {
    transform: scale(0.9);
  }
}

@media (max-width: 480px) {
  .profile-content {
    padding: 0 10px;
  }

  .info-card {
    padding: 15px;
  }

  .card-title {
    font-size: 16px;
  }

  .card-icon {
    font-size: 18px;
  }

  .tag {
    font-size: 12px;
    padding: 6px 12px;
  }
}
</style>
