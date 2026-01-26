<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const router = useRouter()
const route = useRoute()

const makeId = () => `q-${Date.now()}-${Math.floor(Math.random() * 10000)}`

const AI_TEMPLATES = [
  {
    key: 'cafeteria',
    title: '员工餐厅就餐满意度调查',
    description: '本问卷用于了解员工对餐厅服务的满意度，结果仅用于改进餐厅服务。',
    questions: [
      { type: 'single', title: '您一周大约在员工餐厅就餐几次？', options: ['1-2 次', '3-4 次', '5 次以上'], required: true },
      { type: 'single', title: '您对餐厅整体环境的满意度如何？', options: ['非常满意', '满意', '一般', '不满意'], required: true },
      { type: 'single', title: '餐厅菜品口味是否符合您的预期？', options: ['非常符合', '比较符合', '一般', '不符合'], required: true },
      { type: 'multi', title: '您最常选择的菜系是？', options: ['家常菜', '轻食沙拉', '面食/汤粉', '特色窗口'], required: false },
      { type: 'single', title: '餐厅菜品丰富度是否充足？', options: ['非常充足', '还可以', '一般', '不足'], required: true },
      { type: 'single', title: '菜品价格与品质是否匹配？', options: ['非常匹配', '较匹配', '一般', '不匹配'], required: true },
      { type: 'single', title: '餐厅排队时间是否可接受？', options: ['非常快', '较快', '一般', '过长'], required: true },
      { type: 'multi', title: '您希望餐厅增加哪些服务？', options: ['夜宵档', '自助称重', '移动支付', '健康营养标识'], required: false },
      { type: 'single', title: '餐厅工作人员服务态度如何？', options: ['非常好', '较好', '一般', '较差'], required: true },
      { type: 'single', title: '您对餐厅卫生情况的评价？', options: ['非常干净', '比较干净', '一般', '不满意'], required: true },
      { type: 'single', title: '餐厅座位充足度如何？', options: ['充足', '基本够用', '偏紧张'], required: false },
      { type: 'multi', title: '您更倾向于哪种用餐方式？', options: ['堂食', '打包', '外卖到工位'], required: false },
      { type: 'single', title: '餐厅营业时间是否满足需求？', options: ['完全满足', '基本满足', '不太满足'], required: true },
      { type: 'text', title: '您对餐厅最满意的地方是？', options: [], required: false },
      { type: 'text', title: '您希望餐厅优先改进的方面是？', options: [], required: false },
    ],
  },
  {
    key: 'training',
    title: '新员工培训体验调研',
    description: '请分享你对近期培训安排的反馈，我们将持续优化课程设计。',
    questions: [
      { type: 'single', title: '本次培训整体节奏是否合适？', options: ['非常合适', '较合适', '一般', '过快/过慢'], required: true },
      { type: 'multi', title: '你最喜欢的培训形式是？', options: ['现场讲授', '实操演练', '案例讨论', '线上学习'], required: false },
      { type: 'single', title: '培训内容与岗位需求匹配度如何？', options: ['非常匹配', '较匹配', '一般', '不匹配'], required: true },
      { type: 'single', title: '讲师答疑是否及时清晰？', options: ['非常清晰', '较清晰', '一般', '不清晰'], required: true },
      { type: 'single', title: '培训资料的可用性如何？', options: ['非常好', '较好', '一般', '需要改进'], required: true },
      { type: 'multi', title: '你希望补充哪些主题？', options: ['业务流程', '工具系统', '团队协作', '职业发展'], required: false },
      { type: 'text', title: '你在培训中遇到的最大困难是什么？', options: [], required: false },
      { type: 'text', title: '你对培训安排的建议是？', options: [], required: false },
    ],
  },
  {
    key: 'service',
    title: '会员服务体验反馈',
    description: '帮助我们了解会员服务体验，提升服务质量。',
    questions: [
      { type: 'single', title: '客服响应速度如何？', options: ['非常快', '较快', '一般', '较慢'], required: true },
      { type: 'single', title: '客服解决问题的效率如何？', options: ['非常高', '较高', '一般', '较低'], required: true },
      { type: 'multi', title: '你最常使用的会员权益是？', options: ['专属折扣', '优先客服', '会员活动', '积分兑换'], required: false },
      { type: 'single', title: '会员权益是否有吸引力？', options: ['非常有', '较有', '一般', '不足'], required: true },
      { type: 'text', title: '你希望增加哪些新的会员权益？', options: [], required: false },
      { type: 'text', title: '你对会员服务的整体评价？', options: [], required: false },
    ],
  },
]

