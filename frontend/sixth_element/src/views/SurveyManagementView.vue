<script setup>
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { handleTokenExpired } from '@/utils/authHelper'
import {
  getSurveys,
  deleteSurvey,
  pauseSurvey,
  resumeSurvey,
  publishSurvey
} from '@/utils/surveyManagementApi'

const router = useRouter()
const route = useRoute()
const pointsBalance = ref(1240)

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
const hideCompleted = ref(false)
const showDeleteModal = ref(false)
const deleteTarget = ref(null)
const showPublishModal = ref(false)
const showPublishConfigModal = ref(false)
const publishTarget = ref(null)
const publishConfig = ref({
  rewardPoints: 3,
  targetCount: 30,
  promptConstraint: '',
  speedBoostPoints: 0,
  estimatedMinutes: 5
})

// 计算建议的加速积分（20%）
const suggestedBoostPoints = computed(() => {
  const total = publishConfig.value.rewardPoints * publishConfig.value.targetCount
  return Math.ceil(total * 0.2)
})

const surveys = ref([])
const loading = ref(false)
const error = ref('')

const filteredSurveys = computed(() => {
  if (!hideCompleted.value) {
    return surveys.value
  }
  return surveys.value.filter((survey) => survey.status !== 'ended')
})

const sections = computed(() => {
  const draft = []
  const live = []
  const ended = []

  filteredSurveys.value.forEach((survey) => {
    if (survey.status === 'draft') {
      draft.push(survey)
      return
    }
    if (survey.status === 'ended') {
      ended.push(survey)
      return
    }
    live.push(survey)
  })

  const result = [
    { key: 'draft', title: '未发出', hint: '已创建但尚未发布', items: draft },
    { key: 'live', title: '已发出', hint: '进行中 / 暂停中', items: live },
    { key: 'ended', title: '已结束', hint: '份数已满的问卷', items: ended },
  ]

  if (hideCompleted.value) {
    return result.filter((section) => section.key !== 'ended')
  }

  return result
})

const progressText = (survey) => `${survey.completed}/${survey.target}`

const openDeleteModal = (survey) => {
  deleteTarget.value = survey
  showDeleteModal.value = true
}

const closeDeleteModal = () => {
  showDeleteModal.value = false
  deleteTarget.value = null
}

const closePublishModal = () => {
  showPublishModal.value = false
  router.replace({ query: {} })
}

const openPublishConfig = (survey) => {
  publishTarget.value = survey
  publishConfig.value = {
    rewardPoints: 3,
    targetCount: 30,
    promptConstraint: '',
    speedBoostPoints: 0,
    estimatedMinutes: 5
  }
  showPublishConfigModal.value = true
}

const closePublishConfig = () => {
  showPublishConfigModal.value = false
  publishTarget.value = null
}

const confirmPublish = async () => {
  if (!publishTarget.value) return
  
  try {
    loading.value = true
    const boostPoints = publishConfig.value.speedBoostPoints || 0
    await publishSurvey(publishTarget.value.id, {
      budget_points: publishConfig.value.rewardPoints * publishConfig.value.targetCount + boostPoints,
      target: publishConfig.value.targetCount
    })
    
    // 刷新问卷列表
    await loadSurveys()
    closePublishConfig()
  } catch (err) {
    // 检查是否是登录过期
    if (err.message.includes('登录已过期')) {
      handleTokenExpired(router)
      return
    }
    error.value = err.message
    setTimeout(() => {
      error.value = ''
    }, 3000)
  } finally {
    loading.value = false
  }
}

const confirmDelete = async () => {
  if (!deleteTarget.value) return
  
  try {
    loading.value = true
    await deleteSurvey(deleteTarget.value.id)
    
    // 刷新问卷列表
    await loadSurveys()
    closeDeleteModal()
  } catch (err) {
    // 检查是否是登录过期
    if (err.message.includes('登录已过期')) {
      handleTokenExpired(router)
      return
    }
    error.value = err.message
    setTimeout(() => {
      error.value = ''
    }, 3000)
  } finally {
    loading.value = false
  }
}

