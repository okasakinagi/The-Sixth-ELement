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
          <button class="delete-btn" @click="handleDelete(task.id)" aria-label="删除问卷">
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
import { getUserPoints } from '@/utils/userPointsHelper'

const keyword = ref('')
const userPoints = ref(0) // 用户积分
const windowWidth = ref(window.innerWidth)
const windowHeight = ref(window.innerHeight)

// 根据屏幕大小计算最佳显示数量
const optimalTaskCount = computed(() => {
  const width = windowWidth.value
  const height = windowHeight.value
  
  // 估算每个卡片的大小（包含间距）
  let cardWidth = 360  // 默认卡片宽度 + 间距
  let cardHeight = 180 // 估算卡片高度 + 间距
  
  if (width >= 1800) {
    cardWidth = 420
  } else if (width >= 1400) {
    cardWidth = 380
  } else if (width <= 640) {
    cardWidth = width - 20  // 移动端单列
    cardHeight = 160
  } else if (width <= 960) {
    cardWidth = (width - 40) / 2  // 小屏幕2列
    cardHeight = 160
  }
  
  // 计算可以容纳的列数
  const cols = Math.floor((width - 40) / cardWidth) || 1
  // 计算可以容纳的行数（减去header等空间）
  const availableHeight = height - 200 // 减去header和底部空间
  const rows = Math.max(3, Math.floor(availableHeight / cardHeight))
  
  // 总数量，至少15个
  return Math.max(15, cols * rows)
})

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

// 监听窗口大小变化
function handleResize() {
  windowWidth.value = window.innerWidth
  windowHeight.value = window.innerHeight
}

onMounted(() => {

  // 初始化问卷列表
  visibleTasks.value = pickBatch(allTasks.value, optimalTaskCount.value)
  
  // 添加窗口大小监听
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  // 清除FAB长按定时器
  if (fabDragTimer.value) {
    clearTimeout(fabDragTimer.value)
  }
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', stopDrag)
  window.removeEventListener('resize', handleResize)
})

