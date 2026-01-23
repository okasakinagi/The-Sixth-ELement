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

      <div class="nav-right">
        <RouterLink class="nav-btn" to="/surveys">问卷管理</RouterLink>
        <RouterLink class="avatar" to="/profile" aria-label="个人信息">
          <span>U</span>
        </RouterLink>
      </div>
    </header>

    <section class="task-grid">
      <article
        v-for="(task, idx) in filteredTasks"
        :key="task.id"
        class="task-card"
        @contextmenu.prevent="handleDelete(idx)"
      >
        <div class="card-top">
          <div class="card-titles">
            <p class="sender">{{ task.sender }}</p>
            <h3>{{ task.title }}</h3>
            <p class="subtitle">{{ task.subtitle }}</p>
          </div>
          <div class="meta">
            <span class="pill type">{{ task.type }}</span>
            <span class="pill time">约 {{ task.estimated }} 分钟</span>
          </div>
        </div>

        <div class="card-middle">
          <div class="badge">
            <span class="label">难度</span>
            <div class="stars">
              <span v-for="n in 5" :key="n" :class="{ active: n <= task.difficulty }">★</span>
            </div>
          </div>
          <div class="badge">
            <span class="label">奖励</span>
            <span class="points">+{{ task.reward }} 积分</span>
          </div>
        </div>

        <div class="card-bottom">
          <div class="progress">
            <div class="progress-bar" :style="{ width: progressPercent(task) + '%' }"></div>
          </div>
          <div class="progress-text">{{ task.filled }} / {{ task.total }}</div>
        </div>
      </article>
    </section>

    <RouterLink class="fab" to="/survey/new" aria-label="新建问卷">+</RouterLink>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const keyword = ref('')

const allTasks = ref([
  { id: 't01', title: '校园生活满意度调查', subtitle: '宿舍、食堂、安保整体反馈', sender: '李同学', type: '校园调研', estimated: 6, difficulty: 2, reward: 3, filled: 54, total: 200 },
  { id: 't02', title: '课程体验回访', subtitle: '这学期的主要课程体验', sender: '张老师', type: '教学反馈', estimated: 8, difficulty: 3, reward: 4, filled: 120, total: 260 },
  { id: 't03', title: '食堂新品口味投票', subtitle: '为春季菜单挑选新品', sender: '后勤部', type: '投票', estimated: 3, difficulty: 1, reward: 2, filled: 82, total: 150 },
  { id: 't04', title: '社团活动偏好', subtitle: '选出你想参加的活动', sender: '学生会', type: '兴趣画像', estimated: 5, difficulty: 2, reward: 3, filled: 33, total: 100 },
  { id: 't05', title: '实习就业意向', subtitle: '求职方向、城市与行业偏好', sender: '就业中心', type: '就业调研', estimated: 7, difficulty: 3, reward: 4, filled: 45, total: 120 },
  { id: 't06', title: '心理健康与压力', subtitle: '期末周的压力与缓解方式', sender: '心理中心', type: '健康问卷', estimated: 9, difficulty: 4, reward: 5, filled: 18, total: 80 },
  { id: 't07', title: '图书馆使用体验', subtitle: '空间、座位、设备反馈', sender: '图书馆', type: '服务反馈', estimated: 4, difficulty: 2, reward: 3, filled: 210, total: 400 },
  { id: 't08', title: '校园出行与班车', subtitle: '线路、班次与满意度调查', sender: '后勤部', type: '交通', estimated: 4, difficulty: 2, reward: 3, filled: 60, total: 180 },
  { id: 't09', title: '新生入学指南优化', subtitle: '帮我们改进 2026 新生手册', sender: '教务处', type: '文案优化', estimated: 10, difficulty: 4, reward: 5, filled: 12, total: 60 },
  { id: 't10', title: '赛事观众调研', subtitle: '校运动会观众体验反馈', sender: '体育部', type: '活动复盘', estimated: 6, difficulty: 2, reward: 3, filled: 140, total: 260 },
  { id: 't11', title: '校友访谈邀约', subtitle: '愿意参加校友访谈的时间', sender: '校友办', type: '访谈邀约', estimated: 5, difficulty: 3, reward: 4, filled: 28, total: 90 },
  { id: 't12', title: '科研助理机会', subtitle: '可接受的课题与工作量', sender: '科研办', type: '科研匹配', estimated: 12, difficulty: 5, reward: 5, filled: 8, total: 50 },
  { id: 't13', title: '寝室卫生公约共识', subtitle: '共建寝室卫生标准', sender: '宿管部', type: '共识投票', estimated: 3, difficulty: 1, reward: 2, filled: 76, total: 120 },
  { id: 't14', title: '艺术节节目征集', subtitle: '报名你想展示的节目', sender: '文艺部', type: '活动报名', estimated: 5, difficulty: 2, reward: 3, filled: 34, total: 100 },
  { id: 't15', title: '志愿服务档期收集', subtitle: '收集可出勤的志愿时段', sender: '团委', type: '志愿服务', estimated: 4, difficulty: 2, reward: 3, filled: 95, total: 180 },
])

const visibleTasks = ref(pickBatch(allTasks.value))

function pickBatch(pool) {
  const shuffled = [...pool].sort(() => Math.random() - 0.5)
  return shuffled.slice(0, 10)
}

function refreshBatch() {
  visibleTasks.value = pickBatch(allTasks.value)
}

function handleDelete(index) {
  const ok = window.confirm('确认删除该问卷吗？将自动补位新的问卷。')
  if (!ok) return

  const usedIds = new Set(visibleTasks.value.map((t) => t.id))
  const candidates = allTasks.value.filter((t) => !usedIds.has(t.id))
  const replacement = candidates.length ? candidates[Math.floor(Math.random() * candidates.length)] : null

  if (replacement) {
    visibleTasks.value.splice(index, 1, replacement)
  } else {
    visibleTasks.value.splice(index, 1)
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
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
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

.sender {
  margin: 0;
  font-size: 13px;
  color: #7a8ca6;
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
}

.pill.time {
  background: #f4f9ff;
}

.card-middle {
  display: flex;
  gap: 12px;
  align-items: center;
}

.badge {
  background: #f7f9fc;
  border: 1px solid #e3e9f5;
  border-radius: 12px;
  padding: 8px 10px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
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
  gap: 10px;
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
}

.progress-text {
  min-width: 72px;
  text-align: right;
  font-size: 12px;
  color: #48607f;
}

.fab {
  position: fixed;
  right: 20px;
  bottom: 20px;
  width: 54px;
  height: 54px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0052d9, #2f7bff);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  text-decoration: none;
  box-shadow: 0 14px 30px rgba(0, 82, 217, 0.25);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.fab:hover {
  transform: translateY(-2px);
  box-shadow: 0 18px 36px rgba(0, 82, 217, 0.28);
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
}

@media (max-width: 640px) {
  .task-hall {
    padding: 10px 8px 16px;
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
}
</style>
