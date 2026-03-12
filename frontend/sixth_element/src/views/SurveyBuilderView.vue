<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { aiGenerateDraftQuestions, createSurveyDraft } from '../utils/surveyManagementApi'

const route = useRoute()

const aiGenerating = ref(false)

const makeId = () => `q-${Date.now()}-${Math.floor(Math.random() * 10000)}`

// 拖拽排序相关
const dragState = ref({
  dragging: false,
  dragIndex: null,
  dropIndex: null
})

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

// 默认模板内容
const DEFAULT_TEMPLATE = `【问卷主题】：
【目标人群】：
【问题数量】：
【问卷类型】：
【关键问题】：
1. 
2. 
3. 

【特殊要求】：`

// 示例内容
const DEFAULT_EXAMPLE = `【问卷主题】：大学生消费习惯调研
【目标人群】：本校大一至大四学生
【问题数量】：8-12道题
【问卷类型】：消费偏好
【关键问题】：
1. 每月生活费多少？
2. 主要消费项目是什么？
3. 是否有理财习惯？
4. 最常用的支付方式？

【特殊要求】：需要包含多选题、填空题`

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
  templateInput: DEFAULT_TEMPLATE,
  exampleInput: DEFAULT_EXAMPLE,
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

const normalizeQuestions = (questions) => {
  return questions.map((question, index) => {
    const type = (question.type || 'text').toLowerCase()
    const options = Array.isArray(question.options) ? question.options : []
    const required = typeof question.required === 'boolean' ? question.required : false
    const isAi = typeof question.is_ai === 'boolean' ? question.is_ai : (question.isAi ?? true)
    return {
      id: question.id || makeId(),
      type,
      title: question.title || `问题${index + 1}`,
      options: type === 'text' ? [] : options,
      required,
      isAi,
    }
  })
}

const setQuestions = (questions) => {
  state.questions = normalizeQuestions(questions)
}

