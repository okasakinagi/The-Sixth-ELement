<template>
  <div class="profile-container">
    <!-- 左上角返回按钮 -->
    <div class="top-back-btn-container">
      <button class="top-back-btn" @click="goBack">
        <span class="back-arrow">←</span>
        <span class="back-text">返回</span>
      </button>
    </div>

    <!-- 个人主页头部 -->
    <div class="profile-header">
      <div class="header-bg"></div>
      <div class="header-content">
        <div class="avatar-section">
          <div class="avatar">
            <span class="avatar-text">{{ userInitial }}</span>
          </div>
          <div class="user-basic-info">
            <div class="username-row">
              <h1 class="username">{{ userBasicInfo.nickname || '未设置姓名' }}</h1>
              <div v-if="levelInfo" class="level-badge-small">
                <span class="level-text-small">Lv{{ levelInfo.level }} · {{ levelInfo.title }}</span>
                <div class="exp-wrapper" @mouseenter="showExpTooltip" @mouseleave="hideExpTooltip">
                  <div class="exp-bar-tiny">
                    <div class="exp-fill-tiny" :style="{ width: levelInfo.progress_pct + '%' }"></div>
                  </div>
                  <span class="exp-num" :class="{ show: showExp }">{{ levelInfo.exp_in_level }}/{{ levelInfo.exp_to_next }}</span>
                </div>
              </div>
            </div>
            <p class="user-subtitle">{{ userData.college || '未设置学院' }} · {{ userData.major || '未设置专业' }}</p>
            <div class="status-row">
              <div
                class="status-pill"
                :class="{ empty: !currentStatusDisplay }"
                @click="openStatusModal"
              >
                <span class="status-dot" :class="{ active: currentStatusDisplay }"></span>
                <span class="status-text">{{ currentStatusDisplay || '设置状态' }}</span>
                <span class="status-edit">✏️</span>
              </div>
            </div>
          </div>
        </div>
        <div class="header-actions">
          <button class="edit-button" @click="goToEdit">
            <span class="edit-icon">✏️</span>
            编辑资料
          </button>
        </div>
      </div>
    </div>

    <!-- 状态设置弹窗（仿微信） -->
    <div v-if="showStatusModal" class="status-modal-overlay" @click.self="closeStatusModal">
      <div class="status-modal">
        <div class="modal-header">
          <h3>设置状态</h3>
          <button class="modal-close" @click="closeStatusModal">×</button>
        </div>
        
        <!-- 状态分类列表 -->
        <div class="status-categories">
          <!-- 情绪 / 生活状态类 -->
          <div class="category-section">
            <div class="category-title">😊 情绪 / 生活状态</div>
            <div class="status-options">
              <div 
                v-for="status in moodStatuses" 
                :key="status.value"
                class="status-option"
                :class="{ selected: selectedStatus === status.value }"
                @click="selectStatus(status.value)"
              >
                <span class="option-emoji">{{ status.emoji }}</span>
                <span class="option-text">{{ status.label }}</span>
              </div>
            </div>
          </div>

          <!-- 时间 / 精力状态类 -->
          <div class="category-section">
            <div class="category-title">⏰ 时间 / 精力状态</div>
            <div class="status-options">
              <div 
                v-for="status in timeStatuses" 
                :key="status.value"
                class="status-option"
                :class="{ selected: selectedStatus === status.value }"
                @click="selectStatus(status.value)"
              >
                <span class="option-emoji">{{ status.emoji }}</span>
                <span class="option-text">{{ status.label }}</span>
              </div>
            </div>
          </div>

          <!-- 关系 / 生活阶段类 -->
          <div class="category-section">
            <div class="category-title">💕 关系 / 生活阶段</div>
            <div class="status-options">
              <div 
                v-for="status in relationStatuses" 
                :key="status.value"
                class="status-option"
                :class="{ selected: selectedStatus === status.value }"
                @click="selectStatus(status.value)"
              >
                <span class="option-emoji">{{ status.emoji }}</span>
                <span class="option-text">{{ status.label }}</span>
              </div>
            </div>
          </div>

          <!-- 学习 / 校园场景类 -->
          <div class="category-section">
            <div class="category-title">📚 学习 / 校园场景</div>
            <div class="status-options">
              <div 
                v-for="status in studyStatuses" 
                :key="status.value"
                class="status-option"
                :class="{ selected: selectedStatus === status.value }"
                @click="selectStatus(status.value)"
              >
                <span class="option-emoji">{{ status.emoji }}</span>
                <span class="option-text">{{ status.label }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 补充描述 -->
        <div class="status-description-section" v-if="selectedStatus">
          <label class="desc-label">补充描述（可选）</label>
          <textarea 
            v-model="statusDescription"
            class="desc-input"
            placeholder="说点什么来描述你的状态..."
            maxlength="50"
            rows="2"
          ></textarea>
          <div class="desc-counter">{{ statusDescription.length }}/50</div>
        </div>

        <!-- 状态时效提示 -->
        <div class="status-validity-hint">
          <span class="hint-icon">⏱️</span>
          <span>状态将在 24 小时后自动失效，你可以随时修改或关闭</span>
        </div>

        <!-- 操作按钮 -->
        <div class="modal-actions">
          <button class="clear-status-btn" @click="clearStatus" v-if="userData.currentStatus">
            清除状态
          </button>
          <button class="cancel-btn" @click="closeStatusModal">取消</button>
          <button class="confirm-btn" @click="confirmStatus" :disabled="!selectedStatus">
            确认
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
          <div class="detail-section" v-if="userData.interests && userData.interests.length > 0">
            <div class="detail-label">
              <span class="label-icon">🔬</span>
              研究方向 / 兴趣课程
            </div>
            <div class="tag-list">
              <span class="tag skill-tag" v-for="interest in userData.interests" :key="interest">
                {{ interest }}
              </span>
            </div>
          </div>

          <!-- 社团经历 -->
          <div class="detail-section" v-if="userData.organizations && userData.organizations.length > 0">
            <div class="detail-label">
              <span class="label-icon">🎭</span>
              社团 / 组织经历
            </div>
            <div class="tag-list">
              <span class="tag skill-tag" v-for="org in userData.organizations" :key="org">
                {{ org }}
              </span>
            </div>
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
          <div v-if="(!userData.interests || userData.interests.length === 0) && (!userData.organizations || userData.organizations.length === 0) && (!userData.skills || userData.skills.length === 0)" class="empty-state">
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
    <div v-if="showFloatingProgress" class="floating-progress" :class="{ mobile: isMobile }">
      <div class="floating-header">
        <span class="floating-title">画像完成度</span>
        <div class="floating-header-right">
          <button v-if="completionRate < 100" class="floating-action" @click="goToEdit">去完善</button>
          <button class="floating-close" @click="dismissFloating" aria-label="关闭">×</button>
        </div>
      </div>
      <div class="floating-body">
        <div class="circular-progress small">
          <svg class="progress-ring" width="84" height="84" viewBox="0 0 84 84">
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
import { ref, computed, onMounted, onBeforeUnmount, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { handleTokenExpired } from '@/utils/authHelper'
import { getUserProfile, updateUserProfile, getCurrentUser } from '@/utils/profileApi'
import { getUserLevel } from '@/utils/levelApi'

const router = useRouter()

const defaultProfile = {
  user_id: null,
  gender: '',
  age: null,
  grade: '',
  college: '',
  major: '',
  mbti: '',
  interests: [],
  organizations: [],
  consumptionPreferences: [],
  careerIntention: [],
  skills: [],
  currentStatus: '',
  profile_completion: 0
}

const userData = ref({ ...defaultProfile })
const userBasicInfo = ref({ nickname: '加载中...' })
const levelInfo = ref(null)
const isMobile = ref(window.innerWidth <= 768)
const isLoading = ref(true)
const errorMessage = ref('')

// 悬浮完成度窗口
const showFloatingProgress = ref(false)
const FLOATING_STATUS_KEY = 'profile_floating_status'

function checkFloatingVisibility() {
  const rate = completionRate.value
  const stored = localStorage.getItem(FLOATING_STATUS_KEY)
  let status = null
  if (stored) {
    try { status = JSON.parse(stored) } catch {}
  }

  if (rate === 100) {
    // 100% 时：已展示过则不再显示
    if (status?.type === '100_seen') {
      showFloatingProgress.value = false
      return
    }
    // 首次达到100%：展示并立即记录，3秒后自动关闭
    localStorage.setItem(FLOATING_STATUS_KEY, JSON.stringify({ type: '100_seen' }))
    showFloatingProgress.value = true
    setTimeout(() => {
      showFloatingProgress.value = false
    }, 3000)
  } else {
    // < 100% 时：被关闭后 24h 内不再显示
    if (status?.type === 'dismissed' && Date.now() < status.until) {
      showFloatingProgress.value = false
      return
    }
    showFloatingProgress.value = true
  }
}

function dismissFloating() {
  localStorage.setItem(FLOATING_STATUS_KEY, JSON.stringify({
    type: 'dismissed',
    until: Date.now() + 24 * 60 * 60 * 1000
  }))
  showFloatingProgress.value = false
}

// 状态弹窗相关
const showStatusModal = ref(false)
const selectedStatus = ref('')
const statusDescription = ref('')
const showExp = ref(false)

// 预置状态配置
const moodStatuses = [
  { value: '心情不错', label: '心情不错', emoji: '😊' },
  { value: '有点emo', label: '有点emo', emoji: '😔' },
  { value: '累了', label: '累了', emoji: '😴' },
  { value: '美滋滋', label: '美滋滋', emoji: '🥰' },
  { value: '平静中', label: '平静中', emoji: '😌' }
]

const timeStatuses = [
  { value: '有空', label: '有空', emoji: '🆓' },
  { value: '有点忙', label: '有点忙', emoji: '🏃' },
  { value: '很忙', label: '很忙', emoji: '🔥' },
  { value: '碎片时间', label: '碎片时间', emoji: '⏱️' },
  { value: '摸鱼中', label: '摸鱼中', emoji: '🐟' }
]

const relationStatuses = [
  { value: '恋爱中', label: '恋爱中', emoji: '💑' },
  { value: '单身', label: '单身', emoji: '🙋' },
  { value: '暗恋中', label: '暗恋中', emoji: '💭' },
  { value: '室友矛盾中', label: '室友矛盾中', emoji: '😤' }
]

const studyStatuses = [
  { value: '学习中', label: '学习中', emoji: '📖' },
  { value: '赶ddl', label: '赶ddl', emoji: '⏰' },
  { value: '在实习', label: '在实习', emoji: '💼' },
  { value: '备考中', label: '备考中', emoji: '✍️' },
  { value: '刚下课', label: '刚下课', emoji: '🎒' }
]

// 当前显示的状态（主状态 + 描述，第3段为时间戳不显示）
const currentStatusDisplay = computed(() => {
  if (!userData.value.currentStatus) return ''
  // 存储格式: "主状态|描述|timestamp" 或 "主状态|描述" 或 "主状态"
  const parts = userData.value.currentStatus.split('|')
  if (parts[1]) {
    return `${parts[0]} · ${parts[1]}`
  }
  return parts[0]
})

const handleResize = () => {
  isMobile.value = window.innerWidth <= 768
}

/**
 * 加载用户画像数据
 */
const loadProfile = async () => {
  isLoading.value = true
  errorMessage.value = ''
  
  try {
    // 并发获取用户基本信息和画像
    const [basicInfo, profile] = await Promise.all([
      getCurrentUser(),
      getUserProfile()
    ])
    
    userBasicInfo.value = basicInfo
    
    // 映射后端数据到前端格式
    userData.value = {
      user_id: profile.user_id,
      gender: profile.gender || '',
      age: profile.age || null,
      grade: profile.grade || '',
      college: profile.college || '',
      major: profile.major || '',
      mbti: profile.mbti || '',
      interests: profile.interests || [],
      organizations: profile.organizations || [],
      consumptionPreferences: profile.consumption_preferences || [],
      careerIntention: profile.career_intention || [],
      skills: profile.skills || [],
      currentStatus: profile.current_status || '',
      profile_completion: profile.profile_completion || 0
    }
    localStorage.setItem('sixth_element_profile_completion', String(profile.profile_completion || 0))
    // 检查是否展示悬浮完成度窗口
    checkFloatingVisibility()
    // 24小时自动清除状态（时间戳存在后端状态字符串第3段，多端通用）
    if (userData.value.currentStatus) {
      const parts = userData.value.currentStatus.split('|')
      const timestamp = parts[2] ? parseInt(parts[2]) : null
      if (timestamp && Date.now() - timestamp > 24 * 60 * 60 * 1000) {
        updateUserProfile({ current_status: '' }).then(() => {
          userData.value.currentStatus = ''
        }).catch(err => console.error('自动清除状态失败:', err))
      }
    }
  } catch (error) {
    console.error('加载画像失败:', error)
    errorMessage.value = error.message
    
    // 检查是否是登录过期
    if (error.message.includes('登录已过期')) {
      handleTokenExpired(router)
      return
    }
    
    // 其他认证错误，3秒后跳转到登录页
    if (error.message.includes('登录')) {
      setTimeout(() => {
        router.push('/auth')
      }, 2000)
    }
  } finally {
    isLoading.value = false
  }
}

// 用户名首字母
const userInitial = computed(() => {
  const name = userBasicInfo.value.nickname || '?'
  return name.charAt(0).toUpperCase()
})

// 计算完成度（使用后端返回的值）
const completionRate = computed(() => {
  return userData.value.profile_completion || 0
})

// 完成度提示信息
const completionMessage = computed(() => {
  if (completionRate.value >= 80) return '画像非常完整！'
  if (completionRate.value >= 60) return '画像比较完整'
  if (completionRate.value >= 40) return '继续完善可提升匹配度'
  return '画像完成度较低，建议完善'
})

// 打开状态弹窗
const openStatusModal = () => {
  // 解析当前状态（格式: 主状态|描述|timestamp）
  if (userData.value.currentStatus) {
    const parts = userData.value.currentStatus.split('|')
    selectedStatus.value = parts[0] || ''
    statusDescription.value = parts[1] || ''
  } else {
    selectedStatus.value = ''
    statusDescription.value = ''
  }
  showStatusModal.value = true
}

// 关闭状态弹窗
const closeStatusModal = () => {
  showStatusModal.value = false
  selectedStatus.value = ''
  statusDescription.value = ''
  showExp.value = false
}

const showExpTooltip = () => {
  showExp.value = true
}

const hideExpTooltip = () => {
  showExp.value = false
}

// 选择状态
const selectStatus = (status) => {
  selectedStatus.value = status
}

// 确认状态
const confirmStatus = async () => {
  if (!selectedStatus.value) return
  
  // 组合状态字符串: "主状态|描述|timestamp"（时间戳随状态存后端，多端通用）
  const ts = Date.now()
  const statusValue = statusDescription.value.trim()
    ? `${selectedStatus.value}|${statusDescription.value.trim()}|${ts}`
    : `${selectedStatus.value}||${ts}`
  
  try {
    await updateUserProfile({ current_status: statusValue })
    userData.value.currentStatus = statusValue
    closeStatusModal()
  } catch (error) {
    console.error('保存状态失败:', error)
    
    if (error.message.includes('登录已过期')) {
      handleTokenExpired(router)
      return
    }
    
    alert('保存失败: ' + error.message)
  }
}

// 清除状态
const clearStatus = async () => {
  try {
    await updateUserProfile({ current_status: '' })
    userData.value.currentStatus = ''
    closeStatusModal()
  } catch (error) {
    console.error('清除状态失败:', error)
    
    if (error.message.includes('登录已过期')) {
      handleTokenExpired(router)
      return
    }
    
    alert('清除失败: ' + error.message)
  }
}

// 圆形进度条计算（悬浮）
const floatingCircumference = 2 * Math.PI * 34
const floatingOffset = computed(() => {
  return floatingCircumference - (completionRate.value / 100) * floatingCircumference
})

// 跳转到编辑页面
const goToEdit = () => {
  router.push('/profile/edit')
}

const goToTaskHall = () => {
  router.push('/task-hall')
}

// 返回上一页
const goBack = () => {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/task-hall')
  }
}

// 拖拽相关
const menuRef = ref(null)
const menuPosition = ref({ x: 0, y: 0 })
const dragState = ref({ isDragging: false, startX: 0, startY: 0, initialX: 0, initialY: 0 })

function startDrag(e) {
  const clientX = e.type.includes('touch') ? e.touches[0]?.clientX : e.clientX
  const clientY = e.type.includes('touch') ? e.touches[0]?.clientY : e.clientY

  if (!clientX || !clientY) return

  dragState.value = {
    isDragging: true,
    startX: clientX,
    startY: clientY,
    initialX: menuPosition.value.x,
    initialY: menuPosition.value.y
  }

  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  document.addEventListener('touchmove', onDrag)
  document.addEventListener('touchend', stopDrag)
}

function onDrag(e) {
  if (!dragState.value.isDragging) return
  
  const clientX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX
  const clientY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY

  const deltaX = clientX - dragState.value.startX
  const deltaY = clientY - dragState.value.startY

  menuPosition.value = {
    x: dragState.value.initialX + deltaX,
    y: dragState.value.initialY + deltaY
  }
}

function stopDrag() {
  dragState.value.isDragging = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', stopDrag)
}

// 组件挂载时加载数据
onMounted(() => {
  loadProfile()
  loadLevelInfo()
  window.addEventListener('resize', handleResize)
})

async function loadLevelInfo() {
  try {
    const token = localStorage.getItem('access_token')
    console.log('Token exists:', !!token)
    console.log('Loading level info...')
    levelInfo.value = await getUserLevel(router)
    console.log('Level info loaded:', levelInfo.value)
  } catch (e) {
    console.error('获取等级信息失败:', e)
  }
}

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})