const state = reactive({
  title: '未命名问卷',
  description: '',
  descriptionEditing: false,
  titleEditing: false,
  questions: [],
  lastSaved: null,
  outlineOpen: false,
  settingsOpen: false,
  addMenuOpen: false,
  saveModalOpen: false,
  showTemplateGuide: false,
  templateInput: '',
})

const formatTime = (value) => {
  if (!value) return ''
  const hours = `${value.getHours()}`.padStart(2, '0')
  const minutes = `${value.getMinutes()}`.padStart(2, '0')
  return `${hours}:${minutes} 已自动保存`
}

const lastSavedText = computed(() => formatTime(state.lastSaved))

const saveDraft = () => {
  const payload = {
    title: state.title,
    description: state.description,
    questions: state.questions,
  }
  sessionStorage.setItem('survey-autosave', JSON.stringify(payload))
  state.lastSaved = new Date()
}

let autosaveTimer

const setQuestions = (questions) => {
  state.questions = questions.map((question) => ({
    id: makeId(),
    required: false,
    isAi: true,
    ...question,
  }))
}

const loadDraft = () => {
  const raw = sessionStorage.getItem('survey-draft')
  if (raw) {
    try {
      const draft = JSON.parse(raw)
      state.title = draft.title || state.title
      state.description = draft.description || ''
      if (route.query.ai === '1') {
        const prompt = `${draft.prompt || ''}${draft.title || ''}`
        const matched =
          AI_TEMPLATES.find((item) => (prompt.includes('餐厅') ? item.key === 'cafeteria' : false)) ||
          AI_TEMPLATES.find((item) => (prompt.includes('培训') ? item.key === 'training' : false)) ||
          AI_TEMPLATES.find((item) => (prompt.includes('会员') ? item.key === 'service' : false))
        const fallback = matched || AI_TEMPLATES[0]
        setQuestions(fallback.questions)
        state.description = fallback.description
        return
      }
    } catch {
      state.title = state.title
    }
  }

  if (route.params.id) {
    state.title = '城市通勤满意度问卷'
    state.description = '本问卷用于了解城市通勤体验，请根据实际情况填写。'
    setQuestions([
      { type: 'single', title: '您常用的通勤方式是？', options: ['地铁', '公交', '自驾', '骑行'], required: true },
      { type: 'single', title: '通勤时间是否可接受？', options: ['非常可接受', '还可以', '一般', '不可接受'], required: true },
      { type: 'text', title: '您希望改善的通勤环节是？', options: [], required: false },
    ])
  }
}

onMounted(() => {
  loadDraft()
  autosaveTimer = setInterval(saveDraft, 2 * 60 * 1000)
})

onBeforeUnmount(() => {
  if (autosaveTimer) clearInterval(autosaveTimer)
})

const startTitleEdit = () => {
  state.titleEditing = true
  nextTick(() => {
    const input = document.querySelector('.title-input')
    if (input) input.focus()
  })
}

const stopTitleEdit = () => {
  state.titleEditing = false
  if (!state.title.trim()) {
    state.title = '未命名问卷'
  }
}

const startDescriptionEdit = () => {
  state.descriptionEditing = true
  nextTick(() => {
    const input = document.querySelector('.description-input')
    if (input) input.focus()
  })
}

const stopDescriptionEdit = () => {
  state.descriptionEditing = false
}

const createQuestion = (type) => {
  if (type === 'single' || type === 'multi') {
    return {
      id: makeId(),
      type,
      title: type === 'single' ? '单选题标题' : '多选题标题',
      options: ['选项1', '选项2'],
      required: true,
      isAi: false,
    }
  }
  if (type === 'multi-text') {
    return {
      id: makeId(),
      type,
      title: '多项填空题标题',
      options: ['填空1', '填空2'],
      required: false,
      isAi: false,
    }
  }
  return {
    id: makeId(),
    type,
    title: '填空题标题',
    options: [],
    required: false,
    isAi: false,
  }
}

