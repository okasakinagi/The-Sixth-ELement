<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const surveyId = computed(() => route.params.id)
</script>

<template>
  <div class="analytics">
    <header>
      <RouterLink class="back" to="/surveys">返回问卷管理</RouterLink>
      <h1>数据分析</h1>
      <p>问卷 {{ surveyId }} 的概览数据</p>
    </header>
    <section class="grid">
      <article class="card">
        <h2>完成率</h2>
        <p class="metric">100%</p>
        <p class="hint">采集份数已达标</p>
      </article>
      <article class="card">
        <h2>平均用时</h2>
        <p class="metric">3'12"</p>
        <p class="hint">高于同类问卷 12%</p>
      </article>
      <article class="card">
        <h2>题目满意度</h2>
        <p class="metric">4.6 / 5</p>
        <p class="hint">来自 300 份反馈</p>
      </article>
    </section>
  </div>
</template>

<style scoped>
.analytics {
  min-height: 100vh;
  padding: 48px;
  background: radial-gradient(circle at top left, #edf3ff 0%, #f7f9ff 45%, #ffffff 100%);
}

header {
  display: grid;
  gap: 10px;
  margin-bottom: 32px;
}

h1 {
  font-family: 'Newsreader', serif;
  font-size: 32px;
}

.back {
  color: #1e4fb4;
  font-weight: 600;
}

.grid {
  display: grid;
  gap: 20px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.card {
  background: #ffffff;
  padding: 24px;
  border-radius: 20px;
  box-shadow: 0 14px 30px rgba(16, 35, 63, 0.12);
  display: grid;
  gap: 10px;
}

.metric {
  font-size: 28px;
  font-weight: 600;
  color: #1e4fb4;
}

.hint {
  color: #6a7d95;
}
</style>