const togglePause = async (survey) => {
  try {
    loading.value = true
    if (survey.status === 'paused') {
      await resumeSurvey(survey.id)
    } else if (survey.status === 'live') {
      await pauseSurvey(survey.id)
    }
    
    // 刷新问卷列表
    await loadSurveys()
  } catch (err) {
    // 检查是否是登录过期
    if (err.message.includes('登录已过期')) {
      handleTokenExpired(router)
      return
    }
    error.value = err.message
    setTimeout(() => {
      error.value = ''
    }, 3000)
  } finally {
    loading.value = false
  }
}

const openSurvey = (survey) => {
  router.push({ name: 'survey-builder', params: { id: survey.id } })
}

const openAnalytics = (survey) => {
  router.push({ name: 'survey-analytics', params: { id: survey.id } })
}

const loadSurveys = async () => {
  try {
    loading.value = true
    const response = await getSurveys()
    surveys.value = response.items || []
  } catch (err) {
    // 检查是否是登录过期
    if (err.message.includes('登录已过期')) {
      handleTokenExpired(router)
      return
    }
    error.value = err.message
    setTimeout(() => {
      error.value = ''
    }, 3000)
  } finally {
    loading.value = false
  }
}

watch(
  () => route.query.publish,
  (value) => {
    if (value === '1') {
      showPublishModal.value = true
    }
  },
  { immediate: true },
)

onMounted(() => {
  loadSurveys()
  // 初始化导航菜单位置（右上角）
  if (menuRef.value) {
    const headerRect = menuRef.value.closest('.survey-header')?.getBoundingClientRect()
    if (headerRect) {
      menuPosition.value = { x: headerRect.width - 200, y: 12 }
    }
  }
  // 从localStorage读取用户积分
  try {
    const profile = localStorage.getItem('sixth_element_profile')
    if (profile) {
      const userData = JSON.parse(profile)
      pointsBalance.value = userData.points || 0
    }
  } catch (error) {
    console.error('读取用户积分失败:', error)
  }
})

onUnmounted(() => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', stopDrag)
})
</script>