const addQuestion = (type) => {
  state.questions.push(createQuestion(type))
  state.addMenuOpen = false
}

const removeQuestion = (id) => {
  state.questions = state.questions.filter((question) => question.id !== id)
}

const addOption = (question) => {
  question.options.push(`选项${question.options.length + 1}`)
  question.isAi = false
}

const removeOption = (question, index) => {
  question.options.splice(index, 1)
  question.isAi = false
}

const markEdited = (question) => {
  question.isAi = false
}

const openSaveModal = () => {
  state.saveModalOpen = true
  saveDraft()
}

const closeSaveModal = () => {
  state.saveModalOpen = false
}

const publishSurvey = () => {
  state.saveModalOpen = false
  router.push({ name: 'survey-management', query: { publish: '1' } })
}

const openOutline = () => {
  state.outlineOpen = !state.outlineOpen
  state.settingsOpen = false
}

const openSettings = () => {
  state.settingsOpen = !state.settingsOpen
  state.outlineOpen = false
}

const handleBack = () => {
  const hasContent = state.questions.length > 0 || state.title !== '未命名问卷' || state.description.trim()
  if (hasContent) {
    const confirm = window.confirm('离开当前页面将失去未保存的内容，确认返回任务大厅吗？')
    if (!confirm) return
  }
  router.push('/')
}

const toggleTemplateGuide = () => {
  state.showTemplateGuide = !state.showTemplateGuide
  if (state.showTemplateGuide && !state.templateInput) {
    state.templateInput = `请按以下格式填写，系统将自动生成问卷：

【问卷主题】：例如：大学生消费习惯调研
【目标人群】：例如：本校大一至大四学生
【问题数量】：例如：8-12道题
【问卷类型】：例如：消费偏好/学习习惯/服务反馈/其他
【关键问题】：例如：
1. 每月生活费多少？
2. 主要消费项目是什么？
3. 是否有理财习惯？

【特殊要求】（可选）：例如：需要包含多选题、填空题等`
  }
}

const generateFromTemplate = () => {
  const input = state.templateInput.trim()
  if (!input) {
    alert('请先填写模板内容')
    return
  }

  // 提取模板信息
  const themeMatch = input.match(/【问卷主题】[:：]\s*(.+)/)
  const targetMatch = input.match(/【目标人群】[:：]\s*(.+)/)
  const questionsMatch = input.match(/【关键问题】[:：]\s*([\s\S]+?)(?=【|$)/)

  // 设置标题和描述
  if (themeMatch) {
    state.title = themeMatch[1].trim()
  }
  if (targetMatch) {
    state.description = `针对${targetMatch[1].trim()}的问卷调研`
  }

  // 生成问题
  const questions = []
  if (questionsMatch) {
    const keyQuestions = questionsMatch[1].trim().split('\n').filter(line => line.trim() && /^\d+\./.test(line.trim()))
    keyQuestions.forEach((q, idx) => {
      const questionText = q.replace(/^\d+\.\s*/, '').trim()
      if (questionText) {
        let type = 'single'
        if (questionText.includes('多少') || questionText.includes('填写') || questionText.includes('简述')) {
          type = 'text'
        } else if (questionText.includes('多选') || questionText.includes('全部')) {
          type = 'multi'
        }

        questions.push({
          id: makeId(),
          type: type,
          title: questionText,
          options: type === 'text' ? [] : ['选项1', '选项2', '选项3', '选项4'],
          required: idx < 3,
          isAi: true
        })
      }
    })
  }

  if (questions.length === 0) {
    for (let i = 0; i < 5; i++) {
      questions.push({
        id: makeId(),
        type: i % 3 === 0 ? 'multi' : (i % 3 === 1 ? 'single' : 'text'),
        title: `问题${i + 1}：请根据实际需求修改`,
        options: i % 3 === 2 ? [] : ['选项1', '选项2', '选项3'],
        required: i < 3,
        isAi: true
      })
    }
  }

  state.questions = questions
  state.showTemplateGuide = false
  saveDraft()
  alert(`已成功生成 ${questions.length} 道问题，请根据需要继续编辑`)
}