const loadDraft = () => {
  const raw = sessionStorage.getItem('survey-draft')
  if (raw) {
    try {
      const draft = JSON.parse(raw)
      state.title = draft.title || state.title
      state.description = draft.description || ''
      if (route.query.ai === '1' && Array.isArray(draft.questions) && draft.questions.length > 0) {
        setQuestions(draft.questions)
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
    const confirm = window.confirm('离开当前页面将失去未保存的内容，确认返回吗？')
    if (!confirm) return
  }
  router.back()
}

const toggleTemplateGuide = () => {
  state.showTemplateGuide = !state.showTemplateGuide
}

// 拖拽排序相关函数
const handleDragStart = (index) => {
  dragState.value.dragging = true
  dragState.value.dragIndex = index
}

const handleDragOver = (e, index) => {
  e.preventDefault()
  dragState.value.dropIndex = index
}

const handleDragEnd = () => {
  if (dragState.value.dragIndex !== null && dragState.value.dropIndex !== null && dragState.value.dragIndex !== dragState.value.dropIndex) {
    const questions = [...state.questions]
    const [removed] = questions.splice(dragState.value.dragIndex, 1)
    questions.splice(dragState.value.dropIndex, 0, removed)
    state.questions = questions
    saveDraft()
  }
  dragState.value.dragging = false
  dragState.value.dragIndex = null
  dragState.value.dropIndex = null
}

// 移动端触摸拖拽
let touchStartY = 0
let touchElement = null
let touchIndex = null

const handleTouchStart = (e, index) => {
  touchStartY = e.touches[0].clientY
  touchElement = e.target.closest('.question-card')
  touchIndex = index
  if (touchElement) {
    touchElement.classList.add('dragging-touch')
  }
}

const handleTouchMove = (e) => {
  if (touchElement && touchIndex !== null) {
    const touch = e.touches[0]
    const cards = document.querySelectorAll('.question-card')
    cards.forEach((card, i) => {
      if (i !== touchIndex) {
        const rect = card.getBoundingClientRect()
        if (touch.clientY > rect.top && touch.clientY < rect.bottom) {
          dragState.value.dropIndex = i
        }
      }
    })
  }
}

const handleTouchEnd = () => {
  if (touchElement) {
    touchElement.classList.remove('dragging-touch')
  }
  if (touchIndex !== null && dragState.value.dropIndex !== null && touchIndex !== dragState.value.dropIndex) {
    const questions = [...state.questions]
    const [removed] = questions.splice(touchIndex, 1)
    questions.splice(dragState.value.dropIndex, 0, removed)
    state.questions = questions
    saveDraft()
  }
  touchElement = null
  touchIndex = null
  dragState.value.dropIndex = null
}

const generateFromTemplate = async () => {
  const input = state.templateInput.trim()
  if (!input) {
    alert('请先填写模板内容')
    return
  }

  // 提取模板信息
  const themeMatch = input.match(/【问卷主题】[:：]\s*(.+)/)
  const targetMatch = input.match(/【目标人群】[:：]\s*(.+)/)

  if (themeMatch) {
    state.title = themeMatch[1].trim()
  }
  if (targetMatch) {
    state.description = `针对${targetMatch[1].trim()}的问卷调研`
  }

  aiGenerating.value = true
  try {
    const draftRaw = sessionStorage.getItem('survey-draft')
    const storedDraft = draftRaw ? JSON.parse(draftRaw) : {}
    let draftId = storedDraft.id
    if (!draftId) {
      const created = await createSurveyDraft({
        title: state.title || '未命名问卷',
        subtitle: state.description || '',
      })
      draftId = created.id
    }

    const questionCount = parseQuestionCount(input)
    const generated = await aiGenerateDraftQuestions(draftId, {
      prompt: input,
      question_count: questionCount,
    })

    const normalized = normalizeQuestions(generated.questions || [])
    state.questions = normalized
    state.showTemplateGuide = false
    sessionStorage.setItem(
      'survey-draft',
      JSON.stringify({
        ...storedDraft,
        id: draftId,
        title: state.title,
        description: state.description,
        prompt: input,
        questions: normalized,
        source: 'ai',
      }),
    )
    saveDraft()
    alert(`已成功生成 ${normalized.length} 道问题，请根据需要继续编辑`)
  } catch (error) {
    alert(error?.message || 'AI 生成失败，请稍后重试')
  } finally {
    aiGenerating.value = false
  }
}

const scrollToQuestion = (id) => {
  const element = document.getElementById(id)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

// 重置模板内容
const resetTemplate = () => {
  state.templateInput = DEFAULT_TEMPLATE
}

const parseQuestionCount = (input) => {
  const match = input.match(/【问题数量】[:：]\s*(\d+)/)
  if (!match) return 10
  const parsed = parseInt(match[1], 10)
  return Number.isNaN(parsed) || parsed <= 0 ? 10 : parsed
}
</script>

<template>
  <div class="builder-shell">
    <!-- 返回按钮 - 单独在左上角 -->
    <div class="back-btn-container">
      <button class="back-btn" type="button" @click="handleBack">
        ← 返回
      </button>
    </div>

    <!-- 问卷制作 设定标题区域 -->
    <header class="builder-header">
      <div class="header-main">
        <h1 class="page-title">问卷制作</h1>
        <div class="title-block">
          <span class="title-label">问卷标题：</span>
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
    </header>

    <!-- AI生成模板区域 - 移到页面中上方 -->
    <section v-if="state.questions.length === 0" class="ai-template-section">
      <div class="ai-template-header">
        <h2>🎯 用 AI 生成问卷草案</h2>
        <p class="ai-hint">在左侧描述需求，或参考右侧示例进行修改</p>
      </div>
      
      <div class="ai-template-content">
        <!-- 左侧: 可编辑的需求描述 -->
        <div class="template-edit-area">
          <h3>📝 描述你的需求</h3>
          <textarea
            v-model="state.templateInput"
            class="template-textarea"
            rows="16"
            placeholder="在这里填写你的问卷需求..."
          ></textarea>
          <div class="template-actions">
            <button class="ghost-button small" type="button" @click="resetTemplate">
              🔄 重置
            </button>
            <button class="primary-button" type="button" :disabled="aiGenerating" @click="generateFromTemplate">
              {{ aiGenerating ? '生成中...' : '✨ 生成问卷' }}
            </button>
          </div>
        </div>

        <!-- 右侧: 只读的案例引导 -->
        <div class="template-example-area">
          <h3>📖 案例引导</h3>
          <textarea
            v-model="state.exampleInput"
            class="template-textarea"
            rows="8"
            placeholder="参考示例，可直接修改..."
            readonly
          ></textarea>
          <div class="template-actions">
            <button class="ghost-button small" type="button" @click="state.templateInput = state.exampleInput">
              ← 复制到左侧
            </button>
          </div>
        </div>
      </div>
    </section>

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
      <div v-if="state.questions.length === 0 && !state.showTemplateGuide" class="empty-state">
        <p>点击下方 + 号，手动添加题目</p>
        <p class="empty-hint">或使用上方 AI 功能快速生成问卷</p>
      </div>

      <div 
        v-for="(question, index) in state.questions" 
        :id="question.id" 
        :key="question.id" 
        class="question-card"
        :class="{ 
          'dragging': dragState.dragIndex === index,
          'drop-target': dragState.dropIndex === index && dragState.dragIndex !== index
        }"
        draggable="true"
        @dragstart="handleDragStart(index)"
        @dragover="handleDragOver($event, index)"
        @dragend="handleDragEnd"
        @touchstart="handleTouchStart($event, index)"
        @touchmove="handleTouchMove"
        @touchend="handleTouchEnd"
      >
        <header class="question-header">
          <div class="drag-handle" title="拖拽排序">⋮⋮</div>
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

    <!-- 底部控制台 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <button class="ghost-button small" type="button" @click="openOutline">📋 大纲</button>
        <button class="ghost-button small" type="button" @click="openSettings">⚙️ 设置</button>
        <span class="autosave-text">{{ lastSavedText }}</span>
      </div>
      <div class="toolbar-right">
        <button class="ghost-button" type="button">预览</button>
        <button class="primary-button" type="button" @click="openSaveModal">保存</button>
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
  </div>
</template>

<style scoped>
.builder {
  min-height: 100vh;
  padding: 32px 48px 120px 80px;
  background: radial-gradient(circle at top left, #edf3ff 0%, #f7f9ff 45%, #ffffff 100%);
}

.builder-header {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px 0;
  margin-top: 0;
}

/* 返回按钮容器 */
.back-btn-container {
  display: flex;
  padding: 12px 0;
  margin-bottom: 12px;
}

.back-btn {
  color: #1e4fb4;
  font-weight: 600;
  background: #ffffff;
  border: 2px solid #1e4fb4;
  cursor: pointer;
  font-size: 14px;
  padding: 8px 14px;
  border-radius: 10px;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  box-shadow: 0 2px 8px rgba(16, 35, 63, 0.1);
  white-space: nowrap;
}

.back-btn:hover {
  background: #f2f6ff;
  transform: translateX(-2px);
  box-shadow: 0 4px 12px rgba(16, 35, 63, 0.15);
}

header {
  display: grid;
  gap: 20px;
  position: relative;
}

.builder-header {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px 0;
  margin-top: 40px;
}

.header-main {
  text-align: center;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  color: #0d1b37;
  margin: 0 0 16px 0;
  font-family: 'Newsreader', serif;
}

.title-block {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.title-label {
  font-size: 16px;
  color: #5a7395;
  font-weight: 500;
}

.title-display {
  font-family: 'Newsreader', serif;
  font-size: 24px;
  color: #1e4fb4;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.title-display:hover {
  background: rgba(30, 79, 180, 0.1);
}

.title-input {
  font-family: 'Newsreader', serif;
  font-size: 22px;
  padding: 8px 12px;
  border-radius: 12px;
  border: 2px solid #2665d4;
  min-width: 280px;
}

.status-pill {
  padding: 6px 12px;
  background: #f2f6ff;
  color: #1e4fb4;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

/* AI模板区域 */
.ai-template-section {
  background: linear-gradient(135deg, #ffffff, #f8faff);
  border-radius: 24px;
  padding: 32px;
  box-shadow: 0 8px 32px rgba(13, 27, 55, 0.08);
  border: 2px solid #e6effa;
  margin-bottom: 24px;
}

.ai-template-header {
  text-align: center;
  margin-bottom: 28px;
}

.ai-template-header h2 {
  font-size: 24px;
  font-weight: 700;
  color: #0d1b37;
  margin: 0 0 8px 0;
}

.ai-hint {
  color: #5a7395;
  font-size: 14px;
  margin: 0;
}

.ai-template-content {
  display: grid;
  grid-template-columns: 2fr 0.7fr;
  gap: 24px;
}

.template-edit-area,
.template-example-area {
  background: #ffffff;
  border-radius: 16px;
  padding: 20px;
  border: 1px solid #e6effa;
}

.template-example-area {
  padding: 16px;
}

.template-edit-area h3,
.template-example-area h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1a3b7f;
  margin: 0 0 16px 0;
}

.template-example-area h3 {
  font-size: 14px;
  margin: 0 0 12px 0;
}

.template-textarea {
  width: 100%;
  padding: 16px;
  border: 2px solid #2665d4;
  border-radius: 12px;
  font-size: 14px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  line-height: 1.8;
  color: #0d1b37;
  background: #ffffff;
  resize: vertical;
  min-height: 320px;
  transition: all 0.3s ease;
  cursor: text;
}

.template-example-area .template-textarea {
  min-height: 400px;
  border: 1px dashed #d4e1f6;
  background: #f5f8fc;
  opacity: 0.8;
  cursor: default;
  resize: none;
  overflow: auto;
}

.template-textarea:focus {
  outline: none;
  border-color: #1e4fb4;
  box-shadow: 0 0 0 4px rgba(38, 101, 212, 0.15);
  background: #ffffff;
}

.template-actions {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
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

.primary-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(38, 101, 212, 0.3);
}

.description-area {
  background: #ffffff;
  border-radius: 20px;
  padding: 20px 24px;
  box-shadow: var(--color-shadow);
  display: grid;
  gap: 12px;
  margin-bottom: 24px;
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
  padding: 40px;
  text-align: center;
  border-radius: 20px;
  border: 2px dashed #c8d6ee;
  color: #7b8da7;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
}

.empty-hint {
  font-size: 14px;
  color: #a0b0cc;
}

/* 题目卡片 */
.question-card {
  background: #ffffff;
  border-radius: 22px;
  padding: 22px;
  box-shadow: var(--color-shadow);
  display: grid;
  gap: 14px;
  animation: fadeIn 0.4s ease;
  transition: all 0.2s ease;
  cursor: grab;
}

.question-card:active {
  cursor: grabbing;
}

.question-card.dragging {
  opacity: 0.6;
  transform: scale(0.98);
  box-shadow: 0 8px 24px rgba(16, 35, 63, 0.15);
}

.question-card.drop-target {
  border: 2px dashed #2665d4;
  background: #f8faff;
}

.question-card.dragging-touch {
  opacity: 0.7;
  transform: scale(0.98);
}

.question-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.drag-handle {
  color: #a0b0cc;
  font-size: 18px;
  cursor: grab;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.2s ease;
  user-select: none;
}

.drag-handle:hover {
  background: #f0f4ff;
  color: #2665d4;
}

.drag-handle:active {
  cursor: grabbing;
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

/* 底部工具栏 */
.toolbar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  background: #ffffff;
  border-radius: 0;
  border-top: 1px solid #e6effa;
  box-shadow: 0 -4px 12px rgba(16, 35, 63, 0.08);
  padding: 12px 48px 12px 80px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 50;
  flex-wrap: wrap;
  gap: 12px;
  box-sizing: border-box;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-right {
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
  transition: all 0.2s ease;
}

.add-button:hover {
  transform: scale(1.05);
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
  transition: all 0.2s ease;
}

.add-item:hover:not(.disabled) {
  background: #eef4ff;
  border-color: #2665d4;
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
  transition: all 0.2s ease;
}

.outline-item:hover {
  background: #eef4ff;
  border-color: #2665d4;
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

/* 平板适配 */
@media (max-width: 960px) {
  .builder-shell {
    padding: 24px 24px 100px 70px;
  }

  .toolbar {
    padding: 12px 24px 12px 70px;
  }

  .ai-template-content {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .template-edit-area {
    order: 1;
  }

  .template-example-area {
    order: 2;
  }
}

/* 移动端适配 */
@media (max-width: 720px) {
  .builder-shell {
    padding: 16px 16px 100px 16px;
  }

  /* 移动端返回按钮调整 */
  .back-btn {
    padding: 6px 12px;
    font-size: 12px;
  }

  .back-btn-container {
    padding: 8px 0;
    margin-bottom: 8px;
  }

  .builder-header {
    margin-top: 0;
    padding: 16px 0;
  }

  .page-title {
    font-size: 24px;
  }

  .title-display {
    font-size: 18px;
  }

  .title-input {
    font-size: 16px;
    min-width: 200px;
  }

  .ai-template-section {
    padding: 20px 16px;
    border-radius: 16px;
  }

  .ai-template-header h2 {
    font-size: 18px;
  }

  .ai-template-content {
    grid-template-columns: 1fr;
  }

  .template-textarea {
    min-height: 200px;
    font-size: 13px;
  }

  .example-content {
    min-height: 150px;
  }

  .example-text {
    font-size: 12px;
  }

  /* 移动端工具栏 */
  .toolbar {
    padding: 10px 16px 10px 16px;
  }

  .toolbar-left {
    width: 100%;
    justify-content: flex-start;
    gap: 8px;
  }

  .toolbar-right {
    width: 100%;
    justify-content: flex-end;
    gap: 8px;
  }

  .ghost-button {
    padding: 8px 12px;
    font-size: 13px;
  }

  .primary-button {
    padding: 8px 14px;
    font-size: 13px;
  }

  .add-button {
    width: 40px;
    height: 40px;
    font-size: 20px;
  }

  .add-panel {
    right: 0;
    left: auto;
    grid-template-columns: 1fr 1fr;
    min-width: 240px;
  }

  .side-panel {
    left: 12px;
    right: 12px;
    width: auto;
    bottom: 100px;
  }

  /* 拖拽手柄在移动端更明显 */
  .drag-handle {
    padding: 8px 10px;
    font-size: 20px;
    background: #f5f8ff;
    border-radius: 8px;
  }

  .question-card {
    padding: 16px;
  }
}
</style>
