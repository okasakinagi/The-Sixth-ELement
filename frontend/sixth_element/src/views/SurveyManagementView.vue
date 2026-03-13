<script setup>
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { handleTokenExpired } from '@/utils/authHelper'
import {
  getSurveys,
  deleteSurvey,
  pauseSurvey,
  resumeSurvey,
  publishSurvey,
  evaluateSurvey,
  getSurveyDetail,
} from '@/utils/surveyManagementApi'
import { cancelPublish } from '@/utils/surveyManagementApi'

const router = useRouter()
const route = useRoute()

const hideCompleted = ref(false)
const showDeleteModal = ref(false)
const deleteTarget = ref(null)
const showCancelModal = ref(false)
const cancelTarget = ref(null)
const cancelEstimate = ref(null)
const showPublishModal = ref(false)
const showPublishConfigModal = ref(false)
const isEvaluating = ref(false)
const isPublishing = ref(false)
const publishConfigMessage = ref('')
const publishConfigMessageType = ref('info')
const publishEvaluateSeq = ref(0)
const publishTarget = ref(null)
const publishConfig = ref({
  rewardPoints: 3,
  targetCount: 30,
  speedBoostPoints: 0,
  estimatedMinutes: 5,
  difficulty: 1.0
})

// 计算建议的加速积分（20%）
const suggestedBoostPoints = computed(() => {
  const total = publishConfig.value.rewardPoints * publishConfig.value.targetCount
  return Math.ceil(total * 0.2)
})

const surveys = ref([])
const loading = ref(false)
const error = ref('')

const setPublishConfigMessage = (message, type = 'info') => {
  publishConfigMessage.value = message
  publishConfigMessageType.value = type
}

const clearPublishConfigMessage = () => {
  publishConfigMessage.value = ''
  publishConfigMessageType.value = 'info'
}

const extractErrorMessage = (err) => {
  if (!err) return '未知错误'

  const INVALID_TEXT = new Set(['', '{}', '[]', 'null', 'undefined', '""', "''"])

  const normalizeText = (value) => {
    const text = String(value ?? '').trim()
    if (!text || INVALID_TEXT.has(text)) return ''
    if (/^[()（）\s]+$/.test(text)) return ''
    return text
  }

  const pickMessage = (value) => {
    if (value == null) return ''

    if (typeof value === 'string') {
      const text = normalizeText(value)
      if (!text) return ''

      // 尝试解析 JSON 字符串，例如 "{}" 或 "{\"message\":\"...\"}"
      try {
        const parsed = JSON.parse(text)
        const parsedMsg = pickMessage(parsed)
        if (parsedMsg) return parsedMsg
      } catch {
        // 非 JSON 字符串，直接使用
      }

      return text
    }

    if (Array.isArray(value)) {
      const parts = value.map(pickMessage).filter(Boolean)
      return Array.from(new Set(parts)).join('；')
    }

    if (typeof value === 'object') {
      const candidates = [
        value.message,
        value.error,
        value.detail,
        value.details,
        value.msg,
      ]
      for (const candidate of candidates) {
        const msg = pickMessage(candidate)
        if (msg) return msg
      }
      return ''
    }

    return normalizeText(value)
  }

  const raw = err
  const message = pickMessage(raw)
  return message || '未知错误'
}

const runPublishEvaluation = async (surveyId) => {
  if (!surveyId) return

  const currentSeq = ++publishEvaluateSeq.value
  isEvaluating.value = true
  setPublishConfigMessage('AI 正在评估问卷，评估期间你仍可随时取消。', 'info')

  try {
    const evaluation = await evaluateSurvey(surveyId)
    if (currentSeq !== publishEvaluateSeq.value || !showPublishConfigModal.value) return

    publishConfig.value.estimatedMinutes = evaluation.estimated_time_minutes || 5
    publishConfig.value.difficultyLevel = evaluation.difficulty_level || 3
    publishConfig.value.rewardPoints = publishConfig.value.difficultyLevel
    setPublishConfigMessage('评估完成，可调整参数后发布。', 'success')
  } catch (err) {
    if (currentSeq !== publishEvaluateSeq.value || !showPublishConfigModal.value) return
    console.error('Failed to evaluate survey:', err)
    setPublishConfigMessage('AI 评估失败，已使用默认值。你可以继续发布，或取消后重试。', 'warning')
  } finally {
    if (currentSeq === publishEvaluateSeq.value) {
      isEvaluating.value = false
    }
  }
}

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

