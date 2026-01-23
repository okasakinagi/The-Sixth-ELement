<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const token = localStorage.getItem('access_token')

// 问卷数据
const survey = ref(null)
const loading = ref(false)
const error = ref(null)
const startTime = ref(null)

// 答案存储
const answers = ref({})
const showSuccessModal = ref(false)
const submitting = ref(false)
const validationErrors = ref(new Set())

// 计算进度
const progress = computed(() => {
  if (!survey.value?.questions) return 0
  const totalQuestions = survey.value.questions.length
  const answeredQuestions = Object.keys(answers.value).filter((qId) => {
    const answer = answers.value[qId]
    if (Array.isArray(answer)) return answer.length > 0
    if (typeof answer === 'string') return answer.trim() !== ''
    return false
  }).length
  return totalQuestions > 0 ? Math.round((answeredQuestions / totalQuestions) * 100) : 0
})

// 本地存储键名
const localStorageKey = computed(() => `survey-fill-${route.params.id}`)

// 加载问卷数据
async function fetchSurvey() {
  if (!token) {
    alert('未登录，请先登录')
    router.push('/auth')
    return
  }

  loading.value = true
  error.value = null

  try {
    const res = await fetch(`/api/v1/surveys/${route.params.id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })

    if (!res.ok) {
      // 开发模式：后端问卷不存在时使用模拟数据
      console.warn('问卷不存在，使用模拟数据进行演示')
      survey.value = {
        id: route.params.id,
        title: '员工餐厅就餐满意度调查（演示）',
        description: '这是一个演示问卷，用于展示问卷填写界面的功能。实际使用时需要后端返回真实的问卷数据。',
        reward_points: 10,
        estimated_minutes: 5,
        status: 'active',
        questions: generateMockQuestions(),
      }
      
      startTime.value = Date.now()
      loadAnswersFromStorage()
      loading.value = false
      return
    }

    const data = await res.json()
    
    // 模拟问卷题目结构（实际应从后端获取）
    // TODO: 后端实现 GET /api/v1/surveys/{id}/fill 接口
    survey.value = {
      ...data,
      questions: data.questions || generateMockQuestions(),
    }
    
    startTime.value = Date.now()
    
    // 从本地存储恢复答案
    loadAnswersFromStorage()
  } catch (err) {
    console.error('Failed to fetch survey:', err)
    // 网络错误时也使用模拟数据
    console.warn('网络错误，使用模拟数据进行演示')
    survey.value = {
      id: route.params.id,
      title: '员工餐厅就餐满意度调查（演示）',
      description: '这是一个演示问卷，用于展示问卷填写界面的功能。实际使用时需要后端返回真实的问卷数据。',
      reward_points: 10,
      estimated_minutes: 5,
      status: 'active',
      questions: generateMockQuestions(),
    }
    startTime.value = Date.now()
    loadAnswersFromStorage()
  } finally {
    loading.value = false
  }
}

// 生成模拟题目（用于演示，实际应从后端获取）
function generateMockQuestions() {
  return [
    {
      id: 'q_1',
      type: 'single',
      title: '您一周大约在员工餐厅就餐几次？',
      options: ['1-2 次', '3-4 次', '5 次以上', '从不在餐厅就餐'],
      required: true,
      order: 1,
    },
    {
      id: 'q_2',
      type: 'single',
      title: '您对餐厅整体环境的满意度如何？',
      options: ['非常满意', '满意', '一般', '不满意', '非常不满意'],
      required: true,
      order: 2,
    },
    {
      id: 'q_3',
      type: 'multi',
      title: '您最常选择的菜系是？（可多选）',
      options: ['家常菜', '轻食沙拉', '面食/汤粉', '特色窗口', '其他'],
      required: false,
      order: 3,
    },
    {
      id: 'q_4',
      type: 'single',
      title: '餐厅菜品价格与品质是否匹配？',
      options: ['非常匹配', '较匹配', '一般', '不匹配'],
      required: true,
      order: 4,
    },
    {
      id: 'q_5',
      type: 'text',
      title: '您对餐厅最满意的地方是？',
      options: [],
      required: false,
      order: 5,
    },
    {
      id: 'q_6',
      type: 'text',
      title: '您希望餐厅优先改进的方面是？',
      options: [],
      required: true,
      order: 6,
    },
  ]
}

// 从本地存储加载答案
function loadAnswersFromStorage() {
  try {
    const saved = localStorage.getItem(localStorageKey.value)
    if (saved) {
      answers.value = JSON.parse(saved)
    }
  } catch (err) {
    console.error('Failed to load answers from storage:', err)
  }
}

// 保存答案到本地存储
function saveAnswersToStorage() {
  try {
    localStorage.setItem(localStorageKey.value, JSON.stringify(answers.value))
  } catch (err) {
    console.error('Failed to save answers to storage:', err)
  }
}

// 处理单选题
function handleSingleChoice(questionId, option) {
  answers.value[questionId] = option
  validationErrors.value.delete(questionId)
  saveAnswersToStorage()
  
  // 自动滚动到下一题（可选）
  nextTick(() => {
    const currentCard = document.querySelector(`[data-question-id="${questionId}"]`)
    if (currentCard) {
      const nextCard = currentCard.nextElementSibling
      if (nextCard) {
        setTimeout(() => {
          nextCard.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }, 300)
      }
    }
  })
}

// 处理多选题
function handleMultiChoice(questionId, option) {
  if (!answers.value[questionId]) {
    answers.value[questionId] = []
  }
  
  const index = answers.value[questionId].indexOf(option)
  if (index > -1) {
    answers.value[questionId].splice(index, 1)
  } else {
    answers.value[questionId].push(option)
  }
  
  if (answers.value[questionId].length > 0) {
    validationErrors.value.delete(questionId)
  }
  
  saveAnswersToStorage()
}

// 处理填空题
function handleTextInput(questionId, value) {
  answers.value[questionId] = value
  if (value.trim()) {
    validationErrors.value.delete(questionId)
  }
  saveAnswersToStorage()
}

// 校验必填项
function validateAnswers() {
  const errors = new Set()
  
  survey.value.questions.forEach((q) => {
    if (q.required) {
      const answer = answers.value[q.id]
      if (!answer || (Array.isArray(answer) && answer.length === 0) || (typeof answer === 'string' && answer.trim() === '')) {
        errors.add(q.id)
      }
    }
  })
  
  validationErrors.value = errors
  return errors.size === 0
}

// 滚动到第一个错误题目
function scrollToFirstError() {
  if (validationErrors.value.size === 0) return
  
  const firstErrorId = Array.from(validationErrors.value)[0]
  const errorCard = document.querySelector(`[data-question-id="${firstErrorId}"]`)
  if (errorCard) {
    errorCard.scrollIntoView({ behavior: 'smooth', block: 'center' })
    errorCard.classList.add('shake')
    setTimeout(() => {
      errorCard.classList.remove('shake')
    }, 600)
  }
}

// 提交问卷
async function handleSubmit() {
  if (submitting.value) return
  
  // 校验必填项
  if (!validateAnswers()) {
    scrollToFirstError()
    return
  }
  
  submitting.value = true
  
  try {
    const duration = Math.round((Date.now() - startTime.value) / 1000)
    
    const payload = {
      survey_id: route.params.id,
      answers: Object.entries(answers.value).map(([questionId, value]) => ({
        question_id: questionId,
        value,
      })),
      duration_seconds: duration,
    }
    
    const res = await fetch(`/api/v1/surveys/${route.params.id}/fills`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    })
    
    if (!res.ok) {
      const errorData = await res.json()
      throw new Error(errorData.error || '提交失败')
    }
    
    // 清除本地存储
    localStorage.removeItem(localStorageKey.value)
    
    // 显示成功弹窗
    showSuccessModal.value = true
    
    // 3秒后跳转
    setTimeout(() => {
      router.push('/task-hall')
    }, 3000)
  } catch (err) {
    console.error('Failed to submit survey:', err)
    alert(err.message || '提交失败，请重试')
  } finally {
    submitting.value = false
  }
}

// 放弃填写
function handleAbandon() {
  if (Object.keys(answers.value).length === 0) {
    router.back()
    return
  }
  
  if (confirm('退出后进度将不被保存，确定离开吗？')) {
    localStorage.removeItem(localStorageKey.value)
    router.back()
  }
}

// 自动保存定时器
let autoSaveTimer = null

onMounted(() => {
  fetchSurvey()
  
  // 每30秒自动保存一次
  autoSaveTimer = setInterval(() => {
    saveAnswersToStorage()
  }, 30000)
})

onBeforeUnmount(() => {
  if (autoSaveTimer) {
    clearInterval(autoSaveTimer)
  }
  saveAnswersToStorage()
})
</script>

<template>
  <div class="survey-fill-page">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <p>加载问卷中...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-overlay">
      <div class="error-icon">⚠️</div>
      <h2>{{ error }}</h2>
      <button class="btn-secondary" @click="router.back()">返回</button>
    </div>

    <!-- 主内容区 -->
    <div v-else-if="survey" class="fill-container">
      <!-- 顶部进度条 -->
      <div class="progress-bar-container">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${progress}%` }"></div>
        </div>
      </div>

      <!-- 头部信息 -->
      <header class="survey-header">
        <h1 class="survey-title">{{ survey.title }}</h1>
        <p v-if="survey.description" class="survey-description">{{ survey.description }}</p>
        <div class="survey-meta">
          <span v-if="survey.estimated_minutes" class="meta-badge">
            ⏱ 预计 {{ survey.estimated_minutes }} 分钟
          </span>
          <span v-if="survey.reward_points" class="meta-badge reward">
            💰 +{{ survey.reward_points }} 积分
          </span>
        </div>
      </header>

      <!-- 题目卡片区 -->
      <main class="questions-container">
        <div
          v-for="(question, index) in survey.questions"
          :key="question.id"
          :data-question-id="question.id"
          :class="['question-card', { 'has-error': validationErrors.has(question.id) }]"
        >
          <!-- 题目标题 -->
          <div class="question-header">
            <span class="question-number">{{ index + 1 }}</span>
            <h3 class="question-title">
              <span v-if="question.required" class="required-mark">*</span>
              {{ question.title }}
            </h3>
          </div>

          <!-- 单选题 -->
          <div v-if="question.type === 'single'" class="question-body">
            <div
              v-for="option in question.options"
              :key="option"
              :class="['option-item', 'single-option', { active: answers[question.id] === option }]"
              @click="handleSingleChoice(question.id, option)"
            >
              <div class="option-radio">
                <div v-if="answers[question.id] === option" class="radio-checked"></div>
              </div>
              <span class="option-text">{{ option }}</span>
            </div>
          </div>

          <!-- 多选题 -->
          <div v-if="question.type === 'multi'" class="question-body">
            <div
              v-for="option in question.options"
              :key="option"
              :class="[
                'option-item',
                'multi-option',
                { active: answers[question.id]?.includes(option) },
              ]"
              @click="handleMultiChoice(question.id, option)"
            >
              <div class="option-checkbox">
                <svg
                  v-if="answers[question.id]?.includes(option)"
                  class="checkbox-icon"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="3"
                >
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
              </div>
              <span class="option-text">{{ option }}</span>
            </div>
          </div>

          <!-- 填空题 -->
          <div v-if="question.type === 'text'" class="question-body">
            <textarea
              :value="answers[question.id] || ''"
              @input="handleTextInput(question.id, $event.target.value)"
              class="text-input"
              placeholder="请输入您的回答..."
              rows="4"
            ></textarea>
          </div>

          <!-- 多项填空题 -->
          <div v-if="question.type === 'multi-text'" class="question-body">
            <div v-for="(label, idx) in question.options" :key="idx" class="multi-text-item">
              <label class="multi-text-label">{{ label }}</label>
              <input
                type="text"
                :value="(answers[question.id] || [])[idx] || ''"
                @input="
                  (e) => {
                    if (!answers[question.id]) answers[question.id] = []
                    answers[question.id][idx] = e.target.value
                    saveAnswersToStorage()
                  }
                "
                class="multi-text-input"
                placeholder="请输入..."
              />
            </div>
          </div>

          <!-- 错误提示 -->
          <div v-if="validationErrors.has(question.id)" class="error-hint">
            <span class="error-icon">⚠</span>
            <span>此题为必填项，请完成后再提交</span>
          </div>
        </div>
      </main>

      <!-- 底部操作区 -->
      <footer class="survey-footer">
        <button class="btn-abandon" @click="handleAbandon">放弃填写</button>
        <button class="btn-submit" @click="handleSubmit" :disabled="submitting">
          <span v-if="submitting">提交中...</span>
          <span v-else>提交问卷</span>
        </button>
      </footer>
    </div>

    <!-- 成功弹窗 -->
    <transition name="modal">
      <div v-if="showSuccessModal" class="success-modal-overlay">
        <div class="success-modal">
          <div class="success-animation">
            <div class="coin-rain">
              <span v-for="i in 15" :key="i" class="coin" :style="{ '--delay': `${i * 0.1}s` }">
                💰
              </span>
            </div>
            <div class="checkmark-circle">
              <svg class="checkmark" viewBox="0 0 52 52">
                <circle class="checkmark-circle-path" cx="26" cy="26" r="25" fill="none" />
                <path class="checkmark-check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8" />
              </svg>
            </div>
          </div>
          <h2 class="success-title">提交成功！</h2>
          <p class="success-message">感谢你的用心填答</p>
          <div class="success-reward">
            <span class="reward-text">+{{ survey.reward_points || 0 }} 积分</span>
            <span class="reward-sub">已存入账户</span>
          </div>
          <p class="success-redirect">即将返回任务大厅...</p>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
/* 全局容器 - 极简主义，蓝白色调 */
.survey-fill-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #e8f2ff 0%, #ffffff 100%);
  position: relative;
}