onUnmounted(() => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', stopDrag)
})
</script>

<style scoped>
/* 可拖动悬浮菜单 */
.draggable-menu {
  position: fixed;
  z-index: 100;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(12px);
  border: 1px solid #e3e9f5;
  border-radius: 16px;
  padding: 8px 12px;
  box-shadow: 0 8px 24px rgba(0, 82, 217, 0.15);
  cursor: move;
  touch-action: none;
  user-select: none;
  transition: box-shadow 0.2s ease;
  display: flex;
  align-items: center;
  gap: 10px;
}

.draggable-menu:hover {
  box-shadow: 0 12px 32px rgba(0, 82, 217, 0.22);
}

.drag-handle {
  position: absolute;
  left: 4px;
  top: 50%;
  transform: translateY(-50%);
  color: #a0b0cc;
  font-size: 14px;
  letter-spacing: -2px;
  cursor: grab;
}

.drag-handle:active {
  cursor: grabbing;
}

.points-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: linear-gradient(135deg, #ffd700, #ffb400);
  color: #333;
  border-radius: 12px;
  text-decoration: none;
  font-weight: 700;
  font-size: 14px;
  box-shadow: 0 4px 12px rgba(255, 180, 0, 0.3);
  transition: transform 0.2s ease;
}

.points-badge:hover {
  transform: scale(1.05);
}

