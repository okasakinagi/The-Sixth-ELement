<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const router = useRouter()
const route = useRoute()
const pointsBalance = ref(1240)
const hideCompleted = ref(false)
const showDeleteModal = ref(false)
const deleteTarget = ref(null)
const showPublishModal = ref(false)
const showPublishConfigModal = ref(false)
const publishTarget = ref(null)
const publishConfig = ref({
  rewardPoints: 3,
  targetCount: 100,
  promptConstraint: '',
  speedBoost: false,
  estimatedMinutes: 5
})

const surveys = ref([
  {
    id: 'S-1204',
    title: '城市通勤满意度问卷',
    status: 'draft',
    completed: 0,
    target: 120,
    updatedAt: '2026-01-12',
  },
  {
    id: 'S-1205',
    title: '新品包装视觉偏好调研',
    status: 'live',
    completed: 64,
    target: 102,
    updatedAt: '2026-01-13',
  },
  {
    id: 'S-1206',
    title: '低碳出行行为追踪',
    status: 'paused',
    completed: 28,
    target: 60,
    updatedAt: '2026-01-10',
  },
  {
    id: 'S-1207',
    title: '会员服务体验反馈',
    status: 'ended',
    completed: 300,
    target: 300,
    updatedAt: '2026-01-08',
  },
])

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

const statusLabel = (survey) => {
  if (survey.status === 'draft') return '未发出'
  if (survey.status === 'paused') return '已发出 · 暂停中'
  if (survey.status === 'ended') return '已结束'
  return '已发出 · 进行中'
}

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
    targetCount: 100,
    promptConstraint: '',
    speedBoost: false,
    estimatedMinutes: 5
  }
  showPublishConfigModal.value = true
}

const closePublishConfig = () => {
  showPublishConfigModal.value = false
  publishTarget.value = null
}

const confirmPublish = () => {
  if (!publishTarget.value) return
  publishTarget.value.status = 'live'
  publishTarget.value.target = publishConfig.value.targetCount
  closePublishConfig()
}

const confirmDelete = () => {
  if (!deleteTarget.value) return
  surveys.value = surveys.value.filter((survey) => survey.id !== deleteTarget.value.id)
  closeDeleteModal()
}

const togglePause = (survey) => {
  if (survey.status === 'paused') {
    survey.status = 'live'
    return
  }
  if (survey.status === 'live') {
    survey.status = 'paused'
  }
}

const openSurvey = (survey) => {
  router.push({ name: 'survey-builder', params: { id: survey.id } })
}

const openAnalytics = (survey) => {
  router.push({ name: 'survey-analytics', params: { id: survey.id } })
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
</script>

<template>
  <div class="survey-main">
    <header class="survey-header">
      <div>
        <p class="header-kicker">Survey Management</p>
        <h1>问卷管理</h1>
      </div>
      <div class="header-actions">
        <RouterLink class="points" to="/points">
          <span>积分余额</span>
          <strong>{{ pointsBalance.toLocaleString() }}</strong>
        </RouterLink>
        <RouterLink class="avatar-button" to="/profile" aria-label="个人信息">
          <span>U</span>
        </RouterLink>
        <RouterLink class="primary-button" to="/survey/new">
          <span class="button-icon">📝</span>
          <span>创建问卷</span>
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
                <p class="survey-id">{{ survey.id }} · 最近更新 {{ survey.updatedAt }}</p>
              </div>
              <span class="status-badge" :data-status="survey.status">{{ statusLabel(survey) }}</span>
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
                class="ghost-button"
                type="button"
                @click="togglePause(survey)"
              >
                {{ survey.status === 'paused' ? '继续发布' : '暂停发布' }}
              </button>
              <button
                v-if="survey.status === 'ended'"
                class="ghost-button"
                type="button"
                @click="openAnalytics(survey)"
              >
                数据分析/查看问卷
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
          <input v-model.number="publishConfig.targetCount" type="number" min="10" max="1000" />
          <span class="hint">需要收集的问卷份数</span>
        </div>
        <div class="form-group">
          <label>预估时间（分钟）</label>
          <input v-model.number="publishConfig.estimatedMinutes" type="number" min="1" max="60" />
          <span class="hint">填写问卷需要的时间</span>
        </div>
        <div class="form-group">
          <label>Prompt约束（可选）</label>
          <textarea v-model="publishConfig.promptConstraint" rows="3" placeholder="例如：只允许本校学生填写、需要在校生等..."></textarea>
          <span class="hint">AI将根据约束过滤不符合条件的填写</span>
        </div>
        <div class="form-group checkbox-group">
          <label>
            <input v-model="publishConfig.speedBoost" type="checkbox" />
            <span>积分加速（额外消耗 {{ publishConfig.targetCount * 0.5 }} 积分）</span>
          </label>
          <span class="hint">优先展示给高活跃用户，加快收集速度</span>
        </div>
        <div class="cost-summary">
          <div class="cost-row">
            <span>基础成本</span>
            <span>{{ publishConfig.rewardPoints * publishConfig.targetCount }} 积分</span>
          </div>
          <div v-if="publishConfig.speedBoost" class="cost-row">
            <span>加速费用</span>
            <span>{{ publishConfig.targetCount * 0.5 }} 积分</span>
          </div>
          <div class="cost-row total">
            <span>总计</span>
            <strong>{{ publishConfig.rewardPoints * publishConfig.targetCount + (publishConfig.speedBoost ? publishConfig.targetCount * 0.5 : 0) }} 积分</strong>
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.points {
  display: grid;
  text-align: right;
  font-size: 12px;
  color: #5a7395;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 12px;
  transition: all 0.2s ease;
  cursor: pointer;
}

.points:hover {
  background: rgba(38, 101, 212, 0.05);
}

.points strong {
  font-size: 18px;
  color: #1e4fb4;
  font-weight: 600;
}

.avatar-button {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2665d4, #4f80f1);
  color: white;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  font-weight: 700;
  font-size: 16px;
  box-shadow: 0 4px 12px rgba(38, 101, 212, 0.2);
  transition: all 0.2s ease;
}

.avatar-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(38, 101, 212, 0.3);
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

.status-badge {
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  align-self: flex-start;
  white-space: nowrap;
}

.status-badge[data-status='draft'] {
  background: #eaf2ff;
  color: #1e4fb4;
}

.status-badge[data-status='live'] {
  background: #e7f7ee;
  color: #1a7f4d;
}

.status-badge[data-status='paused'] {
  background: #fff4df;
  color: #b16112;
}

.status-badge[data-status='ended'] {
  background: #f1f2f6;
  color: #5a6579;
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

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: normal;
  cursor: pointer;
}

.checkbox-group input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
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
  }

  .survey-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .control-bar {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-actions {
    width: 100%;
    display: grid;
    grid-template-columns: auto auto 1fr;
    gap: 10px;
  }

  .primary-button {
    grid-column: 1 / -1;
  }

  .config-modal {
    width: 95vw;
  }
}

@media (max-width: 480px) {
  .survey-main {
    padding: 16px;
  }

  .survey-card {
    padding: 14px 16px;
  }

  .survey-header h1 {
    font-size: 24px;
  }

  .survey-meta {
    flex-direction: column;
  }
}
</style>