const allTasks = ref([
  { id: 't01', title: '校园生活满意度调查', subtitle: '宿舍、食堂、安保整体反馈', sender: '李同学', type: '校园调研', estimated: 6, difficulty: 2, reward: 2, filled: 54, total: 200 },
  { id: 't02', title: '课程体验回访', subtitle: '这学期的主要课程体验', sender: '张老师', type: '教学反馈', estimated: 8, difficulty: 4, reward: 4, filled: 120, total: 260 },
  { id: 't03', title: '食堂新品口味投票', subtitle: '为春季菜单挑选新品', sender: '后勤部', type: '投票', estimated: 3, difficulty: 1, reward: 1, filled: 82, total: 150 },
  { id: 't04', title: '社团活动偏好', subtitle: '选出你想参加的活动', sender: '学生会', type: '兴趣画像', estimated: 5, difficulty: 2, reward: 2, filled: 33, total: 100 },
  { id: 't05', title: '实习就业意向', subtitle: '求职方向、城市与行业偏好', sender: '就业中心', type: '就业调研', estimated: 7, difficulty: 4, reward: 4, filled: 45, total: 120 },
  { id: 't06', title: '心理健康与压力', subtitle: '期末周的压力与缓解方式', sender: '心理中心', type: '健康问卷', estimated: 9, difficulty: 5, reward: 5, filled: 18, total: 80 },
  { id: 't07', title: '图书馆使用体验', subtitle: '空间、座位、设备反馈', sender: '图书馆', type: '服务反馈', estimated: 4, difficulty: 2, reward: 2, filled: 210, total: 400 },
  { id: 't08', title: '校园出行与班车', subtitle: '线路、班次与满意度调查', sender: '后勤部', type: '交通', estimated: 4, difficulty: 2, reward: 2, filled: 60, total: 180 },
  { id: 't09', title: '新生入学指南优化', subtitle: '帮我们改进 2026 新生手册', sender: '教务处', type: '文案优化', estimated: 10, difficulty: 4, reward: 4, filled: 12, total: 60 },
  { id: 't10', title: '赛事观众调研', subtitle: '校运动会观众体验反馈', sender: '体育部', type: '活动复盘', estimated: 6, difficulty: 2, reward: 2, filled: 140, total: 260 },
  { id: 't11', title: '校友访谈邀约', subtitle: '愿意参加校友访谈的时间', sender: '校友办', type: '访谈邀约', estimated: 5, difficulty: 3, reward: 3, filled: 28, total: 90 },
  { id: 't12', title: '科研助理机会', subtitle: '可接受的课题与工作量', sender: '科研办', type: '科研匹配', estimated: 12, difficulty: 5, reward: 5, filled: 8, total: 50 },
  { id: 't13', title: '寝室卫生公约共识', subtitle: '共建寝室卫生标准', sender: '宿管部', type: '共识投票', estimated: 3, difficulty: 1, reward: 1, filled: 76, total: 120 },
  { id: 't14', title: '艺术节节目征集', subtitle: '报名你想展示的节目', sender: '文艺部', type: '活动报名', estimated: 5, difficulty: 2, reward: 2, filled: 34, total: 100 },
  { id: 't15', title: '志愿服务档期收集', subtitle: '收集可出勤的志愿时段', sender: '团委', type: '志愿服务', estimated: 4, difficulty: 2, reward: 2, filled: 95, total: 180 },
  { id: 't16', title: '手机使用习惯调研', subtitle: 'APP偏好与使用时长统计', sender: '王同学', type: '数字生活', estimated: 5, difficulty: 2, reward: 2, filled: 67, total: 150 },
  { id: 't17', title: '宿舍网络质量反馈', subtitle: '网速、稳定性与覆盖范围', sender: '信息中心', type: '设施反馈', estimated: 4, difficulty: 1, reward: 1, filled: 156, total: 300 },
  { id: 't18', title: '考研意向调查', subtitle: '考研方向与备考计划', sender: '就业办', type: '升学调研', estimated: 8, difficulty: 3, reward: 3, filled: 42, total: 100 },
  { id: 't19', title: '校园快递满意度', subtitle: '快递点服务质量评价', sender: '物流公司', type: '服务评价', estimated: 3, difficulty: 1, reward: 1, filled: 188, total: 250 },
  { id: 't20', title: '晨跑打卡活动', subtitle: '参与意愿与时间安排', sender: '体育部', type: '活动征集', estimated: 3, difficulty: 1, reward: 1, filled: 23, total: 80 },
  { id: 't21', title: '创业项目需求调研', subtitle: '创业方向与资源需求', sender: '创业中心', type: '创业调研', estimated: 10, difficulty: 4, reward: 4, filled: 15, total: 60 },
  { id: 't22', title: '课外阅读习惯', subtitle: '阅读类型与频率调查', sender: '图书馆', type: '文化调研', estimated: 5, difficulty: 2, reward: 2, filled: 89, total: 200 },
  { id: 't23', title: '校园安全隐患反馈', subtitle: '发现的安全问题上报', sender: '保卫处', type: '安全反馈', estimated: 4, difficulty: 2, reward: 2, filled: 34, total: 100 },
  { id: 't24', title: '选修课程推荐', subtitle: '你最推荐的选修课', sender: '教务处', type: '课程推荐', estimated: 4, difficulty: 2, reward: 2, filled: 112, total: 200 },
  { id: 't25', title: '毕业旅行计划', subtitle: '目的地与预算调查', sender: '旅游协会', type: '活动策划', estimated: 6, difficulty: 2, reward: 2, filled: 56, total: 120 },
  { id: 't26', title: '线上学习效果评估', subtitle: '网课体验与改进建议', sender: '教学办', type: '教学反馈', estimated: 7, difficulty: 3, reward: 3, filled: 78, total: 150 },
  { id: 't27', title: '校园美食地图', subtitle: '推荐你喜欢的餐厅', sender: '美食社', type: '生活分享', estimated: 4, difficulty: 1, reward: 1, filled: 145, total: 300 },
  { id: 't28', title: '环保意识调查', subtitle: '垃圾分类与节能习惯', sender: '环保协会', type: '环保调研', estimated: 5, difficulty: 2, reward: 2, filled: 67, total: 150 },
  { id: 't29', title: '寒假实践活动', subtitle: '实践类型与收获分享', sender: '团委', type: '实践总结', estimated: 8, difficulty: 3, reward: 3, filled: 23, total: 80 },
  { id: 't30', title: '校园文创产品设计', subtitle: '你想要的校园周边', sender: '学生会', type: '创意征集', estimated: 6, difficulty: 3, reward: 3, filled: 45, total: 100 },
  { id: 't31', title: '奖学金评定意见', subtitle: '评定标准合理性反馈', sender: '学工处', type: '制度反馈', estimated: 7, difficulty: 3, reward: 3, filled: 34, total: 80 },
  { id: 't32', title: '通勤方式调查', subtitle: '上下学交通工具选择', sender: '后勤部', type: '交通调研', estimated: 3, difficulty: 1, reward: 1, filled: 167, total: 250 },
  { id: 't33', title: '考试周压力调查', subtitle: '备考状态与心理压力', sender: '心理中心', type: '健康调研', estimated: 6, difficulty: 3, reward: 3, filled: 89, total: 150 },
  { id: 't34', title: '社团招新建议', subtitle: '招新方式与宣传效果', sender: '社团联', type: '活动优化', estimated: 5, difficulty: 2, reward: 2, filled: 56, total: 120 },
  { id: 't35', title: '宿舍文化建设', subtitle: '宿舍氛围与活动建议', sender: '宿管部', type: '文化建设', estimated: 6, difficulty: 2, reward: 2, filled: 78, total: 150 },
  { id: 't36', title: '就业指导需求', subtitle: '需要的就业辅导服务', sender: '就业中心', type: '服务需求', estimated: 7, difficulty: 3, reward: 3, filled: 45, total: 100 },
])