const scrollToQuestion = (id) => {
  const element = document.getElementById(id)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}
</script>

<template>
  <div class="builder-shell">
    <header class="builder-header">
      <div>
        <button class="back" type="button" @click="handleBack">
          ← 返回任务大厅
        </button>
        <div class="title-block">
          <button v-if="!state.titleEditing" class="title-display" type="button" @click="startTitleEdit">
            {{ state.title }}
          </button>
          <input
            v-else
            v-model="state.title"
            class="title-input"
            type="text"
            @blur="stopTitleEdit"
          />
          <span class="status-pill">自动保存</span>
        </div>
      </div>
      <div class="header-actions">
        <button class="ghost-button" type="button">预览</button>
        <button class="primary-button" type="button" @click="openSaveModal">保存</button>
      </div>
    </header>

    <section class="description-area">
      <p class="section-title">问卷说明</p>
      <button
        v-if="!state.descriptionEditing && !state.description"
        class="description-placeholder"
        type="button"
        @click="startDescriptionEdit"
      >
        添加问卷说明
      </button>
      <div v-else class="description-edit">
        <textarea
          v-model="state.description"
          class="description-input"
          rows="3"
          placeholder="请输入问卷说明，将同步到任务大厅副标题"
          @blur="stopDescriptionEdit"
          @input="saveDraft"
        ></textarea>
        <button class="ghost-button small" type="button" @click="stopDescriptionEdit">完成</button>
      </div>
    </section>

    <main class="question-area">
      <div v-if="state.questions.length === 0" class="empty-state">
        <p>点击下方 + 号，开始你的第一道题</p>
        <button class="template-guide-btn" type="button" @click="toggleTemplateGuide">
          📝 或使用文字模板快速生成
        </button>
      </div>

      <!-- 模板引导面板 -->
      <div v-if="state.showTemplateGuide" class="template-guide-panel">
        <div class="template-guide-header">
          <h3>🎯 文字模板引导</h3>
          <button class="close-btn" type="button" @click="state.showTemplateGuide = false">×</button>
        </div>
        <div class="template-guide-content">
          <p class="guide-hint">
            ✨ 请按照以下格式填写，系统将自动为您生成问卷框架
          </p>
          <textarea
            v-model="state.templateInput"
            class="template-textarea"
            rows="18"
            placeholder="模板将自动加载..."
          ></textarea>
          <div class="template-actions">
            <button class="ghost-button" type="button" @click="state.showTemplateGuide = false">取消</button>
            <button class="primary-button" type="button" @click="generateFromTemplate">生成问卷</button>
          </div>
        </div>
      </div>

      <div v-for="(question, index) in state.questions" :id="question.id" :key="question.id" class="question-card">
        <header class="question-header">
          <div class="question-index">Q{{ index + 1 }}</div>
          <div class="question-meta">
            <span v-if="question.isAi" class="ai-tag">AI 生成</span>
            <span class="question-type">{{ question.type === 'single' ? '单选题' : question.type === 'multi' ? '多选题' : question.type === 'multi-text' ? '多项填空题' : '填空题' }}</span>
          </div>
          <button class="delete-button" type="button" @click="removeQuestion(question.id)">删除</button>
        </header>

        <textarea
          v-model="question.title"
          class="question-title"
          rows="2"
          placeholder="请输入题干"
          @input="markEdited(question)"
        ></textarea>

        <div v-if="question.type === 'single' || question.type === 'multi'" class="option-list">
          <div v-for="(option, optionIndex) in question.options" :key="`${question.id}-opt-${optionIndex}`" class="option-row">
            <span class="option-index">{{ optionIndex + 1 }}</span>
            <input
              v-model="question.options[optionIndex]"
              class="option-input"
              type="text"
              @input="markEdited(question)"
            />
            <button class="icon-button" type="button" @click="removeOption(question, optionIndex)">-</button>
          </div>
          <button class="ghost-button small" type="button" @click="addOption(question)">+ 添加选项</button>
        </div>

        <div v-if="question.type === 'multi-text'" class="option-list">
          <div v-for="(option, optionIndex) in question.options" :key="`${question.id}-text-${optionIndex}`" class="option-row">
            <span class="option-index">{{ optionIndex + 1 }}</span>
            <input
              v-model="question.options[optionIndex]"
              class="option-input"
              type="text"
              @input="markEdited(question)"
            />
            <button class="icon-button" type="button" @click="removeOption(question, optionIndex)">-</button>
          </div>
          <button class="ghost-button small" type="button" @click="addOption(question)">+ 添加填空</button>
        </div>

        <div v-if="question.type === 'text'" class="text-hint">填答者将输入简答内容</div>

        <div class="question-footer">
          <label class="switch">
            <input v-model="question.required" type="checkbox" @change="markEdited(question)" />
            <span class="switch-track"></span>
            <span class="switch-label">必填</span>
          </label>
        </div>
      </div>
    </main>

    <div class="toolbar">
      <div class="toolbar-left">
        <button class="ghost-button small" type="button" @click="openOutline">大纲</button>
        <button class="ghost-button small" type="button" @click="openSettings">设置</button>
        <span class="autosave-text">{{ lastSavedText }}</span>
      </div>
      <div class="toolbar-right">
        <div class="add-menu">
          <button class="add-button" type="button" @click="state.addMenuOpen = !state.addMenuOpen">+</button>
          <div v-if="state.addMenuOpen" class="add-panel">
            <button class="add-item" type="button" @click="addQuestion('single')">单选题</button>
            <button class="add-item" type="button" @click="addQuestion('multi')">多选题</button>
            <button class="add-item" type="button" @click="addQuestion('text')">填空题</button>
            <button class="add-item" type="button" @click="addQuestion('multi-text')">多项填空题</button>
            <button class="add-item disabled" type="button" disabled>评分题（预留）</button>
            <button class="add-item disabled" type="button" disabled>排序题（预留）</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="state.outlineOpen" class="side-panel">
      <div class="panel-header">
        <h3>问卷大纲</h3>
        <button class="ghost-button small" type="button" @click="state.outlineOpen = false">关闭</button>
      </div>
      <div class="panel-body">
        <button
          v-for="(question, index) in state.questions"
          :key="`${question.id}-outline`"
          class="outline-item"
          type="button"
          @click="scrollToQuestion(question.id)"
        >
          Q{{ index + 1 }} {{ question.title || '未命名题目' }}
        </button>
      </div>
    </div>

    <div v-if="state.settingsOpen" class="side-panel">
      <div class="panel-header">
        <h3>问卷设置</h3>
        <button class="ghost-button small" type="button" @click="state.settingsOpen = false">关闭</button>
      </div>
      <div class="panel-body settings">
        <label class="settings-item">
          <span>逻辑跳题</span>
          <input type="checkbox" disabled />
        </label>
        <label class="settings-item">
          <span>提交后提示文案</span>
          <input type="text" placeholder="感谢填写" disabled />
        </label>
        <p class="settings-hint">逻辑设置与高级选项将在后续版本开放。</p>
      </div>
    </div>
  </div>

  <div v-if="state.saveModalOpen" class="modal-backdrop" @click.self="closeSaveModal">
    <div class="modal">
      <h3>问卷保存成功，是否立即发布？</h3>
      <p>发布后将进入问卷管理并进行积分结算确认。</p>
      <div class="modal-actions">
        <button class="ghost-button" type="button" @click="closeSaveModal">继续编辑</button>
        <button class="primary-button" type="button" @click="publishSurvey">发布调查</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.builder-shell {
  min-height: 100vh;
  padding: 48px;
  background: radial-gradient(circle at top left, #edf3ff 0%, #f7f9ff 45%, #ffffff 100%);
}

header {
  display: grid;
  gap: 28px;
  position: relative;
}

.builder-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.back {
  color: #1e4fb4;
  font-weight: 600;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 15px;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.back:hover {
  background: rgba(30, 79, 180, 0.1);
  transform: translateX(-2px);
}

.title-block {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.title-display {
  font-family: 'Newsreader', serif;
  font-size: 28px;
  color: #0e2a55;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}

.title-input {
  font-family: 'Newsreader', serif;
  font-size: 26px;
  padding: 6px 10px;
  border-radius: 12px;
  border: 1px solid #d4e1f6;
}

.status-pill {
  padding: 6px 12px;
  background: #f2f6ff;
  color: #1e4fb4;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.ghost-button,
.primary-button {
  padding: 10px 18px;
  border-radius: 14px;
  font-weight: 600;
  cursor: pointer;
  border: none;
}

.ghost-button {
  background: #ffffff;
  border: 1px solid rgba(26, 59, 127, 0.2);
  color: #1a3b7f;
}

.ghost-button.small {
  padding: 6px 12px;
  font-size: 12px;
}

.primary-button {
  background: linear-gradient(135deg, #2665d4, #4f80f1);
  color: #ffffff;
}

.description-area {
  background: #ffffff;
  border-radius: 20px;
  padding: 20px 24px;
  box-shadow: var(--color-shadow);
  display: grid;
  gap: 12px;
}

.section-title {
  font-weight: 600;
  color: #1a3b7f;
}

.description-placeholder {
  text-align: left;
  color: #8a9ab2;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
}

.description-edit {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.description-input {
  width: 100%;
  border-radius: 14px;
  border: 1px solid #d4e1f6;
  padding: 12px;
  resize: vertical;
}

.question-area {
  display: grid;
  gap: 18px;
}

.empty-state {
  padding: 50px;
  text-align: center;
  border-radius: 20px;
  border: 2px dashed #c8d6ee;
  color: #7b8da7;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: center;
}

.template-guide-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #4f80f1, #2665d4);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(38, 101, 212, 0.2);
}

.template-guide-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(38, 101, 212, 0.3);
}

.template-guide-panel {
  background: white;
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 8px 24px rgba(13, 27, 55, 0.12);
  border: 2px solid #e6effa;
  margin-bottom: 24px;
}

.template-guide-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid #e6effa;
}

.template-guide-header h3 {
  margin: 0;
  font-size: 20px;
  color: #0d1b37;
  font-weight: 700;
}

.close-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: #f1f2f6;
  color: #5a6579;
  font-size: 24px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: #ef4444;
  color: white;
}

.template-guide-content {
  display: grid;
  gap: 16px;
}

.guide-hint {
  margin: 0;
  padding: 12px 16px;
  background: #f0f7ff;
  border-left: 4px solid #2665d4;
  border-radius: 8px;
  color: #1a3b7f;
  font-size: 14px;
  line-height: 1.6;
}

.template-textarea {
  width: 100%;
  padding: 20px;
  border: 2px solid #d8e4f4;
  border-radius: 16px;
  font-size: 15px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  line-height: 2;
  color: #0d1b37;
  background: linear-gradient(to bottom, #ffffff, #f9fbff);
  resize: vertical;
  min-height: 450px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(13, 27, 55, 0.04);
}

.template-textarea:focus {
  outline: none;
  border-color: #2665d4;
  box-shadow: 0 0 0 4px rgba(38, 101, 212, 0.12), 0 4px 16px rgba(13, 27, 55, 0.08);
  background: white;
  transform: translateY(-1px);
}

.template-textarea::placeholder {
  color: #a0b0cc;
  font-style: italic;
}

.template-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.question-card {
  background: #ffffff;
  border-radius: 22px;
  padding: 22px;
  box-shadow: var(--color-shadow);
  display: grid;
  gap: 14px;
  animation: fadeIn 0.4s ease;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.question-index {
  font-weight: 700;
  color: #1e4fb4;
}

.question-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.ai-tag {
  background: rgba(38, 101, 212, 0.15);
  color: #1e4fb4;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  animation: pulse 2s infinite;
}

.question-type {
  font-size: 12px;
  color: #6b7b94;
}

.delete-button {
  background: none;
  border: none;
  color: #ef4444;
  font-weight: 600;
  cursor: pointer;
}

.question-title {
  width: 100%;
  border-radius: 14px;
  border: 1px solid #d4e1f6;
  padding: 12px;
  resize: vertical;
}

.option-list {
  display: grid;
  gap: 10px;
}

.option-row {
  display: grid;
  grid-template-columns: 26px 1fr 32px;
  align-items: center;
  gap: 10px;
}

.option-index {
  background: #eef4ff;
  color: #1e4fb4;
  width: 26px;
  height: 26px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  font-size: 12px;
}

.option-input {
  border-radius: 12px;
  border: 1px solid #d4e1f6;
  padding: 8px 10px;
}

.icon-button {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  border: 1px solid #d4e1f6;
  background: #ffffff;
  cursor: pointer;
}

.text-hint {
  font-size: 12px;
  color: #8a9ab2;
}

.question-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.switch {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.switch input {
  display: none;
}

.switch-track {
  width: 38px;
  height: 20px;
  border-radius: 999px;
  background: #d8e4f4;
  position: relative;
  transition: background 0.2s ease;
}

.switch-track::after {
  content: '';
  position: absolute;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #ffffff;
  top: 3px;
  left: 3px;
  transition: transform 0.2s ease;
  box-shadow: 0 3px 6px rgba(16, 35, 63, 0.2);
}

.switch input:checked + .switch-track {
  background: #2665d4;
}

.switch input:checked + .switch-track::after {
  transform: translateX(18px);
}

.switch-label {
  font-size: 12px;
  color: #5a7395;
}

.toolbar {
  position: fixed;
  left: 40px;
  right: 40px;
  bottom: 24px;
  background: #ffffff;
  border-radius: 18px;
  box-shadow: 0 20px 40px rgba(16, 35, 63, 0.12);
  padding: 12px 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 20;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.autosave-text {
  font-size: 12px;
  color: #8a9ab2;
}

.add-menu {
  position: relative;
}

.add-button {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  border: none;
  background: linear-gradient(135deg, #2665d4, #4f80f1);
  color: #ffffff;
  font-size: 24px;
  cursor: pointer;
}

.add-panel {
  position: absolute;
  right: 0;
  bottom: 54px;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(16, 35, 63, 0.12);
  padding: 12px;
  display: grid;
  grid-template-columns: repeat(2, minmax(120px, 1fr));
  gap: 10px;
}

.add-item {
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid #d4e1f6;
  background: #f7faff;
  color: #1a3b7f;
  font-size: 12px;
  cursor: pointer;
}

.add-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.side-panel {
  position: fixed;
  left: 40px;
  bottom: 90px;
  width: min(320px, 90vw);
  background: #ffffff;
  border-radius: 18px;
  box-shadow: 0 20px 40px rgba(16, 35, 63, 0.12);
  padding: 16px;
  display: grid;
  gap: 12px;
  z-index: 25;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-body {
  display: grid;
  gap: 10px;
  max-height: 260px;
  overflow: auto;
}

.outline-item {
  background: #f7faff;
  border: 1px solid #d4e1f6;
  border-radius: 12px;
  padding: 8px 10px;
  text-align: left;
  cursor: pointer;
  font-size: 12px;
}

.settings {
  gap: 12px;
}

.settings-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: #5a7395;
}

.settings-item input[type='text'] {
  flex: 1;
  padding: 6px 8px;
  border-radius: 10px;
  border: 1px solid #d4e1f6;
}

.settings-hint {
  font-size: 12px;
  color: #8a9ab2;
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
  width: min(380px, 90vw);
  box-shadow: 0 20px 50px rgba(13, 27, 55, 0.25);
  display: grid;
  gap: 16px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(38, 101, 212, 0.4);
  }
  70% {
    box-shadow: 0 0 0 8px rgba(38, 101, 212, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(38, 101, 212, 0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 960px) {
  .builder-shell {
    padding: 24px 24px 120px;
  }

  .toolbar {
    left: 20px;
    right: 20px;
  }
}

@media (max-width: 720px) {
  .builder-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .toolbar {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .add-panel {
    right: auto;
    left: 0;
  }

  .side-panel {
    left: 20px;
  }
}
</style>
