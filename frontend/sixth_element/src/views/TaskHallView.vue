<template>
  <div class="task-hall">
    <header class="header">
      <div class="title-block">
        <p class="kicker">Task Lobby</p>
        <h1>任务大厅</h1>
      </div>

      <div class="actions">
        <div class="search-box">
          <span class="icon">🔍</span>
          <input v-model="keyword" type="search" placeholder="搜索问卷关键词" />
        </div>
        <button class="ghost" @click="refreshBatch">换一批</button>
      </div>
    </header>

    <section class="task-grid">
      <article
        v-for="(task, idx) in filteredTasks"
        :key="task.id"
        class="task-card"
      >
        <div class="card-top">
          <div class="card-titles">
            <h3>{{ task.title }}</h3>
            <p class="subtitle">{{ task.subtitle }}</p>
          </div>
          <div class="meta">
            <span class="pill type">{{ task.type }}</span>
            <span class="pill time">{{ task.estimated }}min</span>
          </div>
        </div>

        <div class="card-middle">
          <div class="badge">
            <span class="label">难度</span>
            <div class="stars">
              <span v-for="n in 5" :key="n" :class="{ active: n <= task.difficulty }">★</span>
            </div>
          </div>
          <div class="badge reward-badge">
            <span class="label">奖励</span>
            <span class="points">+{{ task.reward }}</span>
          </div>
          <div class="badge participants-badge">
            <span class="label">👥</span>
            <span class="count">{{ task.filled }}/{{ task.total }}</span>
          </div>
        </div>

        <div class="card-bottom">
          <div class="progress-wrapper">
            <div class="progress">
              <div class="progress-bar" :style="{ width: progressPercent(task) + '%' }"></div>
            </div>
            <div class="progress-percent">{{ progressPercent(task) }}%</div>
          </div>
          <div class="match-indicator" :class="getMatchClass(task)">
            {{ getMatchText(task) }}
          </div>
          <button class="fill-btn" @click.stop="goFill(task)">填写问卷</button>
          <button class="delete-btn" @click.stop="handleDelete(idx)" aria-label="删除问卷">
            ×
          </button>
        </div>
      </article>
    </section>

    <!-- 可拖动的FAB -->
    <RouterLink
      class="fab"
      ref="fabRef"
      :style="{ right: fabPosition.x + 'px', bottom: fabPosition.y + 'px' }"
      @mousedown.stop="startDrag($event, 'fab')"
      to="/survey/new"
      aria-label="新建问卷"
    >
      <span class="fab-icon">📝</span>
      <span class="fab-plus">+</span>
    </RouterLink>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  getTaskHallOverview,
  getTaskHallTasks,
  refreshTaskHallBatch
} from '@/utils/taskHallApi'

const router = useRouter()

const keyword = ref('')
const userPoints = ref(0) // 用户积分
const tasks = ref([])
const loading = ref(false)
const error = ref('')
const searchTimer = ref(null)

// 拖拽相关
const menuRef = ref(null)
const fabRef = ref(null)
const menuPosition = ref({ x: 0, y: 0 })
const fabPosition = ref({ x: 20, y: 20 })
const dragState = ref({ isDragging: false, type: null, startX: 0, startY: 0, initialX: 0, initialY: 0 })
const fabDragTimer = ref(null)
const fabTouchStarted = ref(false)

function startDrag(e, type) {
  // FAB使用长按才能拖拽，防止误触
  if (type === 'fab') {
    fabTouchStarted.value = true
    fabDragTimer.value = setTimeout(() => {
      if (fabTouchStarted.value) {
        activateFabDrag(e, type)
      }
    }, 500) // 长按500ms才能拖拽
    return
  }

  // 菜单可以直接拖拽
  activateFabDrag(e, type)
}

function activateFabDrag(e, type) {
  const clientX = e.type.includes('touch') ? e.touches[0]?.clientX : e.clientX
  const clientY = e.type.includes('touch') ? e.touches[0]?.clientY : e.clientY

  if (!clientX || !clientY) return

  dragState.value = {
    isDragging: true,
    type: type,
    startX: clientX,
    startY: clientY,
    initialX: type === 'menu' ? menuPosition.value.x : fabPosition.value.x,
    initialY: type === 'menu' ? menuPosition.value.y : fabPosition.value.y
  }

  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  document.addEventListener('touchmove', onDrag)
  document.addEventListener('touchend', stopDrag)
}