/* 加载状态 */
.loading-overlay,
.error-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  gap: 20px;
  padding: 24px;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e0e7ff;
  border-top: 4px solid #2665d4;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-icon {
  font-size: 64px;
}

.error-overlay h2 {
  font-size: 20px;
  color: #d32f2f;
  margin: 0;
}

.btn-secondary {
  padding: 10px 32px;
  background: #f0f4f8;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  color: #475569;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: #e2e8f0;
}

/* 主容器 */
.fill-container {
  max-width: 720px;
  margin: 0 auto;
  padding: 0 0 120px 0;
}

/* 顶部进度条 */
.progress-bar-container {
  position: sticky;
  top: 0;
  z-index: 100;
  background: #ffffff;
  padding: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.progress-bar {
  height: 4px;
  background: #e0e7ff;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #2665d4 0%, #4f8aff 100%);
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 头部信息 */
.survey-header {
  padding: 48px 24px 32px;
  text-align: center;
  background: #ffffff;
  margin-bottom: 24px;
}

.survey-title {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 16px 0;
  line-height: 1.4;
}

.survey-description {
  font-size: 16px;
  color: #64748b;
  line-height: 1.7;
  margin: 0 0 20px 0;
}

.survey-meta {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

.meta-badge {
  padding: 6px 16px;
  background: #f0f4f8;
  border-radius: 20px;
  font-size: 14px;
  color: #475569;
  font-weight: 500;
}

.meta-badge.reward {
  background: #fef3c7;
  color: #92400e;
}

/* 题目容器 */
.questions-container {
  padding: 0 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 题目卡片 */
.question-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  transition: all 0.3s;
  border: 2px solid transparent;
}

.question-card:hover {
  box-shadow: 0 4px 20px rgba(38, 101, 212, 0.08);
}

.question-card.has-error {
  border-color: #ef4444;
  animation: shake 0.5s;
}

@keyframes shake {
  0%,
  100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-8px);
  }
  75% {
    transform: translateX(8px);
  }
}

.question-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 24px;
}

