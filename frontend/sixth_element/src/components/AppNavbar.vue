<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getUserLevel } from '@/utils/levelApi'

const router = useRouter()
const route = useRoute()
const levelInfo = ref(null)

const userInitial = computed(() => {
  const nickname = localStorage.getItem('user_nickname') || ''
  return nickname.charAt(0).toUpperCase() || '?'
})

onMounted(async () => {
  if (localStorage.getItem('access_token')) {
    try {
      levelInfo.value = await getUserLevel(router)
    } catch (e) {}
  }
})

function handleLogout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user_id')
  localStorage.removeItem('user_nickname')
  router.push('/login')
}

function isActive(routeName) {
  return route.name === routeName
}
</script>

<template>
  <nav class="app-navbar">
    <div class="navbar-left">
      <RouterLink to="/" class="navbar-logo">
        <span>📚 第六元素</span>
      </RouterLink>
    </div>

    <div class="navbar-center">
      <RouterLink
        to="/task-hall"
        :class="['navbar-link', { active: isActive('task-hall') }]"
      >
        📋 任务大厅
      </RouterLink>
      <RouterLink
        to="/contacts"
        :class="['navbar-link', { active: isActive('contacts') }]"
      >
        👥 伙伴与组队
      </RouterLink>
      <RouterLink
        to="/surveys"
        :class="['navbar-link', { active: isActive('survey-management') }]"
      >
        📝 问卷管理
      </RouterLink>
      <RouterLink
        to="/points"
        :class="['navbar-link', { active: isActive('points-record') }]"
      >
        💰 积分记录
      </RouterLink>
    </div>

    <div class="navbar-right">
      <div v-if="levelInfo" class="level-indicator">
        <div class="level-badge">
          <span class="level-num">Lv{{ levelInfo.level }}</span>
          <span class="level-title-nav">{{ levelInfo.title }}</span>
        </div>
        <div class="exp-mini-bar">
          <div class="exp-mini-fill" :style="{ width: levelInfo.progress_pct + '%' }"></div>
        </div>
        <span class="exp-text">{{ levelInfo.exp_in_level }}/{{ levelInfo.exp_to_next }}</span>
      </div>
      <RouterLink
        to="/profile"
        :class="['navbar-link', 'profile-link', { active: isActive('profile') }]"
      >
        <span class="navbar-avatar">{{ userInitial }}</span>
        个人资料
      </RouterLink>
      <button class="navbar-logout" @click="handleLogout">登出</button>
    </div>
  </nav>
</template>

<style scoped>
.app-navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 32px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid #e8eef5;
  position: sticky;
  top: 0;
  z-index: 100;
  gap: 24px;
}

.navbar-left {
  flex-shrink: 0;
}

.navbar-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #1e4fb4;
  text-decoration: none;
  font-weight: 700;
  font-size: 16px;
  transition: all 0.2s ease;
}

.navbar-logo:hover {
  transform: scale(1.05);
}

.navbar-center {
  flex-grow: 1;
  display: flex;
  gap: 8px;
  justify-content: center;
}

.navbar-right {
  flex-shrink: 0;
  display: flex;
  gap: 8px;
  align-items: center;
}

.navbar-link {
  color: #637089;
  text-decoration: none;
  font-weight: 500;
  padding: 8px 14px;
  border-radius: 6px;
  transition: all 0.2s ease;
  font-size: 14px;
  white-space: nowrap;
}

.navbar-link:hover {
  color: #1e4fb4;
  background: rgba(30, 79, 180, 0.08);
}

.navbar-link.active {
  color: #1e4fb4;
  background: rgba(30, 79, 180, 0.12);
  font-weight: 600;
}

.navbar-logout {
  padding: 6px 14px;
  background: transparent;
  border: 1px solid #e8eef5;
  border-radius: 6px;
  color: #637089;
  cursor: pointer;
  font-weight: 500;
  font-size: 14px;
  transition: all 0.2s ease;
}

.navbar-logout:hover {
  background: #d32f2f;
  color: white;
  border-color: #d32f2f;
}

.navbar-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, #42a5f5, #1976d2);
  color: white;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.profile-link {
  display: flex;
  align-items: center;
  gap: 6px;
}

.level-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: linear-gradient(135deg, #f8fafc, #f1f5f9);
  border: 1px solid #e2e8f0;
  border-radius: 20px;
}

.level-badge {
  display: flex;
  align-items: center;
  gap: 4px;
}

.level-num {
  font-size: 13px;
  font-weight: 700;
  color: #1e3a5f;
  background: linear-gradient(135deg, #ffd700, #ffb400);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.level-title-nav {
  font-size: 11px;
  color: #64748b;
  font-weight: 500;
}

.exp-mini-bar {
  width: 48px;
  height: 4px;
  background: #e2e8f0;
  border-radius: 2px;
  overflow: hidden;
}

.exp-mini-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.exp-text {
  font-size: 10px;
  color: #94a3b8;
  font-weight: 500;
  min-width: 40px;
}

@media (max-width: 768px) {
  .app-navbar {
    padding: 12px 16px;
    gap: 12px;
  }

  .navbar-center {
    gap: 4px;
  }

  .navbar-link {
    padding: 6px 10px;
    font-size: 13px;
  }

  .navbar-logo {
    font-size: 14px;
  }

  .navbar-logout {
    padding: 6px 10px;
  }
}

@media (max-width: 480px) {
  .app-navbar {
    flex-wrap: wrap;
    padding: 8px 12px;
  }

  .navbar-right {
    order: 2;
    width: 100%;
    justify-content: flex-end;
    border-top: 1px solid #e8eef5;
    padding-top: 6px;
    flex-wrap: wrap;
    gap: 6px;
  }

  .level-indicator {
    order: -1;
    padding: 4px 10px;
  }

  .exp-mini-bar {
    width: 36px;
  }

  .navbar-center {
    order: 3;
    width: 100%;
    flex-wrap: wrap;
    border-top: 1px solid #e8eef5;
    padding-top: 6px;
  }

  .navbar-link {
    flex: 1 1 45%;
    text-align: center;
    padding: 6px 8px;
    font-size: 12px;
  }

  .navbar-logo {
    font-size: 13px;
  }

  .navbar-logout {
    padding: 5px 12px;
    font-size: 12px;
  }
}
</style>