.points-icon {
  font-size: 16px;
}

.points-value {
  font-family: 'Courier New', monospace;
}

.avatar-link {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0052d9, #2f7bff);
  color: white;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  font-weight: 700;
  box-shadow: 0 6px 12px rgba(0, 82, 217, 0.16);
  transition: transform 0.2s ease;
}

.avatar-link:hover {
  transform: scale(1.1);
}

.avatar-link span {
  font-size: 16px;
}

.profile-container {
  min-height: 100vh;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  background: linear-gradient(135deg, #e3f2fd 0%, #f5f9ff 100%);
  padding: 0 0 40px;
  overflow-x: hidden;
  position: relative;
}

:global(.main-content) {
  padding: 0;
  background: transparent;
}

/* 左上角返回按钮 */
.top-back-btn-container {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 100;
}

.top-back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(33, 150, 243, 0.2);
  border-radius: 22px;
  color: #1565c0;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(8px);
}

.top-back-btn:hover {
  background: #ffffff;
  transform: translateX(-4px);
  box-shadow: 0 6px 16px rgba(33, 150, 243, 0.2);
}

.back-arrow {
  font-size: 18px;
  font-weight: bold;
}

/* 头部区域 */
.profile-header {
  position: relative;
  background: white;
  margin-bottom: 30px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  width: 100%;
  box-sizing: border-box;
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
  align-items: flex-start;
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
  flex-shrink: 0;
}

