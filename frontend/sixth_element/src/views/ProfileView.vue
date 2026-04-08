<script setup>
import { useRouter } from 'vue-router'
import { ref, onMounted } from 'vue'
import { getUserLevel } from '@/utils/levelApi'

const router = useRouter()
const levelInfo = ref(null)

onMounted(async () => {
  if (localStorage.getItem('access_token')) {
    try {
      levelInfo.value = await getUserLevel(router)
    } catch (e) {}
  }
})

const goBack = () => {
  router.back()
}
</script>

<template>
  <div class="profile">
    <div class="profile-shell">
      <header class="header">
        <div class="title-block">
          <p class="kicker">Profile</p>
          <h1>个人信息</h1>
        </div>
        <div class="actions">
          <button class="ghost" type="button" @click="goBack">← 返回</button>
        </div>
      </header>
      <section class="profile-grid">
        <div class="profile-card">
          <p class="label">昵称</p>
          <p class="value">PL</p>
        </div>
        <div class="profile-card">
          <p class="label">账号类型</p>
          <p class="value">企业管理员</p>
        </div>
        <div class="profile-card">
          <p class="label">积分余额</p>
          <p class="value">1,240</p>
        </div>
      </section>

      <!-- 等级卡片 -->
      <section v-if="levelInfo" class="level-card">
        <div class="level-card-left">
          <div class="level-badge-big">Lv{{ levelInfo.level }}</div>
          <div class="level-text">
            <p class="level-title">{{ levelInfo.title }}</p>
            <p class="level-exp">{{ levelInfo.exp }} EXP</p>
          </div>
        </div>
        <div class="level-card-right">
          <div class="exp-bar-label">
            <span>本级进度</span>
            <span v-if="!levelInfo.is_max_level">{{ levelInfo.exp_in_level }} / {{ levelInfo.exp_to_next }}</span>
            <span v-else>已满级</span>
          </div>
          <div class="exp-bar">
            <div class="exp-bar-fill" :style="{ width: levelInfo.progress_pct + '%' }"></div>
          </div>
          <p v-if="!levelInfo.is_max_level" class="level-next">下一称号：{{ levelInfo.next_title }}（Lv{{ levelInfo.next_level }}）</p>
          <p v-else class="level-next">🌟 已达最高等级</p>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.profile {
  min-height: 100vh;
  padding: 12px 10px 20px;
  background: #f6f8fb;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.profile-shell {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.header {
  background: #ffffff;
  border: 1px solid #e3e9f5;
  border-radius: 14px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
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
}

.ghost {
  color: #0052d9;
  background: none;
  border: none;
  padding: 8px 14px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.ghost:hover {
  background: rgba(0, 82, 217, 0.1);
  transform: translateX(-2px);
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: #5c7599;
  margin: 0 0 6px;
}

.value {
  font-weight: 600;
  font-size: 18px;
  color: #0b2b66;
  margin: 0;
}

.profile-card {
  background: #ffffff;
  border: 1px solid #e3e9f5;
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 8px 20px rgba(0, 82, 217, 0.05);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

@media (max-width: 640px) {
  .header {
    flex-direction: column;
    align-items: flex-start;
  }
}

.level-card {
  background: #ffffff;
  border: 1px solid #e3e9f5;
  border-radius: 14px;
  padding: 18px 20px;
  box-shadow: 0 8px 20px rgba(0, 82, 217, 0.05);
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.level-card-left {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-shrink: 0;
}

.level-badge-big {
  background: linear-gradient(135deg, #ffd700, #ffb400);
  color: #333;
  border-radius: 14px;
  padding: 10px 18px;
  font-size: 22px;
  font-weight: 800;
  box-shadow: 0 4px 12px rgba(255, 180, 0, 0.3);
}

.level-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #0b2b66;
}

.level-exp {
  margin: 4px 0 0;
  font-size: 13px;
  color: #5c7599;
}

.level-card-right {
  flex: 1;
  min-width: 200px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.exp-bar-label {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #5c7599;
}

.exp-bar {
  height: 10px;
  background: #edf1f7;
  border-radius: 999px;
  overflow: hidden;
}

.exp-bar-fill {
  height: 100%;
  background: linear-gradient(135deg, #0052d9, #2f7bff);
  border-radius: 999px;
  transition: width 0.4s ease;
}

.level-next {
  margin: 0;
  font-size: 12px;
  color: #5c7599;
}
</style>
