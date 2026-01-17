<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const title = ref('')

const canProceed = computed(() => title.value.trim().length > 0)

const goDirect = () => {
  if (!canProceed.value) return
  sessionStorage.setItem(
    'survey-draft',
    JSON.stringify({
      title: title.value.trim(),
      description: '',
      questions: [],
      source: 'manual',
    }),
  )
  router.push({ name: 'survey-editor' })
}

const goAi = () => {
  if (!canProceed.value) return
  sessionStorage.setItem(
    'survey-draft',
    JSON.stringify({
      title: title.value.trim(),
      description: '',
      questions: [],
      source: 'ai',
    }),
  )
  router.push({ name: 'survey-ai' })
}
</script>

<template>
  <div class="entry-shell">
    <header class="entry-header">
      <RouterLink class="back" to="/surveys">返回问卷管理</RouterLink>
      <div>
        <p class="kicker">Survey Creation</p>
        <h1>问卷制作 · 设定标题</h1>
      </div>
    </header>

    <main class="entry-main">
      <section class="title-card">
        <p class="title-hint">请输入问卷主标题</p>
        <input
          v-model="title"
          class="title-input"
          type="text"
          placeholder="例如：员工餐厅就餐满意度调查"
        />
        <p class="helper">主标题将显示在问卷首页和任务大厅的卡片上。</p>
      </section>

      <section class="mode-card">
        <h2>选择制作模式</h2>
        <div class="mode-actions">
          <button class="ghost-button" type="button" :disabled="!canProceed" @click="goDirect">
            直接进入
          </button>
          <button class="primary-button" type="button" :disabled="!canProceed" @click="goAi">
            AI 智能制作
          </button>
        </div>
        <p class="mode-note">AI 模式会引导你描述问卷需求，并快速生成题目草案。</p>
      </section>
    </main>
  </div>
</template>

<style scoped>
.entry-shell {
  min-height: 100vh;
  padding: 40px;
  background: radial-gradient(circle at top left, #e7f0ff 0%, #ffffff 55%);
  display: grid;
  gap: 28px;
}

.entry-header {
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

.entry-header h1 {
  font-family: 'Newsreader', serif;
  font-size: 30px;
  margin-top: 6px;
}

.entry-main {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 24px;
  align-items: start;
}

.title-card,
.mode-card {
  background: #ffffff;
  border-radius: 24px;
  padding: 28px;
  box-shadow: var(--color-shadow);
  display: grid;
  gap: 16px;
}

.title-hint {
  font-weight: 600;
  color: #1a3b7f;
}

.title-input {
  width: 100%;
  padding: 16px 18px;
  border-radius: 16px;
  border: 1px solid #d4e1f6;
  font-size: 16px;
}

.title-input:focus {
  outline: 2px solid rgba(38, 101, 212, 0.25);
}

.helper {
  font-size: 13px;
  color: #6d7f9a;
}

.mode-actions {
  display: flex;
  gap: 16px;
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

.ghost-button:disabled,
.primary-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.mode-note {
  font-size: 13px;
  color: #6d7f9a;
}

@media (max-width: 720px) {
  .entry-shell {
    padding: 24px;
  }

  .entry-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