<template>
  <div class="survey-main">
    <header class="survey-header">
      <div>
        <p class="header-kicker">Survey Management</p>
        <h1>问卷管理</h1>
      </div>
      
      <!-- 创建问卷按钮 -->
      <RouterLink class="primary-button create-btn" to="/survey/new">
        <span class="button-icon">📝</span>
        <span>创建问卷</span>
      </RouterLink>

      <!-- 可拖动的导航菜单 -->
      <div
        class="nav-right draggable-menu"
        ref="menuRef"
        :style="{ left: menuPosition.x + 'px', top: menuPosition.y + 'px' }"
        @mousedown="startDrag($event)"
        @touchstart="startDrag($event)"
      >
        <div class="drag-handle">⋮⋮</div>
        <RouterLink class="points-badge" to="/points">
          <span class="points-icon">💰</span>
          <span class="points-value">{{ pointsBalance }}</span>
        </RouterLink>
        <RouterLink class="avatar" to="/profile" aria-label="个人信息">
          <span>U</span>
        </RouterLink>
      </div>
    </header>

    <section class="control-bar">
      <label class="toggle">
        <input v-model="hideCompleted" type="checkbox" />
        <span class="toggle-track"></span>
        <span class="toggle-label">隐藏已完成问卷</span>
      </label>
    </section>

      <section class="survey-lists">
        <div v-for="section in sections" :key="section.key" class="survey-section">
          <div class="section-header">
            <div>
              <h2>{{ section.title }}</h2>
              <p>{{ section.hint }}</p>
            </div>
            <span class="section-count">{{ section.items.length }}</span>
          </div>

          <div v-if="section.items.length === 0" class="empty-state">
            当前没有问卷，试试创建新的模板。
          </div>

          <div v-for="survey in section.items" :key="survey.id" class="survey-card" @contextmenu.prevent="openDeleteModal(survey)">
            <button class="delete-btn" @click.stop="openDeleteModal(survey)" aria-label="删除问卷">
              ×
            </button>
            <div class="survey-meta">
              <div>
                <p class="survey-title">{{ survey.title }}</p>
                <p class="survey-id">{{ survey.id }} · 最近更新 {{ survey.updated_at }}</p>
              </div>
            </div>

            <div class="survey-progress">
              <div class="progress-bar">
                <div
                  class="progress-fill"
                  :style="{ width: `${Math.min(100, (survey.completed / survey.target) * 100)}%` }"
                ></div>
              </div>
              <p class="progress-text">{{ progressText(survey) }}</p>
            </div>

            <div class="survey-actions">
              <button
                v-if="survey.status === 'draft'"
                class="primary-button small"
                type="button"
                @click="openPublishConfig(survey)"
              >
                发布问卷
              </button>
              <button
                v-if="survey.status === 'live' || survey.status === 'paused'"
                class="primary-button small"
                :class="{ 'pause-btn': survey.status === 'live', 'resume-btn': survey.status === 'paused' }"
                type="button"
                @click="togglePause(survey)"
              >
                {{ survey.status === 'paused' ? '继续发布' : '暂停发布' }}
              </button>
              <button
                v-if="survey.status === 'ended'"
                class="primary-button small"
                type="button"
                @click="openAnalytics(survey)"
              >
                数据分析
              </button>
              <button
                v-if="survey.status !== 'ended'"
                class="ghost-button"
                type="button"
                @click="openSurvey(survey)"
              >
                编辑/查看问卷
              </button>
              <button
                v-if="survey.status === 'ended'"
                class="ghost-button"
                type="button"
                @click="openSurvey(survey)"
              >
                查看问卷
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>

  <div v-if="showDeleteModal" class="modal-backdrop" @click.self="closeDeleteModal">
    <div class="modal">
      <h3>确认删除</h3>
      <p>删除后的问卷无法复原，确定要删除吗？</p>
      <div class="modal-actions">
        <button class="ghost-button" type="button" @click="closeDeleteModal">取消</button>
        <button class="danger-button" type="button" @click="confirmDelete">确认</button>
      </div>
    </div>
  </div>

  <div v-if="showPublishModal" class="modal-backdrop" @click.self="closePublishModal">
    <div class="modal">
      <h3>发问卷确认</h3>
      <p>发布将进行积分结算并进入投放流程，确认现在发布吗？</p>
      <div class="modal-actions">
        <button class="ghost-button" type="button" @click="closePublishModal">稍后再说</button>
        <button class="primary-button" type="button" @click="closePublishModal">确认发布</button>
      </div>
    </div>
  </div>

  <!-- 发布配置模态框 -->
  <div v-if="showPublishConfigModal" class="modal-backdrop" @click.self="closePublishConfig">
    <div class="modal config-modal">
      <h3>发布问卷配置</h3>
      <div class="config-form">
        <div class="form-group">
          <label>奖励积分（每份）</label>
          <input v-model.number="publishConfig.rewardPoints" type="number" min="1" max="10" />
          <span class="hint">每份问卷给填写者的积分</span>
        </div>
        <div class="form-group">
          <label>目标份数</label>
          <input v-model.number="publishConfig.targetCount" type="number" min="10" max="1000" placeholder="30" />
          <span class="hint">需要收集的问卷份数</span>
        </div>
        <div class="form-group">
          <label>预估时间（分钟）</label>
          <input v-model.number="publishConfig.estimatedMinutes" type="number" min="1" max="60" />
          <span class="hint">填写问卷需要的时间</span>
        </div>
        <div class="form-group">
          <label>人群锁定（可选）</label>
          <textarea v-model="publishConfig.promptConstraint" rows="3" placeholder="例如：只想要大一到大三女生的数据、不需要研究生和博士生的数据等..."></textarea>
          <span class="hint">我们的AI助手会根据您的需求智能投放问卷</span>
        </div>
        <div class="form-group">
          <label>积分加速（可选）</label>
          <div class="boost-input-wrapper">
            <input v-model.number="publishConfig.speedBoostPoints" type="number" min="0" :placeholder="`建议 ${suggestedBoostPoints} 积分`" />
            <span class="boost-suggest">建议：{{ suggestedBoostPoints }} 积分</span>
          </div>
          <span class="hint">使用积分进行额外曝光，更高效地收集您问卷的结果，使用的积分越多效果越显著噢~</span>
        </div>
        <div class="cost-summary">
          <div class="cost-row">
            <span>基础成本</span>
            <span>{{ publishConfig.rewardPoints * publishConfig.targetCount }} 积分</span>
          </div>
          <div v-if="publishConfig.speedBoostPoints > 0" class="cost-row">
            <span>加速费用</span>
            <span>{{ publishConfig.speedBoostPoints }} 积分</span>
          </div>
          <div class="cost-row total">
            <span>总计</span>
            <strong>{{ publishConfig.rewardPoints * publishConfig.targetCount + (publishConfig.speedBoostPoints || 0) }} 积分</strong>
          </div>
        </div>
      </div>
      <div class="modal-actions">
        <button class="ghost-button" type="button" @click="closePublishConfig">取消</button>
        <button class="primary-button" type="button" @click="confirmPublish">确认发布</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.survey-main {
  min-height: 100vh;
  background: radial-gradient(circle at top left, #edf3ff 0%, #f7f9ff 45%, #ffffff 100%);
  padding: 48px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.survey-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  position: relative;
}

.survey-header h1 {
  font-family: 'Newsreader', serif;
  font-size: 32px;
  color: #0d1b37;
  margin: 6px 0 0 0;
}

.header-kicker {
  text-transform: uppercase;
  letter-spacing: 0.24em;
  font-size: 11px;
  color: #5a7395;
  margin: 0;
}

/* 可拖动导航菜单 */
.draggable-menu {
  position: fixed;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12px);
  border-radius: 999px;
  box-shadow: 0 4px 16px rgba(13, 27, 55, 0.12);
  z-index: 100;
  cursor: grab;
  user-select: none;
  transition: box-shadow 0.2s ease;
}