function onDrag(e) {
  if (!dragState.value.isDragging) return
  
  const clientX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX
  const clientY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY

  const deltaX = clientX - dragState.value.startX
  const deltaY = clientY - dragState.value.startY

  if (dragState.value.type === 'menu') {
    menuPosition.value = {
      x: dragState.value.initialX + deltaX,
      y: dragState.value.initialY + deltaY
    }
  } else if (dragState.value.type === 'fab') {
    // FAB使用right/bottom，所以拖动时需要反向计算
    fabPosition.value = {
      x: dragState.value.initialX - deltaX,
      y: dragState.value.initialY - deltaY
    }
  }
}

function stopDrag() {
  // 清除FAB长按定时器
  if (fabDragTimer.value) {
    clearTimeout(fabDragTimer.value)
    fabDragTimer.value = null
  }
  fabTouchStarted.value = false

  dragState.value.isDragging = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', stopDrag)
}

async function loadOverview() {
  try {
    const data = await getTaskHallOverview(router)
    userPoints.value = data?.user?.points ?? 0
  } catch (err) {
    console.error('加载任务大厅概览失败:', err)
    error.value = err.message || '加载任务大厅失败'
  }
}

async function loadTasks(params = {}) {
  loading.value = true
  error.value = ''
  try {
    const data = await getTaskHallTasks(
      {
        keyword: keyword.value.trim() || undefined,
        page: 1,
        page_size: 20,
        ...params,
      },
      router
    )
    tasks.value = Array.isArray(data?.items) ? data.items : []
  } catch (err) {
    console.error('加载任务列表失败:', err)
    error.value = err.message || '加载任务列表失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {

  loadOverview()
  loadTasks()
})

onUnmounted(() => {
  // 清除FAB长按定时器
  if (fabDragTimer.value) {
    clearTimeout(fabDragTimer.value)
  }
  if (searchTimer.value) {
    clearTimeout(searchTimer.value)
  }
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', stopDrag)
  window.removeEventListener('resize', handleResize)
})

async function refreshBatch() {
  const confirm = window.confirm('确认要换一批问卷吗？当前页面的问卷将被替换。')
  if (!confirm) return
  try {
    loading.value = true
    const excludeIds = tasks.value.map((t) => t.id)
    const data = await refreshTaskHallBatch(excludeIds, 15, router)
    tasks.value = Array.isArray(data?.items) ? data.items : []
  } catch (err) {
    console.error('换一批失败:', err)
    error.value = err.message || '换一批失败'
  } finally {
    loading.value = false
  }
}

async function handleDelete(index) {
  const ok = window.confirm('确认删除该问卷吗？将自动补位新的问卷。')
  if (!ok) return

  const current = tasks.value[index]
  tasks.value.splice(index, 1)

  try {
    const excludeIds = tasks.value.map((t) => t.id)
    if (current?.id) {
      excludeIds.push(current.id)
    }
    const data = await refreshTaskHallBatch(excludeIds, 1, router)
    const replacement = Array.isArray(data?.items) ? data.items[0] : null
    if (replacement) {
      tasks.value.splice(index, 0, replacement)
    }
  } catch (err) {
    console.error('补位失败:', err)
  }
}

const filteredTasks = computed(() => tasks.value)

function progressPercent(task) {
  if (!task.total) return 0
  return Math.min(100, Math.round((task.filled / task.total) * 100))
}

// 根据难度显示分类（只有高性价比和挑战任务两种）
function getMatchClass(task) {
  if (task.match_level === 'high') return 'high-match'
  if (task.match_level === 'medium') return 'high-match'
  if (task.difficulty <= 2) return 'high-match'
  return 'low-match'
}

function getMatchText(task) {
  if (task.match_level === 'high') return '高性价比'
  if (task.match_level === 'medium') return '中性价比'
  if (task.match_level === 'low') return '挑战任务'
  if (task.difficulty <= 2) return '高性价比'
  return '挑战任务'
}

function extractSurveyId(taskId) {
  if (!taskId) return null
  const raw = String(taskId)
  const match = raw.match(/\d+/)
  return match ? match[0] : null
}

function goFill(task) {
  const surveyId = extractSurveyId(task?.id)
  if (!surveyId) {
    alert('问卷ID无效，无法进入填写页面')
    return
  }
  router.push(`/survey/${surveyId}/fill`)
}

watch(keyword, () => {
  if (searchTimer.value) {
    clearTimeout(searchTimer.value)
  }
  searchTimer.value = setTimeout(() => {
    loadTasks()
  }, 400)
})
</script>