const visibleTasks = ref([])

function pickBatch(pool, size) {
  const shuffled = [...pool].sort(() => Math.random() - 0.5)
  const count = Math.min(size || optimalTaskCount.value, pool.length)
  return shuffled.slice(0, count)
}

// 监听最佳数量变化，自动调整显示数量
watch(optimalTaskCount, (newCount, oldCount) => {
  if (newCount !== oldCount && visibleTasks.value.length > 0) {
    const currentIds = new Set(visibleTasks.value.map(t => t.id))
    
    if (newCount > visibleTasks.value.length) {
      // 需要增加问卷
      const needed = newCount - visibleTasks.value.length
      const candidates = allTasks.value.filter(t => !currentIds.has(t.id))
      const shuffled = [...candidates].sort(() => Math.random() - 0.5)
      const toAdd = shuffled.slice(0, needed)
      visibleTasks.value = [...visibleTasks.value, ...toAdd]
    } else if (newCount < visibleTasks.value.length) {
      // 需要减少问卷
      visibleTasks.value = visibleTasks.value.slice(0, newCount)
    }
  }
})

function refreshBatch() {
  const confirm = window.confirm('确认要换一批问卷吗？当前页面的问卷将被替换。')
  if (!confirm) return
  const currentSize = visibleTasks.value.length
  visibleTasks.value = pickBatch(allTasks.value, currentSize)
}

function handleDelete(taskId) {
  const ok = window.confirm('确认删除该问卷吗？将自动补位新的问卷。')
  if (!ok) return

  // 找到要删除的任务在数组中的索引
  const index = visibleTasks.value.findIndex((t) => t.id === taskId)
  if (index === -1) return

  // 获取当前显示的所有问卷ID
  const usedIds = new Set(visibleTasks.value.map((t) => t.id))
  // 移除被删除的问卷
  usedIds.delete(taskId)
  // 从所有问卷中找出还未显示的问卷
  const candidates = allTasks.value.filter((t) => !usedIds.has(t.id))
  // 随机选择一份未显示的问卷作为补位
  const replacement = candidates.length > 0 ? candidates[Math.floor(Math.random() * candidates.length)] : null

  if (replacement) {
    // 使用新问卷替换被删除的问卷
    visibleTasks.value = [
      ...visibleTasks.value.slice(0, index),
      replacement,
      ...visibleTasks.value.slice(index + 1)
    ]
  } else {
    // 如果没有可替换的问卷，直接删除
    visibleTasks.value = [
      ...visibleTasks.value.slice(0, index),
      ...visibleTasks.value.slice(index + 1)
    ]
  }
}

const filteredTasks = computed(() => {
  if (!keyword.value.trim()) return visibleTasks.value
  const q = keyword.value.trim().toLowerCase()
  return visibleTasks.value.filter((task) =>
    [task.title, task.subtitle, task.sender, task.type].some((field) => field.toLowerCase().includes(q))
  )
})

function progressPercent(task) {
  if (!task.total) return 0
  return Math.min(100, Math.round((task.filled / task.total) * 100))
}

// 根据难度显示分类（只有高性价比和挑战任务两种）
function getMatchClass(task) {
  if (task.difficulty <= 2) return 'high-match'
  return 'low-match'
}

function getMatchText(task) {
  if (task.difficulty <= 2) return '高性价比'
  return '挑战任务'
}
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
