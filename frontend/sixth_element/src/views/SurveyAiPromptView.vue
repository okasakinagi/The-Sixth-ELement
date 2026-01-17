<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const prompt = ref('')
const title = ref('')

const exampleText = `请生成一份调查问卷
问卷主题：员工餐厅就餐满意度调查
题目数量：15题
调研目的：了解员工对员工餐厅各方面的满意度情况
更多要求：`

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

const startGenerate = () => {
  const raw = sessionStorage.getItem('survey-draft')
  const draft = raw ? JSON.parse(raw) : {}
  const merged = {
    title: title.value || draft.title || '未命名问卷',
    description: '',
    prompt: prompt.value.trim(),
    source: 'ai',
  }
  sessionStorage.setItem('survey-draft', JSON.stringify(merged))
  router.push({ name: 'survey-editor', query: { ai: '1' } })
}
</script>

<template>
  <div class="ai-shell">
    <header class="ai-header">
      <RouterLink class="back" to="/survey/new">返回标题设定</RouterLink>
      <div>
        <p class="kicker">AI Prompt</p>
        <h1>用 AI 生成问卷草案</h1>
      </div>
    </header>

    <main class="ai-main">
      <section class="prompt-card">
        <div class="prompt-header">
          <div>
            <p class="prompt-title">描述你的需求</p>
            <p class="prompt-subtitle">AI 会根据描述生成题目草案，你可以再编辑修改。</p>
          </div>
          <div class="prompt-meta">
            <span>当前标题</span>
            <strong>{{ title || '未命名问卷' }}</strong>
          </div>
        </div>

        <textarea
          v-model="prompt"
          class="prompt-input"
          rows="12"
          :placeholder="exampleText"
        ></textarea>
        <div class="prompt-actions">
          <button class="ghost-button" type="button" @click="router.push({ name: 'survey-editor' })">
            跳过并手动编辑
          </button>
          <button class="primary-button" type="button" @click="startGenerate">
            开始生成
          </button>
        </div>
      </section>

      <aside class="case-card">
        <h2>案例引导</h2>
        <p>可以用下面的格式来描述问卷需求：</p>
        <pre class="case-block">{{ exampleText }}</pre>
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
  padding: 40px;
  background: radial-gradient(circle at top right, #eaf2ff 0%, #ffffff 55%);
  display: grid;
  gap: 28px;
}

.ai-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.back {
  color: #1e4fb4;
  font-weight: 600;
}

.kicker {
  text-transform: uppercase;
  letter-spacing: 0.18em;
  font-size: 11px;
  color: #5a7395;
}

.ai-header h1 {
  font-family: 'Newsreader', serif;
  font-size: 30px;
  margin-top: 6px;
}

.ai-main {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
  gap: 24px;
}

.prompt-card,
.case-card {
  background: #ffffff;
  border-radius: 24px;
  padding: 28px;
  box-shadow: var(--color-shadow);
  display: grid;
  gap: 18px;
}

.prompt-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.prompt-title {
  font-weight: 600;
  color: #1a3b7f;
}

.prompt-subtitle {
  font-size: 13px;
  color: #6d7f9a;
  margin-top: 4px;
}

.prompt-meta {
  background: #f2f6ff;
  border-radius: 14px;
  padding: 10px 14px;
  font-size: 12px;
  color: #5a7395;
  display: grid;
  gap: 4px;
}

.prompt-meta strong {
  color: #1a3b7f;
  font-size: 14px;
}

.prompt-input {
  width: 100%;
  border-radius: 16px;
  border: 1px solid #d4e1f6;
  padding: 16px;
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
  background: #fbfdff;
}

.prompt-input:focus {
  outline: 2px solid rgba(38, 101, 212, 0.25);
}

.prompt-actions {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
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

.primary-button {
  background: linear-gradient(135deg, #2665d4, #4f80f1);
  color: #ffffff;
}

.case-card h2 {
  font-size: 18px;
}

.case-block {
  white-space: pre-wrap;
  background: #f2f6ff;
  padding: 16px;
  border-radius: 14px;
  font-size: 13px;
  color: #1a3b7f;
}

.case-tips {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  color: #6d7f9a;
  display: grid;
  gap: 8px;
}

@media (max-width: 960px) {
  .ai-main {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .ai-shell {
    padding: 24px;
  }

  .ai-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