.question-number {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #2665d4 0%, #4f8aff 100%);
  color: #ffffff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.question-title {
  flex: 1;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
  line-height: 1.6;
}

.required-mark {
  color: #ef4444;
  margin-right: 4px;
  font-size: 20px;
}

/* 选项样式 */
.question-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.option-item:hover {
  background: #f0f7ff;
  border-color: #bfdbfe;
}

.option-item.active {
  background: #eff6ff;
  border-color: #2665d4;
}

/* 单选框 */
.option-radio {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  border: 2px solid #cbd5e1;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.option-item.active .option-radio {
  border-color: #2665d4;
}

.radio-checked {
  width: 12px;
  height: 12px;
  background: #2665d4;
  border-radius: 50%;
  animation: popIn 0.2s;
}

@keyframes popIn {
  0% {
    transform: scale(0);
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
  }
}

/* 多选框 */
.option-checkbox {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  border: 2px solid #cbd5e1;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.option-item.active .option-checkbox {
  background: #2665d4;
  border-color: #2665d4;
}

.checkbox-icon {
  width: 14px;
  height: 14px;
  color: #ffffff;
  animation: popIn 0.2s;
}

.option-text {
  flex: 1;
  font-size: 16px;
  color: #334155;
  line-height: 1.5;
}

/* 填空题 */
.text-input {
  width: 100%;
  padding: 16px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 15px;
  color: #334155;
  line-height: 1.6;
  resize: vertical;
  font-family: inherit;
  transition: all 0.2s;
}

