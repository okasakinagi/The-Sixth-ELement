<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { aiGenerateDraftQuestions, createSurveyDraft } from '../utils/surveyManagementApi'

const router = useRouter()
const title = ref('')
const loading = ref(false)
const errorMessage = ref('')

// 左侧可编辑的需求描述（默认填好模板文案）
const prompt = ref(`请生成一份调查问卷
问卷主题：员工餐厅就餐满意度调查
题目数量：15题
调研目的：了解员工对员工餐厅各方面的满意度情况
更多要求：`)

// 右侧只读示例
const exampleText = `请生成一份调查问卷
问卷主题：[填写你的问卷主题]
题目数量：[大约需要的题目数]
调研目的：[说明调研目的]
更多要求：[可选，如需要评分题、排序题等]`

const goBack = () => {
  router.back()
}

const loadDraft = () => {
  const raw = sessionStorage.getItem('survey-draft')
  if (!raw) return
  try {
    const draft = JSON.parse(raw)
    title.value = draft.title || ''
  } catch {
    title.value = ''
  }
}

onMounted(loadDraft)

const startGenerate = async () => {
  const raw = sessionStorage.getItem('survey-draft')
  const draft = raw ? JSON.parse(raw) : {}
  const merged = {
    title: title.value || draft.title || '未命名问卷',
    description: '',
    prompt: prompt.value.trim(),
    source: 'ai',
  }
  if (!merged.prompt) {
    errorMessage.value = '请先填写问卷需求描述'
    return
  }
  loading.value = true
  errorMessage.value = ''
  try {
    const created = await createSurveyDraft({
      title: merged.title,
      subtitle: merged.description,
    })
    const draftId = created.id
    const generated = await aiGenerateDraftQuestions(draftId, {
      prompt: merged.prompt,
      question_count: 10,
    })
    sessionStorage.setItem(
      'survey-draft',
      JSON.stringify({
        ...merged,
        id: draftId,
        questions: generated.questions || [],
      }),
    )
    router.push({ name: 'survey-editor', query: { ai: '1', draft_id: draftId } })
  } catch (error) {
    errorMessage.value = error?.message || 'AI 生成失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="ai-shell">
    <!-- 顶部返回按钮 -->
    <div class="top-bar">
      <button class="back" type="button" @click="goBack">← 返回</button>
    </div>

    <!-- 居中的标题区域 -->
    <header class="ai-header">
      <p class="kicker">AI Prompt</p>
      <h1>用 AI 生成问卷草案</h1>
      <div class="current-title">
        <span>当前标题</span>
        <strong>{{ title || '未命名问卷' }}</strong>
      </div>
    </header>

    <main class="ai-main">
      <!-- 左侧：可编辑的需求描述 -->
      <section class="prompt-card">
        <div class="prompt-header">
          <p class="prompt-title">描述你的需求</p>
          <p class="prompt-subtitle">AI 会根据描述生成题目草案，直接修改下方文字即可。</p>
        </div>

        <textarea
          v-model="prompt"
          class="prompt-input editable"
          rows="14"
        ></textarea>
        <div class="prompt-actions">
          <button class="ghost-button" type="button" @click="router.push({ name: 'survey-editor' })">
            跳过并手动编辑
          </button>
          <button class="primary-button" type="button" :disabled="loading" @click="startGenerate">
            {{ loading ? '生成中...' : '开始生成' }}
          </button>
        </div>
        <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
      </section>

      <!-- 右侧：只读的案例引导 -->
      <aside class="case-card">
        <h2>案例引导</h2>
        <p class="case-desc">比如：使用下面的格式来描述问卷需求</p>
        <div class="example-box">
          <pre class="example-text">{{ exampleText }}</pre>
        </div>
        <ul class="case-tips">
          <li>说明调研目的，有助于 AI 生成更贴合的题目。</li>
          <li>题目数量可以略估，后续可在编辑器中增删。</li>
          <li>如果需要评分题或排序题，可在更多要求中备注。</li>
        </ul>
      </aside>
    </main>
  </div>
</template>

<style scoped>
.ai-shell {
  min-height: 100vh;
  padding: 32px 40px;
  background: radial-gradient(circle at top right, #eaf2ff 0%, #ffffff 55%);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 顶部返回按钮 */
.top-bar {
  display: flex;
  justify-content: flex-start;
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

/* 居中标题区域 */
.ai-header {
  text-align: center;
  padding: 16px 0;
}

.kicker {
  text-transform: uppercase;
  letter-spacing: 0.18em;
  font-size: 11px;
  color: #5a7395;
  margin-bottom: 6px;
}

.ai-header h1 {
  font-family: 'Newsreader', serif;
  font-size: 32px;
  margin: 0 0 16px 0;
  color: #1a3b7f;
}

.current-title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: #f2f6ff;
  border-radius: 14px;
  padding: 10px 18px;
  font-size: 13px;
  color: #5a7395;
}

.current-title strong {
  color: #1a3b7f;
  font-size: 14px;
}

/* 主体双栏布局 */
.ai-main {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 24px;
  flex: 1;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
}

.prompt-card,
.case-card {
  background: #ffffff;
  border-radius: 24px;
  padding: 28px;
  box-shadow: var(--color-shadow);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 左侧：描述需求 */
.prompt-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.prompt-title {
  font-weight: 600;
  color: #1a3b7f;
  font-size: 16px;
}

.prompt-subtitle {
  font-size: 13px;
  color: #6d7f9a;
}

.prompt-input {
  width: 100%;
  border-radius: 16px;
  border: 1px solid #d4e1f6;
  padding: 16px;
  font-size: 14px;
  line-height: 1.7;
  resize: vertical;
  background: #fbfdff;
  flex: 1;
  min-height: 200px;
  font-family: inherit;
}

.prompt-input.editable {
  background: #fffef8;
  border: 2px solid #e8d8a0;
}

.prompt-input:focus {
  outline: 2px solid rgba(38, 101, 212, 0.25);
  border-color: #2665d4;
}

.prompt-input.editable:focus {
  border-color: #c9a932;
  outline: 2px solid rgba(201, 169, 50, 0.2);
}

.prompt-actions {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: auto;
}

.error-text {
  color: #b42318;
  font-size: 13px;
  margin: 0;
}

.ghost-button,
.primary-button {
  padding: 12px 20px;
  border-radius: 16px;
  font-weight: 600;
  cursor: pointer;
  border: none;
}

.ghost-button {
  background: #f2f6ff;
  color: #1e4fb4;
  border: 1px solid rgba(38, 101, 212, 0.2);
}

.ghost-button:hover {
  background: #e8f0ff;
}

.primary-button {
  background: linear-gradient(135deg, #2665d4, #4f80f1);
  color: #ffffff;
}

.primary-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(38, 101, 212, 0.3);
}

/* 右侧：案例引导 */
.case-card h2 {
  font-size: 18px;
  color: #1a3b7f;
  margin: 0;
}

.case-desc {
  font-size: 13px;
  color: #6d7f9a;
  margin: 0;
}

.example-box {
  background: #f5f8fc;
  border: 1px dashed #c5d4e8;
  border-radius: 14px;
  padding: 16px;
  opacity: 0.85;
}

.example-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  color: #5a7395;
  font-family: inherit;
  white-space: pre-wrap;
}

.case-tips {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  color: #6d7f9a;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: auto;
}

/* 响应式：平板及以下 */
@media (max-width: 960px) {
  .ai-main {
    grid-template-columns: 1fr;
  }
}

/* 响应式：手机端保持良好 */
@media (max-width: 720px) {
  .ai-shell {
    padding: 20px;
  }

  .ai-header h1 {
    font-size: 24px;
  }

  .current-title {
    flex-direction: column;
    gap: 4px;
  }

  .prompt-card,
  .case-card {
    padding: 20px;
  }

  .prompt-actions {
    flex-direction: column;
  }

  .ghost-button,
  .primary-button {
    width: 100%;
    text-align: center;
  }
}
</style>