<style scoped>
.task-hall {
  min-height: 100vh;
  background: #f6f8fb;
  padding: 12px 10px 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.header {
  background: #ffffff;
  border: 1px solid #e3e9f5;
  border-radius: 14px;
  padding: 12px 16px;
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 14px;
  box-shadow: 0 6px 20px rgba(0, 82, 217, 0.05);
}

.title-block h1 {
  margin: 2px 0 0;
  font-size: 22px;
  color: #0b2b66;
  font-weight: 700;
}

.kicker {
  text-transform: uppercase;
  letter-spacing: 0.24em;
  font-size: 11px;
  color: #5c7599;
  margin: 0;
}

.actions {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: center;
}

.search-box {
  flex: 1;
  min-width: 240px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f2f6ff;
  border: 1px solid #d7e3ff;
  border-radius: 10px;
  padding: 8px 10px;
}

.search-box input {
  border: none;
  background: transparent;
  outline: none;
  width: 100%;
  font-size: 14px;
  color: #0b2b66;
}

.search-box .icon {
  font-size: 14px;
}

.ghost {
  border: 1px solid #0052d9;
  color: #0052d9;
  background: #ffffff;
  padding: 8px 14px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.ghost:hover {
  background: #0052d9;
  color: #ffffff;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 可拖动菜单 */
.draggable-menu {
  position: fixed;
  z-index: 100;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(12px);
  border: 1px solid #e3e9f5;
  border-radius: 16px;
  padding: 8px 12px;
  box-shadow: 0 8px 24px rgba(0, 82, 217, 0.15);
  cursor: move;
  touch-action: none;
  user-select: none;
  transition: box-shadow 0.2s ease;
}

.draggable-menu:hover {
  box-shadow: 0 12px 32px rgba(0, 82, 217, 0.22);
}

.drag-handle {
  position: absolute;
  left: 4px;
  top: 50%;
  transform: translateY(-50%);
  color: #a0b0cc;
  font-size: 14px;
  letter-spacing: -2px;
  cursor: grab;
}

.drag-handle:active {
  cursor: grabbing;
}

.points-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: linear-gradient(135deg, #ffd700, #ffb400);
  color: #333;
  border-radius: 12px;
  text-decoration: none;
  font-weight: 700;
  font-size: 14px;
  box-shadow: 0 4px 12px rgba(255, 180, 0, 0.3);
  transition: transform 0.2s ease;
}

.points-badge:hover {
  transform: scale(1.05);
}

.points-icon {
  font-size: 16px;
}

.points-value {
  font-family: 'Courier New', monospace;
}

.nav-btn {
  padding: 8px 14px;
  background: #0052d9;
  color: white;
  border-radius: 10px;
  text-decoration: none;
  font-weight: 600;
  box-shadow: 0 8px 20px rgba(0, 82, 217, 0.16);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.nav-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(0, 82, 217, 0.18);
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0052d9, #2f7bff);
  color: white;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  font-weight: 700;
  box-shadow: 0 6px 12px rgba(0, 82, 217, 0.16);
}

.task-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 14px;
  width: 100%;
}

@media (min-width: 1400px) {
  .task-grid {
    grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  }
}

@media (min-width: 1800px) {
  .task-grid {
    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  }
}

.task-card {
  background: #ffffff;
  border: 1px solid #e3e9f5;
  border-radius: 14px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: 0 8px 20px rgba(0, 82, 217, 0.05);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.fill-btn {
  border: none;
  background: #0052d9;
  color: #ffffff;
  padding: 8px 12px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.fill-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 16px rgba(0, 82, 217, 0.18);
}

.task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(0, 82, 217, 0.08);
}

.task-card:hover .delete-btn {
  opacity: 1;
}

.card-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.card-titles h3 {
  margin: 2px 0 4px;
  font-size: 17px;
  color: #0b2b66;
}

.card-titles .subtitle {
  margin: 0;
  color: #5b6d86;
  font-size: 14px;
}

.meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: flex-end;
}

.pill {
  padding: 6px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  color: #0b2b66;
  background: #eef3ff;
  border: 1px solid #d7e3ff;
  white-space: nowrap;
  min-width: fit-content;
}

.pill.time {
  background: #f4f9ff;
}

.card-middle {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.badge {
  background: #f7f9fc;
  border: 1px solid #e3e9f5;
  border-radius: 12px;
  padding: 8px 10px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.reward-badge {
  background: linear-gradient(135deg, #fff8e1, #ffecb3);
  border-color: #ffe082;
}

.participants-badge {
  background: linear-gradient(135deg, #e8f5e9, #c8e6c9);
  border-color: #a5d6a7;
}

.participants-badge .count {
  font-weight: 700;
  color: #2e7d32;
  font-size: 13px;
}

.badge .label {
  font-size: 12px;
  color: #5c7599;
}

.stars span {
  color: #cdd8f3;
  font-size: 14px;
}

.stars span.active {
  color: #ffb400;
}

.points {
  color: #0052d9;
  font-weight: 700;
}

.card-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  position: relative;
}

.delete-btn {
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
  flex-shrink: 0;
  opacity: 0;
}

.delete-btn:hover {
  background: #f44336;
  color: white;
  transform: scale(1.1);
}

.progress-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.progress {
  flex: 1;
  height: 8px;
  border-radius: 999px;
  background: #edf1f7;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(135deg, #0052d9, #2f7bff);
  transition: width 0.3s ease;
}

.progress-percent {
  min-width: 40px;
  text-align: right;
  font-size: 12px;
  font-weight: 700;
  color: #0052d9;
}

.match-indicator {
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  white-space: nowrap;
  flex-shrink: 0;
}

.high-match {
  background: linear-gradient(135deg, #4caf50, #66bb6a);
  color: white;
  box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
}

.low-match {
  background: linear-gradient(135deg, #f44336, #e57373);
  color: white;
  box-shadow: 0 2px 8px rgba(244, 67, 54, 0.3);
}

.fab {
  position: fixed;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ff6b6b, #ee5a6f);
  color: #ffffff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  box-shadow: 0 12px 32px rgba(238, 90, 111, 0.5);
  transition: all 0.2s ease;
  cursor: move;
  touch-action: none;
  user-select: none;
  z-index: 90;
}

.fab:hover {
  transform: scale(1.15);
  box-shadow: 0 16px 40px rgba(238, 90, 111, 0.6);
}

.fab:active {
  cursor: grabbing;
}

.fab-icon {
  font-size: 32px;
  line-height: 1;
}

.fab-plus {
  font-size: 26px;
  font-weight: 700;
  line-height: 1;
  margin-top: -6px;
}

@media (max-width: 960px) {
  .header {
    grid-template-columns: 1fr;
    align-items: flex-start;
  }

  .actions {
    width: 100%;
    justify-content: flex-start;
  }

  .nav-right {
    justify-content: flex-start;
  }

  .task-grid {
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  }

  /* 移动端菜单优化 */
  .draggable-menu {
    padding: 6px 10px;
    gap: 8px;
  }

  .points-badge {
    padding: 5px 10px;
    font-size: 13px;
  }

  .nav-btn {
    padding: 6px 12px;
    font-size: 13px;
  }

  .avatar {
    width: 32px;
    height: 32px;
    font-size: 14px;
  }
}

@media (max-width: 640px) {
  .task-hall {
    padding: 10px 8px 80px; /* 底部留出FAB空间 */
  }

  .header {
    padding: 10px 12px;
  }

  .card-top {
    flex-direction: column;
    align-items: flex-start;
  }

  .meta {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 6px;
  }

  /* 移动端任务卡片更紧凑 */
  .task-card {
    padding: 10px 12px;
    gap: 8px;
  }

  .card-titles h3 {
    margin: 0 0 2px;
    font-size: 15px;
  }

  .card-titles .subtitle {
    font-size: 12px;
    margin: 0;
  }

  .card-middle {
    gap: 6px;
    flex-wrap: wrap;
  }

  .badge {
    padding: 5px 8px;
    font-size: 11px;
  }

  .badge .label {
    font-size: 11px;
  }

  .match-indicator {
    font-size: 10px;
    padding: 3px 8px;
  }

  .delete-btn {
    width: 24px;
    height: 24px;
    font-size: 18px;
    opacity: 1;
  }

  .progress-wrapper {
    gap: 8px;
  }

  .progress {
    height: 6px;
  }

  .progress-percent {
    font-size: 11px;
    min-width: 36px;
  }

  /* 移动端FAB优化 */
  .fab {
    width: 64px;
    height: 64px;
  }

  .fab-icon {
    font-size: 24px;
  }

  .fab-plus {
    font-size: 20px;
  }

  /* 移动端拖动菜单调整 */
  .draggable-menu {
    flex-wrap: wrap;
    max-width: calc(100vw - 24px);
  }

  .drag-handle {
    font-size: 12px;
  }

  /* 任务卡片移动端优化 */
  .task-grid {
    grid-template-columns: 1fr;
  }
}
</style>