.text-input:focus {
  outline: none;
  border-color: #2665d4;
  background: #f8fafc;
}

.text-input::placeholder {
  color: #94a3b8;
}

/* 多项填空 */
.multi-text-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.multi-text-label {
  font-size: 14px;
  color: #64748b;
  font-weight: 500;
}

.multi-text-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  font-size: 15px;
  color: #334155;
  transition: all 0.2s;
}

.multi-text-input:focus {
  outline: none;
  border-color: #2665d4;
  background: #f8fafc;
}

/* 错误提示 */
.error-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 10px 14px;
  background: #fef2f2;
  border-left: 3px solid #ef4444;
  border-radius: 6px;
  font-size: 14px;
  color: #dc2626;
}

.error-icon {
  font-size: 16px;
}

/* 底部操作区 */
.survey-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #ffffff;
  padding: 20px 24px;
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.08);
  display: flex;
  justify-content: center;
  gap: 16px;
  z-index: 50;
}

.btn-abandon {
  padding: 12px 32px;
  background: transparent;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  color: #64748b;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-abandon:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.btn-submit {
  padding: 12px 48px;
  background: linear-gradient(135deg, #2665d4 0%, #4f8aff 100%);
  border: none;
  border-radius: 10px;
  color: #ffffff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(38, 101, 212, 0.3);
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(38, 101, 212, 0.4);
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* 成功弹窗 */
.success-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 24px;
}

.success-modal {
  background: #ffffff;
  border-radius: 24px;
  padding: 48px 40px;
  max-width: 420px;
  width: 100%;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: modalIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes modalIn {
  from {
    opacity: 0;
    transform: scale(0.8) translateY(20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

/* 成功动画 */
.success-animation {
  position: relative;
  margin-bottom: 24px;
}

.coin-rain {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.coin {
  position: absolute;
  font-size: 24px;
  animation: coinFall 1.5s ease-out forwards;
  opacity: 0;
  animation-delay: var(--delay);
  left: calc(50% + (var(--delay, 0) * 50px - 75px));
}

@keyframes coinFall {
  0% {
    opacity: 0;
    transform: translateY(-100px) rotate(0deg);
  }
  10% {
    opacity: 1;
  }
  80% {
    opacity: 1;
  }
  100% {
    opacity: 0;
    transform: translateY(150px) rotate(360deg);
  }
}

.checkmark-circle {
  width: 100px;
  height: 100px;
  margin: 0 auto;
}

.checkmark {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  stroke-width: 3;
  stroke: #22c55e;
  stroke-miterlimit: 10;
  animation: fillCircle 0.4s ease-in-out 0.4s forwards, scaleCircle 0.3s ease-in-out 0.9s both;
}

.checkmark-circle-path {
  stroke-dasharray: 166;
  stroke-dashoffset: 166;
  animation: strokeCircle 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;
}

.checkmark-check {
  transform-origin: 50% 50%;
  stroke-dasharray: 48;
  stroke-dashoffset: 48;
  animation: strokeCheck 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.8s forwards;
}

@keyframes strokeCircle {
  100% {
    stroke-dashoffset: 0;
  }
}

@keyframes strokeCheck {
  100% {
    stroke-dashoffset: 0;
  }
}

@keyframes fillCircle {
  100% {
    fill: #22c55e;
    fill-opacity: 0.1;
  }
}

@keyframes scaleCircle {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.success-title {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.success-message {
  font-size: 16px;
  color: #64748b;
  margin: 0 0 24px 0;
}

.success-reward {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 20px;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-radius: 16px;
  margin-bottom: 16px;
}

.reward-text {
  font-size: 32px;
  font-weight: 700;
  color: #92400e;
  animation: numberPop 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) 1s both;
}

@keyframes numberPop {
  0% {
    transform: scale(0);
  }
  100% {
    transform: scale(1);
  }
}

.reward-sub {
  font-size: 14px;
  color: #b45309;
  font-weight: 500;
}

.success-redirect {
  font-size: 14px;
  color: #94a3b8;
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .fill-container {
    padding: 0 0 100px 0;
  }

  .survey-header {
    padding: 32px 20px 24px;
  }

  .survey-title {
    font-size: 24px;
  }

  .questions-container {
    padding: 0 16px;
    gap: 20px;
  }

  .question-card {
    padding: 24px 20px;
  }

  .question-title {
    font-size: 16px;
  }

  .survey-footer {
    padding: 16px;
    flex-direction: column;
  }

  .btn-abandon,
  .btn-submit {
    width: 100%;
  }

  .success-modal {
    padding: 36px 24px;
  }
}
</style>