const openCancelModal = async (survey) => {
  // 获取问卷详情以计算预估退还积分（仅估算基础预算，不含加速积分）
  try {
    loading.value = true
    const detail = await getSurveyDetail(survey.id)
    const completed = detail.completed || 0
    const target = detail.target || 0
    const reward = detail.reward_points || 0
    const remaining = Math.max(0, target - completed)
    // 估算退还：剩余份数 * 每份奖励；注意：若存在加速积分，实际退还会更少
    cancelEstimate.value = remaining * reward
  } catch (err) {
    console.error('获取问卷详情失败，无法估算退还积分：', err)
    cancelEstimate.value = null
  } finally {
    loading.value = false
    cancelTarget.value = survey
    showCancelModal.value = true
  }
}

const closeCancelModal = () => {
  cancelTarget.value = null
  showCancelModal.value = false
}

const closeDeleteModal = () => {
  showDeleteModal.value = false
  deleteTarget.value = null
}

const closePublishModal = () => {
  showPublishModal.value = false
  router.replace({ query: {} })
}

const handleConfirmPublishFromBuilder = async () => {
  // 尝试从 sessionStorage 读取编辑器保存的草稿并直接进入发布配置
  const raw = sessionStorage.getItem('survey-draft')
  if (!raw) {
    showPublishModal.value = false
    router.replace({ query: {} })
    error.value = '未找到待发布的问卷草稿'
    setTimeout(() => {
      error.value = ''
    }, 3000)
    return
  }

  let draft = null
  try {
    draft = JSON.parse(raw)
  } catch (e) {
    showPublishModal.value = false
    router.replace({ query: {} })
    error.value = '读取问卷草稿失败'
    setTimeout(() => {
      error.value = ''
    }, 3000)
    return
  }

  // 将草稿作为发布目标，初始化配置并打开发布配置弹窗
  publishTarget.value = draft
  showPublishModal.value = false
  publishConfig.value = {
    rewardPoints: 3,
    targetCount: 30,
    speedBoostPoints: 0,
    estimatedMinutes: 5,
    difficultyLevel: 3
  }
  clearPublishConfigMessage()
  showPublishConfigModal.value = true

  // AI 评估问卷难度（与从问卷列表点击发布的流程保持一致）
  if (draft.id) {
    await runPublishEvaluation(draft.id)
  } else {
    setPublishConfigMessage('未找到问卷 ID，已使用默认发布配置。', 'warning')
  }
}
const openPublishConfig = async (survey) => {
  publishTarget.value = survey
  publishConfig.value = {
    rewardPoints: 3,
    targetCount: 30,
    speedBoostPoints: 0,
    estimatedMinutes: 5,
    difficultyLevel: 3
  }
  clearPublishConfigMessage()
  showPublishConfigModal.value = true

  await runPublishEvaluation(survey.id)
}

const closePublishConfig = () => {
  publishEvaluateSeq.value += 1
  isEvaluating.value = false
  isPublishing.value = false
  clearPublishConfigMessage()
  showPublishConfigModal.value = false
  publishTarget.value = null
}

