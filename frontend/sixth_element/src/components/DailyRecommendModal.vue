<template>
  <Teleport to="body">
    <div v-if="visible" class="dr-overlay" @click.self="$emit('close')">
      <div class="dr-modal">
        <div class="dr-header">
          <div class="dr-title-block">
            <span class="dr-badge">每日推荐</span>
            <h2>今日为你推荐</h2>
            <p class="dr-sub">基于你的兴趣个性化挑选，完成可获额外奖励</p>
          </div>
          <button class="dr-close" @click="$emit('close')" aria-label="关闭">×</button>
        </div>

        <div v-if="loading" class="dr-loading">加载中...</div>

        <div v-else-if="items.length === 0" class="dr-empty">暂无推荐，稍后再来看看</div>

        <div v-else class="dr-list">
          <div
            v-for="item in items"
            :key="item.id"
            class="dr-card"
            :class="{ 'dr-card--claimed': item.bonus_claimed }"
          >
            <div class="dr-card-top">
              <h3 class="dr-card-title">{{ item.title }}</h3>
              <div class="dr-card-meta">
                <span class="dr-pill">⏱ {{ item.estimated }}min</span>
                <span class="dr-pill dr-pill--reward">+{{ item.reward }} 积分</span>
              </div>
            </div>
            <p class="dr-reason">{{ item.match_reason }}</p>
            <div class="dr-card-actions">
              <button class="dr-btn dr-btn--fill" @click="goFill(item)">去填写</button>
              <button
                v-if="!item.bonus_claimed"
                class="dr-btn dr-btn--bonus"
                :disabled="claiming === item.id"
                @click="handleClaim(item)"
              >
                {{ claiming === item.id ? '领取中...' : '领取奖励' }}
              </button>
              <span v-else class="dr-claimed-tag">✓ 已领取</span>
            </div>
          </div>
        </div>

        <p class="dr-hint">奖励：完成后额外获得 +2 经验 / +1 积分</p>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getDailyRecommendations, claimDailyBonus } from '@/utils/taskHallApi'

const props = defineProps({ visible: Boolean })
const emit = defineEmits(['close'])

const router = useRouter()
const loading = ref(false)
const items = ref([])
const claiming = ref(null)

watch(
  () => props.visible,
  async (val) => {
    if (!val) return
    loading.value = true
    try {
      const data = await getDailyRecommendations(router)
      items.value = Array.isArray(data.items) ? data.items : []
    } catch (e) {
      console.error('获取每日推荐失败:', e)
      items.value = []
    } finally {
      loading.value = false
    }
  }
)

function extractRawId(publicId) {
  if (!publicId || typeof publicId !== 'string') return publicId
  const m = publicId.match(/^s_(\d+)$/)
  return m ? m[1] : publicId
}

function goFill(item) {
  const rawId = extractRawId(item.id)
  emit('close')
  router.push({ name: 'survey-fill', params: { id: String(rawId) } })
}

async function handleClaim(item) {
  claiming.value = item.id
  try {
    const rawId = extractRawId(item.id)
    await claimDailyBonus(rawId, router)
    item.bonus_claimed = true
  } catch (e) {
    const msg = e?.message || ''
    if (msg.includes('先完成')) {
      alert('请先完成该问卷，再来领取奖励哦～')
    } else if (msg.includes('已领取')) {
      item.bonus_claimed = true
    } else {
      alert('领取失败，请稍后重试')
    }
  } finally {
    claiming.value = null
  }
}
</script>

<style scoped>
.dr-overlay {
  position: fixed;
  inset: 0;
  background: rgba(11, 43, 102, 0.45);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.dr-modal {
  background: #ffffff;
  border-radius: 20px;
  width: 100%;
  max-width: 560px;
  max-height: 90vh;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: 0 24px 64px rgba(0, 82, 217, 0.18);
}

.dr-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.dr-title-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dr-badge {
  display: inline-block;
  background: linear-gradient(135deg, #0052d9, #2f7bff);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  padding: 3px 10px;
  border-radius: 20px;
  width: fit-content;
}

.dr-title-block h2 {
  margin: 0;
  font-size: 20px;
  color: #0b2b66;
  font-weight: 700;
}

.dr-sub {
  margin: 0;
  font-size: 13px;
  color: #5c7599;
}

.dr-close {
  background: none;
  border: none;
  font-size: 24px;
  color: #5c7599;
  cursor: pointer;
  line-height: 1;
  padding: 0 4px;
  flex-shrink: 0;
}

.dr-close:hover { color: #0b2b66; }

.dr-loading,
.dr-empty {
  text-align: center;
  color: #5c7599;
  padding: 24px 0;
  font-size: 14px;
}

.dr-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dr-card {
  background: #f6f8fb;
  border: 1px solid #e3e9f5;
  border-radius: 14px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: box-shadow 0.2s;
}

.dr-card:hover {
  box-shadow: 0 6px 18px rgba(0, 82, 217, 0.08);
}

.dr-card--claimed {
  opacity: 0.7;
}

.dr-card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}

.dr-card-title {
  margin: 0;
  font-size: 15px;
  color: #0b2b66;
  font-weight: 600;
  flex: 1;
}

.dr-card-meta {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.dr-pill {
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 600;
  background: #eef3ff;
  border: 1px solid #d7e3ff;
  color: #0b2b66;
  white-space: nowrap;
}

.dr-pill--reward {
  background: linear-gradient(135deg, #fff8e1, #ffecb3);
  border-color: #ffe082;
  color: #7a5800;
}

.dr-reason {
  margin: 0;
  font-size: 13px;
  color: #2e7d32;
  font-weight: 500;
}

.dr-card-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.dr-btn {
  padding: 7px 14px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.dr-btn--fill {
  background: #0052d9;
  color: #fff;
}

.dr-btn--fill:hover { background: #003faa; }

.dr-btn--bonus {
  background: linear-gradient(135deg, #ffd700, #ffb400);
  color: #333;
}

.dr-btn--bonus:hover { filter: brightness(1.05); }

.dr-btn--bonus:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.dr-claimed-tag {
  font-size: 13px;
  font-weight: 600;
  color: #4caf50;
}

.dr-hint {
  margin: 0;
  text-align: center;
  font-size: 12px;
  color: #8ca0be;
}
</style>
