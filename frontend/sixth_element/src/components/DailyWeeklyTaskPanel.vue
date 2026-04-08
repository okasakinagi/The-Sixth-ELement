<template>
  <section class="task-panel">
    <div class="task-panel-header">
      <div class="task-panel-title">
        <span class="task-panel-badge">{{ activeTab === 'daily' ? '每日任务' : '每周任务' }}</span>
        <span class="task-red-dot" v-if="hasClaimable">●</span>
      </div>
      <div class="task-panel-tabs">
        <button :class="['tab-btn', { active: activeTab === 'daily' }]" @click="switchTab('daily')">今日</button>
        <button :class="['tab-btn', { active: activeTab === 'weekly' }]" @click="switchTab('weekly')">本周</button>
      </div>
      <button class="task-panel-toggle" @click="collapsed = !collapsed">
        {{ collapsed ? '展开 ▾' : '收起 ▴' }}
      </button>
    </div>

    <div v-if="!collapsed">
      <div v-if="loading" class="task-loading">加载中...</div>
      <div v-else class="task-list">
        <div
          v-for="task in tasks"
          :key="task.code"
          class="task-item"
          :class="{
            'task-item--claimed': task.claimed,
            'task-item--claimable': task.claimable,
          }"
        >
          <div class="task-item-left">
            <p class="task-desc">{{ task.desc }}</p>
            <div class="task-progress-row">
              <div class="task-bar">
                <div
                  class="task-bar-fill"
                  :style="{ width: Math.min(100, task.progress / task.target * 100) + '%' }"
                ></div>
              </div>
              <span class="task-progress-text">{{ task.progress }}/{{ task.target }}</span>
            </div>
          </div>
          <div class="task-item-right">
            <span class="task-reward">+{{ task.reward_exp }}EXP  +{{ task.reward_points }}积分</span>
            <button
              v-if="task.claimable"
              class="claim-btn"
              :disabled="claiming === task.code"
              @click="handleClaim(task)"
            >
              {{ claiming === task.code ? '...' : '领取' }}
            </button>
            <span v-else-if="task.claimed" class="claimed-tag">✓ 已领取</span>
            <span v-else class="pending-tag">进行中</span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getDailyTasks, getWeeklyTasks, claimTask } from '@/utils/levelApi'

const props = defineProps({ visible: { type: Boolean, default: true } })
const router = useRouter()
const activeTab = ref('daily')
const collapsed = ref(false)
const loading = ref(false)
const tasks = ref([])
const claiming = ref(null)

const hasClaimable = computed(() => tasks.value.some(t => t.claimable))

async function loadTasks(tab) {
  loading.value = true
  try {
    const data = tab === 'daily'
      ? await getDailyTasks(router)
      : await getWeeklyTasks(router)
    tasks.value = Array.isArray(data.tasks) ? data.tasks : []
  } catch (e) {
    console.error('加载任务失败:', e)
    tasks.value = []
  } finally {
    loading.value = false
  }
}

function switchTab(tab) {
  activeTab.value = tab
  loadTasks(tab)
}

async function handleClaim(task) {
  claiming.value = task.code
  try {
    await claimTask(task.code, router)
    task.claimed = true
    task.claimable = false
  } catch (e) {
    const msg = e?.message || ''
    if (msg.includes('已领取')) {
      task.claimed = true
      task.claimable = false
    } else {
      alert('领取失败，请稍后重试')
    }
  } finally {
    claiming.value = null
  }
}

onMounted(() => loadTasks('daily'))
</script>

<style scoped>
.task-panel {
  background: #ffffff;
  border: 1px solid #e3e9f5;
  border-radius: 14px;
  padding: 14px 16px;
  box-shadow: 0 6px 20px rgba(0, 82, 217, 0.05);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.task-panel-title {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
}

.task-panel-badge {
  background: linear-gradient(135deg, #ff6b6b, #ee5a6f);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 20px;
  letter-spacing: 0.06em;
}

.task-red-dot {
  color: #f44336;
  font-size: 10px;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.task-panel-tabs {
  display: flex;
  gap: 4px;
}

.tab-btn {
  padding: 5px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid #d7e3ff;
  background: #fff;
  color: #5c7599;
  transition: all 0.2s;
}

.tab-btn.active {
  background: #0052d9;
  color: #fff;
  border-color: #0052d9;
}

.task-panel-toggle {
  background: none;
  border: 1px solid #d7e3ff;
  border-radius: 8px;
  padding: 5px 12px;
  font-size: 12px;
  color: #0052d9;
  cursor: pointer;
  font-weight: 600;
  flex-shrink: 0;
}

.task-loading {
  text-align: center;
  color: #5c7599;
  font-size: 13px;
  padding: 12px 0;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: #f6f8fb;
  border: 1px solid #e3e9f5;
  border-radius: 10px;
  padding: 10px 14px;
  transition: box-shadow 0.2s;
}

.task-item--claimable {
  border-color: #ffd700;
  background: linear-gradient(135deg, #fffde7, #fff8e1);
}

.task-item--claimed {
  opacity: 0.6;
}

.task-item-left {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.task-desc {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #0b2b66;
}

.task-progress-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.task-bar {
  flex: 1;
  height: 6px;
  background: #e3e9f5;
  border-radius: 999px;
  overflow: hidden;
}

.task-bar-fill {
  height: 100%;
  background: linear-gradient(135deg, #0052d9, #2f7bff);
  border-radius: 999px;
  transition: width 0.3s ease;
}

.task-progress-text {
  font-size: 11px;
  color: #5c7599;
  white-space: nowrap;
}

.task-item-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  flex-shrink: 0;
}

.task-reward {
  font-size: 11px;
  color: #7a5800;
  font-weight: 500;
  white-space: nowrap;
}

.claim-btn {
  padding: 5px 14px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  border: none;
  background: linear-gradient(135deg, #ffd700, #ffb400);
  color: #333;
  box-shadow: 0 2px 8px rgba(255, 180, 0, 0.3);
  transition: filter 0.2s;
}

.claim-btn:hover { filter: brightness(1.08); }
.claim-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.claimed-tag {
  font-size: 12px;
  color: #4caf50;
  font-weight: 600;
}

.pending-tag {
  font-size: 12px;
  color: #8ca0be;
}
</style>