const confirmPublish = async () => {
  if (!publishTarget.value) return
  if (isEvaluating.value) {
    setPublishConfigMessage('AI 评估尚未完成，请稍候或点击取消关闭。', 'warning')
    return
  }
  
  try {
    isPublishing.value = true
    setPublishConfigMessage('正在发布问卷，请稍候...', 'info')
    loading.value = true
    const boostPoints = publishConfig.value.speedBoostPoints || 0
    await publishSurvey(publishTarget.value.id, {
      reward_points: publishConfig.value.rewardPoints,
      budget_points: publishConfig.value.rewardPoints * publishConfig.value.targetCount + boostPoints,
      target: publishConfig.value.targetCount,
      estimated_minutes: publishConfig.value.estimatedMinutes,
      difficulty: publishConfig.value.difficultyLevel
    })
    
    // 刷新问卷列表
    await loadSurveys()
    closePublishConfig()
    // 通知浮动菜单刷新积分（发布消耗积分）
    window.dispatchEvent(new CustomEvent('points-updated'))
  } catch (err) {
    // 检查是否是登录过期
    const errMsg = extractErrorMessage(err)
    if (errMsg.includes('登录已过期')) {
      handleTokenExpired(router)
      return
    }
    setPublishConfigMessage(`发布失败：${errMsg}`, 'error')
    setTimeout(() => {
      error.value = ''
    }, 3000)
  } finally {
    isPublishing.value = false
    loading.value = false
  }
}