.draggable-menu:hover {
  box-shadow: 0 6px 20px rgba(13, 27, 55, 0.18);
}

.draggable-menu:active {
  cursor: grabbing;
}

.drag-handle {
  font-size: 14px;
  color: #a0afc7;
  letter-spacing: 2px;
  opacity: 0.6;
}

.points-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: linear-gradient(135deg, #fff4dc 0%, #ffe8b8 100%);
  border-radius: 999px;
  text-decoration: none;
  transition: transform 0.2s ease;
}

.points-badge:hover {
  transform: scale(1.05);
}

.points-icon {
  font-size: 16px;
}

.points-value {
  font-weight: 700;
  font-size: 14px;
  color: #b16112;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2665d4, #4f80f1);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  font-weight: 700;
  font-size: 14px;
  box-shadow: 0 2px 8px rgba(38, 101, 212, 0.3);
  transition: transform 0.2s ease;
}

.avatar:hover {
  transform: scale(1.1);
}

.create-btn {
  margin-left: auto;
}

.primary-button {
  background: linear-gradient(135deg, #2665d4, #4f80f1);
  color: #ffffff;
  padding: 12px 20px;
  border-radius: 14px;
  font-weight: 600;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  border: none;
  font-size: 14px;
  transition: all 0.2s ease;
}

.primary-button:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.primary-button.small {
  padding: 8px 16px;
  font-size: 13px;
  border-radius: 999px;
}

/* 暂停发布按钮 - 橙色 */
.primary-button.pause-btn {
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
}

/* 继续发布按钮 - 绿色 */
.primary-button.resume-btn {
  background: linear-gradient(135deg, #10b981, #34d399);
}

.button-icon {
  font-size: 16px;
  line-height: 1;
}

.control-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 18px 20px;
  background: #ffffff;
  border-radius: 20px;
  box-shadow: 0 4px 12px rgba(13, 27, 55, 0.08);
}

.toggle {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: #415673;
  cursor: pointer;
}

.toggle input {
  display: none;
}

.toggle-track {
  width: 44px;
  height: 24px;
  border-radius: 999px;
  background: #d8e4f4;
  position: relative;
  transition: background 0.2s ease;
}

.toggle-track::after {
  content: '';
  position: absolute;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #ffffff;
  top: 3px;
  left: 4px;
  transition: transform 0.2s ease;
  box-shadow: 0 4px 8px rgba(16, 35, 63, 0.2);
}

.toggle input:checked + .toggle-track {
  background: #2665d4;
}

.toggle input:checked + .toggle-track::after {
  transform: translateX(20px);
}

.toggle-label {
  user-select: none;
}

.survey-lists {
  display: grid;
  gap: 24px;
}

.survey-section {
  background: #ffffff;
  padding: 20px;
  border-radius: 22px;
  box-shadow: 0 4px 12px rgba(13, 27, 55, 0.08);
  display: grid;
  gap: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5edf8;
}

.section-header h2 {
  font-size: 20px;
  color: #0d1b37;
  margin: 0;
}

.section-header p {
  font-size: 13px;
  color: #6d7f9a;
  margin: 0;
}

.section-count {
  width: 32px;
  height: 32px;
  border-radius: 12px;
  background: #e6effa;
  color: #1e4fb4;
  display: grid;
  place-items: center;
  font-weight: 600;
  font-size: 14px;
}

.survey-card {
  border-radius: 18px;
  border: 1px solid #e7edf7;
  padding: 18px 20px;
  display: grid;
  gap: 14px;
  background: #fbfdff;
  transition: all 0.3s ease;
  position: relative;
}

.delete-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: rgba(244, 67, 54, 0.1);
  color: #f44336;
  font-size: 20px;
  font-weight: bold;
  line-height: 1;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.delete-btn:hover {
  background: #f44336;
  color: white;
  transform: scale(1.1);
}

.survey-card:hover {
  border-color: #d0dff0;
  box-shadow: 0 4px 12px rgba(13, 27, 55, 0.08);
}

.survey-meta {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  padding-right: 40px; /* 给删除按钮留空间 */
}

.survey-title {
  font-weight: 600;
  font-size: 16px;
  color: #0d1b37;
  flex: 1;
}

.survey-id {
  font-size: 12px;
  color: #7b8da7;
}

.survey-progress {
  display: flex;
  align-items: center;
  gap: 16px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  border-radius: 999px;
  background: #e5edf8;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #2665d4, #4f80f1);
  border-radius: 999px;
}

.progress-text {
  font-size: 12px;
  color: #6b7b94;
  min-width: 60px;
  text-align: right;
}

.survey-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  padding-top: 6px;
  border-top: 1px solid #e7edf7;
}

