<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const surveyId = computed(() => route.params.id)
</script>

<template>
  <div class="builder">
    <header>
      <RouterLink class="back" to="/surveys">返回问卷管理</RouterLink>
      <h1>问卷制作</h1>
      <p v-if="surveyId">正在编辑：{{ surveyId }}</p>
      <p v-else>新建问卷模板</p>
    </header>
    <section class="canvas">
      <h2>拖拽题型到这里开始设计</h2>
      <p>这是问卷制作入口示意，后续可接入真实编辑器。</p>
    </section>
  </div>
</template>

<style scoped>
.builder {
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

.canvas {
  background: #ffffff;
  padding: 32px;
  border-radius: 24px;
  border: 2px dashed #c8d6ee;
  text-align: center;
  color: #5f6f86;
}
</style>