const confirmDelete = async () => {
  if (!deleteTarget.value) return
  
  try {
    loading.value = true
    const delResp = await deleteSurvey(deleteTarget.value.id)
    
    // 刷新问卷列表
    await loadSurveys()
    closeDeleteModal()
    // 通知浮动菜单刷新积分（删除已发布问卷时可能退还积分）
    window.dispatchEvent(new CustomEvent('points-updated'))
    if (delResp?.refund > 0) {
      error.value = `问卷已删除，退还积分：${delResp.refund}`
      setTimeout(() => { error.value = '' }, 4000)
    }
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

const confirmCancel = async () => {
  if (!cancelTarget.value) return
  try {
    loading.value = true
    const resp = await cancelPublish(cancelTarget.value.id)
    await loadSurveys()
    closeCancelModal()
    // 通知浮动菜单刷新积分（取消发布退还积分）
    window.dispatchEvent(new CustomEvent('points-updated'))
    error.value = `已取消发布，退还积分：${resp.refund}（不含加速积分）`
    setTimeout(() => { error.value = '' }, 4000)
  } catch (err) {
    if (err.message.includes('登录已过期')) {
      handleTokenExpired(router)
      return
    }
    error.value = err.message
    setTimeout(() => { error.value = '' }, 4000)
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
})

onUnmounted(() => {
  // cleanup if needed
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
                v-if="survey.status === 'live' || survey.status === 'paused'"
                class="danger-button small"
                type="button"
                @click="openCancelModal(survey)"
              >
                取消发布
              </button>
              <button
                v-if="survey.status !== 'draft'"
                class="primary-button small"
                type="button"
                @click="openAnalytics(survey)"
              >
                数据分析
              </button>
              <button
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

  <div v-if="showCancelModal" class="modal-backdrop" @click.self="closeCancelModal">
    <div class="modal">
      <h3>确认取消发布</h3>
      <p>取消发布则问卷将不能在被填写，并退还剩余的基础预算积分（不退还加速积分）。</p>
      <p v-if="cancelEstimate !== null">预估可退还积分：<strong>{{ cancelEstimate }}</strong>（仅为预估，实际结果以返还积分为准）</p>
      <p v-else>正在获取预估退还积分，或无法获取详情。</p>
      <p>确定要取消发布吗？</p>
      <div class="modal-actions">
        <button class="ghost-button" type="button" @click="closeCancelModal">取消</button>
        <button class="danger-button" type="button" @click="confirmCancel">确认取消</button>
      </div>
    </div>
  </div>

  <div v-if="showPublishModal" class="modal-backdrop" @click.self="closePublishModal">
    <div class="modal">
      <h3>发问卷确认</h3>
      <p>发布将进行积分结算并进入投放流程，确认现在发布吗？</p>
      <div class="modal-actions">
        <button class="ghost-button" type="button" @click="closePublishModal">稍后再说</button>
        <button class="primary-button" type="button" @click="handleConfirmPublishFromBuilder">确认发布</button>
      </div>
    </div>
  </div>

  <!-- 发布配置模态框 -->
  <div v-if="showPublishConfigModal" class="modal-backdrop" @click.self="closePublishConfig">
    <div class="modal config-modal">
      <h3>发布问卷配置</h3>
      
      <div v-if="isEvaluating" class="evaluating-state">
        <div class="spinner"></div>
        <p>AI 正在评估问卷难度和预估时间...</p>
      </div>
      
      <div v-else class="config-form">
        <div class="form-group">
          <label>问卷难度与奖励</label>
          <div class="difficulty-display">
            <span class="difficulty-stars">
              <i v-for="n in 5" :key="n" class="star" :class="{ active: n <= publishConfig.difficultyLevel }">★</i>
            </span>
            <span class="difficulty-value">{{ publishConfig.difficultyLevel }} 级</span>
            <span class="reward-points-badge">自动奖励 {{ publishConfig.rewardPoints }} 积分/份</span>
          </div>
          <span class="hint">本结果由系统智能评估，如有明显不合理可提交反馈。</span>
        </div>
        <div class="form-group">
          <label>目标份数</label>
          <input v-model.number="publishConfig.targetCount" type="number" min="10" max="1000" placeholder="30" />
          <span class="hint">需要收集的问卷份数</span>
        </div>
        <div class="form-group">
          <label>预估时间（分钟）</label>
          <input v-model.number="publishConfig.estimatedMinutes" type="number" min="1" max="60" />
          <span class="hint">填写问卷需要的时间，该时间将由系统根据问卷结构智能评估，通常较为准确。建议保持默认值，以保障填写者体验与积分公平性。如有特殊情况可自行调整。</span>
        </div>

        <div class="form-group">
          <label>积分加速（可选）</label>
          <div class="boost-input-wrapper">
            <input v-model.number="publishConfig.speedBoostPoints" type="number" min="0" :placeholder="`建议 ${suggestedBoostPoints} 积分`" />
            <span class="boost-suggest">建议：{{ suggestedBoostPoints }} 积分</span>
          </div>
          <span class="hint">使用积分进行额外曝光，更高效地收集您问卷的结果，使用的积分越多效果越显著噢~</span>
          <span class="hint" style="color:#b16112">加速积分不予退还，取消发布时只会退还剩余的基础预算积分。</span>
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
      <div v-if="publishConfigMessage" class="publish-config-tip" :class="`tip-${publishConfigMessageType}`">
        {{ publishConfigMessage }}
      </div>
      <div class="modal-actions">
        <button class="ghost-button" type="button" @click="closePublishConfig">取消</button>
        <button class="primary-button" type="button" @click="confirmPublish" :disabled="isEvaluating || isPublishing">
          {{ isPublishing ? '发布中...' : (isEvaluating ? '评估中...' : '确认发布') }}
        </button>
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

.avatar {
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

.avatar:hover {
  transform: scale(1.1);
}

.avatar span {
  font-size: 16px;
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

.primary-button:disabled,
.ghost-button:disabled,
.danger-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.publish-config-tip {
  padding: 10px 12px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.5;
}

.publish-config-tip.tip-info {
  background: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
}

.publish-config-tip.tip-success {
  background: #ecfdf5;
  color: #047857;
  border: 1px solid #a7f3d0;
}

.publish-config-tip.tip-warning {
  background: #fffbeb;
  color: #b45309;
  border: 1px solid #fde68a;
}

.publish-config-tip.tip-error {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
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

.evaluating-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  gap: 16px;
  color: #415673;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e5edf8;
  border-top-color: #1e4fb4;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.difficulty-display {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.difficulty-value {
  font-size: 18px;
  font-weight: 600;
  color: #0d1b37;
}

.difficulty-stars {
  display: flex;
  gap: 4px;
}

.star {
  color: #cbd5e1;
  font-size: 18px;
  font-style: normal;
}

.star.active {
  color: #f59e0b;
}

.reward-points-badge {
  margin-left: auto;
  background: #eef2ff;
  color: #1e4fb4;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
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
  .danger-button.small,
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