.ghost-button {
  padding: 8px 16px;
  border-radius: 999px;
  background: #ffffff;
  border: 1px solid rgba(26, 59, 127, 0.2);
  color: #1a3b7f;
  font-weight: 600;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s ease;
}

.ghost-button:hover {
  border-color: #1e4fb4;
  background: #f5f9ff;
}

.primary-button {
  padding: 8px 16px;
  border-radius: 999px;
  border: none;
  background: linear-gradient(135deg, #2665d4, #4f80f1);
  color: #ffffff;
  font-weight: 600;
  cursor: pointer;
}

.card-hint {
  font-size: 12px;
  color: #97a5bb;
}

.empty-state {
  padding: 18px;
  border-radius: 14px;
  background: #f2f6ff;
  color: #6c7c95;
  font-size: 14px;
  text-align: center;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(13, 27, 55, 0.4);
  display: grid;
  place-items: center;
  z-index: 30;
}

.modal {
  background: #ffffff;
  border-radius: 20px;
  padding: 24px;
  width: min(360px, 90vw);
  box-shadow: 0 20px 50px rgba(13, 27, 55, 0.25);
  display: grid;
  gap: 16px;
}

.modal h3 {
  font-size: 18px;
  color: #0d1b37;
  margin: 0;
}

.modal p {
  font-size: 14px;
  color: #6b7b94;
  margin: 0;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.danger-button {
  padding: 8px 16px;
  border-radius: 999px;
  border: none;
  background: #ef4444;
  color: #ffffff;
  font-weight: 600;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.2s ease;
}

.danger-button:hover {
  background: #dc2626;
}

.config-modal {
  width: min(480px, 90vw);
  max-height: 90vh;
  overflow-y: auto;
}

.config-form {
  display: grid;
  gap: 20px;
}

.form-group {
  display: grid;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 600;
  color: #0d1b37;
}

.form-group input[type="number"],
.form-group textarea {
  padding: 10px 14px;
  border: 1px solid #d8e4f4;
  border-radius: 10px;
  font-size: 14px;
  color: #0d1b37;
  background: #ffffff;
  transition: all 0.2s ease;
}

.form-group input[type="number"]:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #2665d4;
  box-shadow: 0 0 0 3px rgba(38, 101, 212, 0.1);
}

.form-group textarea {
  resize: vertical;
  font-family: inherit;
}

.form-group .hint {
  font-size: 12px;
  color: #6d7f9a;
}

/* 积分加速输入样式 */
.boost-input-wrapper {
  position: relative;
}

.boost-input-wrapper input {
  width: 100%;
  padding-right: 120px;
}

.boost-suggest {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 12px;
  color: #10b981;
  font-weight: 500;
}

.cost-summary {
  background: #f2f6ff;
  padding: 16px;
  border-radius: 12px;
  display: grid;
  gap: 10px;
}

.cost-row {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: #415673;
}

.cost-row.total {
  padding-top: 10px;
  border-top: 1px solid #d8e4f4;
  font-size: 16px;
  color: #0d1b37;
}

.cost-row.total strong {
  color: #1e4fb4;
  font-size: 18px;
}

@media (max-width: 768px) {
  .survey-main {
    margin-left: 0;
    padding: 24px;
    padding-top: 80px; /* 给可拖动菜单留空间 */
  }

  .survey-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .control-bar {
    flex-direction: column;
    align-items: flex-start;
  }

  .create-btn {
    width: 100%;
    justify-content: center;
  }

  /* 移动端可拖动菜单位置 */
  .draggable-menu {
    top: 16px !important;
    left: auto !important;
    right: 16px;
    padding: 6px 12px;
  }

  .config-modal {
    width: 95vw;
  }

  /* 减小卡片间距 */
  .survey-card {
    padding: 14px 16px;
    gap: 10px;
  }

  .survey-actions {
    gap: 8px;
  }

  .primary-button.small,
  .ghost-button {
    padding: 6px 12px;
    font-size: 12px;
  }
}

@media (max-width: 480px) {
  .survey-main {
    padding: 16px;
    padding-top: 70px;
  }

  .survey-card {
    padding: 12px 14px;
  }

  .survey-header h1 {
    font-size: 24px;
  }

  .survey-title {
    font-size: 14px;
  }

  .survey-id {
    font-size: 11px;
  }

  .draggable-menu {
    gap: 8px;
    padding: 5px 10px;
  }

  .points-badge {
    padding: 4px 8px;
  }

  .points-value {
    font-size: 12px;
  }

  .avatar {
    width: 30px;
    height: 30px;
    font-size: 12px;
  }

  .survey-meta {
    flex-direction: column;
  }
}
</style>