.avatar-text {
  font-size: 48px;
  font-weight: bold;
  color: white;
}

.user-basic-info {
  padding-bottom: 0;
  padding-top: 45px;
}

.username-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.username {
  font-size: 28px;
  font-weight: bold;
  background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 0.4px;
  margin: 0;
  filter: drop-shadow(0 2px 4px rgba(30, 58, 95, 0.15));
}

.level-badge-small {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, #fafbff 0%, #f0f2ff 100%);
  border: 1px solid #e0e3f0;
  padding: 3px 10px 3px 8px;
  border-radius: 20px;
  box-shadow: 0 1px 4px rgba(80, 90, 160, 0.06);
}

.level-text-small {
  font-size: 11px;
  color: #5a5a8a;
  font-weight: 600;
  letter-spacing: 0.2px;
}

.exp-wrapper {
  display: flex;
  align-items: center;
  gap: 5px;
}

.exp-bar-tiny {
  width: 36px;
  height: 4px;
  background: #e8ebf5;
  border-radius: 2px;
  overflow: hidden;
}

.exp-fill-tiny {
  height: 100%;
  background: linear-gradient(90deg, #7c8df5, #9b6ddb);
  border-radius: 2px;
}

.exp-num {
  font-size: 10px;
  color: #8888aa;
  font-weight: 500;
  opacity: 0;
  transform: translateX(-3px);
  transition: all 0.2s ease;
  white-space: nowrap;
}

.exp-num.show {
  opacity: 1;
  transform: translateX(0);
}

.user-subtitle {
  font-size: 15px;
  color: #757575;
  margin: 0;
}

.status-row {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: linear-gradient(135deg, #f8fbff, #eef4ff);
  border: 1px solid rgba(33, 150, 243, 0.2);
  border-radius: 999px;
  color: #1565c0;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: 0 6px 14px rgba(33, 150, 243, 0.1);
  width: fit-content;
  max-width: 300px;
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
  background: #b0bec5;
  flex-shrink: 0;
}

.status-dot.active {
  background: #4caf50;
  box-shadow: 0 0 0 4px rgba(76, 175, 80, 0.15);
}

.status-text {
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-edit {
  font-size: 13px;
  color: #5c7599;
  flex-shrink: 0;
}

/* 状态弹窗样式 */
.status-modal-overlay {
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
  padding: 20px;
}

.status-modal {
  background: white;
  border-radius: 20px;
  width: 100%;
  max-width: 480px;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
  position: sticky;
  top: 0;
  background: white;
  z-index: 10;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #1f2b3a;
}

.modal-close {
  width: 32px;
  height: 32px;
  border: none;
  background: #f5f7fa;
  border-radius: 50%;
  font-size: 20px;
  color: #666;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.modal-close:hover {
  background: #e8ecf0;
  color: #333;
}

.status-categories {
  padding: 16px 24px;
}

.category-section {
  margin-bottom: 20px;
}

.category-section:last-child {
  margin-bottom: 0;
}

.category-title {
  font-size: 13px;
  font-weight: 600;
  color: #8a94a6;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-options {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.status-option {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: #f5f7fa;
  border: 2px solid transparent;
  border-radius: 24px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.status-option:hover {
  background: #e8f4fd;
  transform: translateY(-2px);
}

.status-option.selected {
  background: linear-gradient(135deg, #e3f2fd, #bbdefb);
  border-color: #2196f3;
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.2);
}

.option-emoji {
  font-size: 18px;
}

.option-text {
  font-size: 14px;
  font-weight: 500;
  color: #1f2b3a;
}

.status-description-section {
  padding: 0 24px 16px;
}

.desc-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #5c6b82;
  margin-bottom: 8px;
}

.desc-input {
  width: 100%;
  padding: 12px 14px;
  border: 2px solid #e8ecf0;
  border-radius: 12px;
  font-size: 14px;
  resize: none;
  transition: all 0.2s;
  font-family: inherit;
}

.desc-input:focus {
  outline: none;
  border-color: #2196f3;
  box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
}

.desc-counter {
  text-align: right;
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
}

.status-validity-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: #fffbeb;
  font-size: 12px;
  color: #92400e;
}

.hint-icon {
  font-size: 14px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  padding: 16px 24px 24px;
  justify-content: flex-end;
}

.clear-status-btn {
  padding: 10px 20px;
  background: #fef2f2;
  color: #ef4444;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-right: auto;
}

.clear-status-btn:hover {
  background: #fee2e2;
}

.cancel-btn {
  padding: 10px 20px;
  background: #f5f7fa;
  color: #5c6b82;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn:hover {
  background: #e8ecf0;
}

.confirm-btn {
  padding: 10px 24px;
  background: linear-gradient(135deg, #42a5f5, #2196f3);
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
}

.confirm-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(33, 150, 243, 0.4);
}

.confirm-btn:disabled {
  background: #e0e0e0;
  color: #9e9e9e;
  cursor: not-allowed;
  box-shadow: none;
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
  width: 100%;
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
    width: 100%;
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

.floating-header-right {
  display: flex;
  align-items: center;
  gap: 6px;
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

.floating-close {
  width: 22px;
  height: 22px;
  border: none;
  background: #f0f4f8;
  border-radius: 50%;
  color: #8a97a8;
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: background 0.2s, color 0.2s;
  flex-shrink: 0;
}

.floating-close:hover {
  background: #dde5ef;
  color: #374151;
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

/* 手机端悬浮画像进度 - 与PC端同步，固定在右下角 */
@media (max-width: 640px) {
  .floating-progress {
    position: fixed;
    right: 12px;
    bottom: 12px;
    width: 200px;
    padding: 12px;
  }
  
  .floating-progress.mobile {
    right: 12px;
    bottom: 12px;
    width: 200px;
  }
  
  .floating-body {
    flex-direction: column;
    gap: 8px;
  }
  
  .circular-progress.small {
    width: 70px;
    height: 70px;
  }
  
  .circular-progress.small svg {
    width: 70px;
    height: 70px;
  }
  
  .progress-text.small .progress-number {
    font-size: 16px;
  }
  
  .floating-info {
    text-align: center;
  }
  
  .floating-sub {
    font-size: 11px;
  }
  
  .floating-tip {
    font-size: 12px;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .profile-container {
    padding-bottom: 20px;
  }
  
  .top-back-btn-container {
    top: 12px;
    left: 12px;
  }
  
  .top-back-btn {
    padding: 8px 14px;
    font-size: 13px;
  }

  /* 移动端悬浮菜单优化 */
  .draggable-menu {
    top: 16px !important;
    left: auto !important;
    right: 16px;
    padding: 6px 10px;
    gap: 8px;
  }

  .points-badge {
    padding: 5px 10px;
    font-size: 13px;
  }

  .avatar-link {
    width: 32px;
    height: 32px;
    font-size: 14px;
  }

  /* 等级经验卡片样式 */
  .level-exp-card {
    max-width: 1200px;
    margin: 20px auto;
    padding: 0 30px;
  }

  .level-exp-content {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    padding: 20px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
    position: relative;
    overflow: hidden;
  }

  .level-exp-content::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 200px;
    height: 200px;
    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
    border-radius: 50%;
  }

  .level-left {
    display: flex;
    align-items: center;
    gap: 16px;
    flex: 1;
  }

  .level-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    margin-bottom: 16px;
    gap: 12px;
  }

  .level-label {
    margin: 0;
    font-size: 12px;
    letter-spacing: 0.18em;
    color: rgba(255, 255, 255, 0.8);
    text-transform: uppercase;
  }

  .level-subtitle {
    margin: 4px 0 0;
    font-size: 15px;
    color: #ffffff;
    font-weight: 600;
  }

  .level-current-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 10px 16px;
    border-radius: 999px;
    color: #1a1a2e;
    background: rgba(255, 255, 255, 0.9);
    font-weight: 800;
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.12);
  }

  .level-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: linear-gradient(135deg, #ffd700 0%, #ffb400 100%);
    border-radius: 20px;
    padding: 10px 16px;
    box-shadow: 0 8px 24px rgba(255, 182, 0, 0.3);
  }

  .level-num {
    font-size: 26px;
    font-weight: 900;
    color: #1a1a2e;
    letter-spacing: 1px;
  }

  .level-details {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .level-title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .level-title {
    font-size: 16px;
    font-weight: 700;
    color: #ffffff;
  }

  .level-exp-value {
    font-size: 14px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
    background: rgba(255, 255, 255, 0.2);
    padding: 4px 12px;
    border-radius: 8px;
  }

  .exp-progress-container {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .exp-bar {
    height: 12px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 6px;
    overflow: hidden;
    position: relative;
  }

  .exp-fill {
    height: 100%;
    background: linear-gradient(90deg, #00f260 0%, #0575e6 100%);
    border-radius: 6px;
    transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
  }

  .level-exp-content.loading .level-badge {
    background: rgba(255, 255, 255, 0.18);
  }

  .level-exp-content.loading .level-title,
  .level-exp-content.loading .level-exp-value,
  .level-exp-content.loading .exp-current,
  .level-exp-content.loading .exp-next {
    color: rgba(255, 255, 255, 0.65);
  }

  .level-exp-content.loading .exp-fill {
    background: rgba(255, 255, 255, 0.22);
  }

  .exp-fill::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      90deg,
      transparent,
      rgba(255, 255, 255, 0.3),
      transparent
    );
    animation: shimmer 2s infinite;
  }

  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }

  .exp-text {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.9);
    font-weight: 500;
  }

  .exp-current {
    font-weight: 700;
    color: #00f260;
  }

  .exp-divider {
    color: rgba(255, 255, 255, 0.5);
    margin: 0 4px;
  }

  .exp-next {
    color: rgba(255, 255, 255, 0.7);
  }

  .level-right {
    display: flex;
    align-items: center;
    gap: 8px;
    padding-left: 20px;
    border-left: 2px solid rgba(255, 255, 255, 0.3);
  }

  .next-level-info {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(255, 255, 255, 0.15);
    padding: 10px 14px;
    border-radius: 14px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.95);
  }

  .next-level-info.max-level {
    justify-content: center;
    width: 100%;
    background: rgba(255, 255, 255, 0.18);
  }

  .max-level-text {
    font-size: 14px;
    color: #ffecb3;
    font-weight: 700;
  }

  .next-arrow {
    color: #00f260;
    font-weight: bold;
  }

  .next-level-badge {
    background: rgba(255, 255, 255, 0.25);
    color: #ffffff;
    border-radius: 999px;
    padding: 4px 10px;
    font-weight: 700;
  }

  .next-level-badge {
    background: rgba(255, 255, 255, 0.2);
    padding: 4px 10px;
    border-radius: 6px;
    font-weight: 700;
    color: #ffffff;
  }

  .max-level {
    gap: 8px;
  }

  .star-icon {
    font-size: 18px;
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

  .status-row {
    align-items: center;
  }
  
  .status-pill {
    margin: 0 auto;
    max-width: 220px;
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
  
  /* 状态弹窗响应式 */
  .status-modal {
    max-width: 100%;
    max-height: 90vh;
    border-radius: 16px 16px 0 0;
    margin-top: auto;
  }
  
  .status-modal-overlay {
    align-items: flex-end;
    padding: 0;
  }
  
  .status-options {
    gap: 8px;
  }
  
  .status-option {
    padding: 8px 12px;
    font-size: 13px;
  }
  
  .modal-actions {
    flex-wrap: wrap;
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

  /* 移动端悬浮菜单进一步优化 */
  .draggable-menu {
    gap: 6px;
    padding: 5px 8px;
  }

  .points-badge {
    padding: 4px 8px;
    font-size: 12px;
  }

  .points-icon {
    font-size: 14px;
  }

  .avatar-link {
    width: 30px;
    height: 30px;
    font-size: 14px;
  }

  .drag-handle {
    font-size: 12px;
  }
}
</style>
