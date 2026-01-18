<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const token = localStorage.getItem('access_token')

const isReadonly = computed(() => route.query.readonly === 'true')

const survey = ref(null)
const loading = ref(false)
const error = ref(null)
const startTime = ref(null)

async function fetchSurvey() {
  if (!token) {
    alert('未登录，请先登录')
    router.push('/login')
    return
  }

  loading.value = true
  error.value = null

  try {
    const res = await fetch(`/api/v1/surveys/${route.params.id}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (!res.ok) {
      throw new Error('问卷不存在或已删除')
    }

    survey.value = await res.json()
    startTime.value = Date.now()
  } catch (err) {
    console.error('Failed to fetch survey:', err)
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function handleSubmit() {
  if (isReadonly.value) {
    alert('当前为只读模式，无法提交')
    return
  }

  const duration = Math.round((Date.now() - startTime.value) / 1000)
  alert(`提交成功！填答耗时 ${duration} 秒`)
}

function goBack() {
  router.back()
}

onMounted(() => {
  fetchSurvey()
})
</script>

<template>
  <div class="survey-fill">
    <header class="header">
      <button class="back-btn" @click="goBack">&larr; 返回</button>
      <h1>{{ survey?.title || '加载中...' }}</h1>
    </header>

    <div v-if="isReadonly" class="readonly-badge">
      ✓ 您已完成此问卷，当前仅供回顾
    </div>

    <div v-if="loading" class="loading">
      加载问卷中...
    </div>

    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button @click="goBack">返回</button>
    </div>

    <main v-else-if="survey" class="content">
      <section class="survey-info">
        <p v-if="survey.description" class="description">
          {{ survey.description }}
        </p>
        <div class="meta">
          <span v-if="survey.estimated_minutes" class="meta-item">
            ⏱️ 预计耗时: {{ survey.estimated_minutes }} 分钟
          </span>
          <span v-if="survey.reward_points" class="meta-item">
            🎁 奖励积分: {{ survey.reward_points }}
          </span>
          <span v-if="survey.deadline" class="meta-item">
            📅 截止时间: {{ survey.deadline }}
          </span>
        </div>
      </section>

      <section class="survey-form">
        <div v-if="survey.link" class="form-notice">
          <p>问卷链接指向外部表单，请在新标签页打开以填写</p>
          <a 
            :href="survey.link" 
            target="_blank" 
            rel="noopener noreferrer"
            :class="['survey-link', isReadonly ? 'disabled' : '']"
            :onclick="isReadonly ? 'return false' : null"
          >
            📋 打开问卷
          </a>
        </div>
        <div v-else class="form-notice">
          <p>该问卷暂无链接</p>
        </div>
      </section>

      <section class="form-actions">
        <button 
          class="submit-btn"
          @click="handleSubmit"
          :disabled="isReadonly"
        >
          {{ isReadonly ? '只读模式' : '提交答卷' }}
        </button>
      </section>
    </main>
  </div>
</template>

<style scoped>
.survey-fill {
  min-height: 100vh;
  background: radial-gradient(circle at top left, #edf3ff 0%, #f7f9ff 45%, #ffffff 100%);
  padding: 0;
}

.header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 24px;
  background: #ffffff;
  border-bottom: 1px solid #e8eef5;
}

.back-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  color: #1e4fb4;
  font-weight: 600;
  padding: 8px 12px;
}

.back-btn:hover {
  opacity: 0.7;
}

.header h1 {
  font-size: 20px;
  font-weight: 600;
  color: #1a202c;
  margin: 0;
  flex: 1;
}

.readonly-badge {
  margin: 16px 24px;
  padding: 12px 16px;
  background: #e8f5e9;
  color: #2e7d32;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  border-left: 4px solid #2e7d32;
}

.loading,
.error {
  text-align: center;
  padding: 48px 24px;
  color: #666;
}

.error {
  color: #d32f2f;
}

.error button {
  margin-top: 16px;
  padding: 8px 24px;
  background: #d32f2f;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.content {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
}

.survey-info {
  background: #ffffff;
  padding: 24px;
  border-radius: 8px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.description {
  font-size: 16px;
  color: #333;
  line-height: 1.6;
  margin: 0 0 16px 0;
}

.meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meta-item {
  font-size: 14px;
  color: #666;
}

.survey-form {
  background: #ffffff;
  padding: 24px;
  border-radius: 8px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  text-align: center;
}

.form-notice {
  color: #666;
  font-size: 14px;
  margin-bottom: 16px;
}

.form-notice p {
  margin: 0 0 12px 0;
}

.survey-link {
  display: inline-block;
  padding: 12px 32px;
  background: #1e4fb4;
  color: white;
  text-decoration: none;
  border-radius: 6px;
  font-weight: 600;
  transition: all 0.2s;
}

.survey-link:hover:not(.disabled) {
  background: #1a3f8a;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(30, 79, 180, 0.2);
}

.survey-link.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.form-actions {
  text-align: center;
}

.submit-btn {
  padding: 12px 48px;
  background: #1e4fb4;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.submit-btn:hover:not(:disabled) {
  background: #1a3f8a;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(30, 79, 180, 0.2);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
