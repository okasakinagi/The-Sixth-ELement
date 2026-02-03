<template>
  <div
    v-if="isLoggedIn"
    class="global-floating-menu"
    :class="{ 'is-dragging': dragState.isDragging }"
    ref="menuRef"
    :style="{ left: menuPosition.x + 'px', top: menuPosition.y + 'px' }"
    @mousedown="startDrag"
    @touchstart="startDrag"
  >
    <div class="drag-handle">⋮⋮</div>
    <RouterLink 
      class="points-badge" 
      to="/points"
      @click="handleLinkClick"
    >
      <span class="points-icon">💰</span>
      <span class="points-value">{{ userPoints }}</span>
    </RouterLink>
    <RouterLink 
      class="avatar" 
      to="/profile" 
      aria-label="个人信息"
      @click="handleLinkClick"
    >
      <span>U</span>
    </RouterLink>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 状态
const userPoints = ref(0)
const menuRef = ref(null)
const menuPosition = ref({ x: 0, y: 0 })
const dragState = ref({ isDragging: false, startX: 0, startY: 0, initialX: 0, initialY: 0 })

// 检查是否登录
const isLoggedIn = computed(() => {
  return !!localStorage.getItem('access_token')
})

// 从API获取积分
async function fetchUserPoints() {
  if (!isLoggedIn.value) {
    userPoints.value = 0
    return
  }

  try {
    const token = localStorage.getItem('access_token')
    const res = await fetch('/api/v1/users/me', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (res.ok) {
      const data = await res.json()
      userPoints.value = data.points || 0
      
      // 同步更新localStorage
      const profile = localStorage.getItem('sixth_element_profile')
      if (profile) {
        const userData = JSON.parse(profile)
        userData.points = data.points || 0
        localStorage.setItem('sixth_element_profile', JSON.stringify(userData))
      } else {
        localStorage.setItem('sixth_element_profile', JSON.stringify({
          id: data.id,
          email: data.email,
          nickname: data.nickname,
          points: data.points || 0,
          credit_score: data.credit_score || 80,
          activity_points: data.activity_points || 0
        }))
      }
    }
  } catch (error) {
    console.error('获取积分失败:', error)
  }
}

// 拖拽相关
let rafId = null
const DRAG_THRESHOLD = 5 // 拖动阈值，超过5px才认为是拖动

function startDrag(e) {
  const clientX = e.type.includes('touch') ? e.touches[0]?.clientX : e.clientX
  const clientY = e.type.includes('touch') ? e.touches[0]?.clientY : e.clientY

  if (!clientX || !clientY) return

  dragState.value = {
    isDragging: true,
    startX: clientX,
    startY: clientY,
    initialX: menuPosition.value.x,
    initialY: menuPosition.value.y,
    hasMoved: false
  }

  document.addEventListener('mousemove', onDrag, { passive: false })
  document.addEventListener('mouseup', stopDrag)
  document.addEventListener('touchmove', onDrag, { passive: false })
  document.addEventListener('touchend', stopDrag)
}

function onDrag(e) {
  if (!dragState.value.isDragging) return
  
  // 阻止默认行为（防止触摸滚动）
  e.preventDefault()
  
  const clientX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX
  const clientY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY

  const deltaX = clientX - dragState.value.startX
  const deltaY = clientY - dragState.value.startY
  
  // 检查是否超过拖动阈值
  const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY)
  if (distance > DRAG_THRESHOLD) {
    dragState.value.hasMoved = true
  }

  // 使用 requestAnimationFrame 优化性能
  if (rafId) {
    cancelAnimationFrame(rafId)
  }

  rafId = requestAnimationFrame(() => {
    const newX = dragState.value.initialX + deltaX
    const newY = dragState.value.initialY + deltaY

    // 限制在视口范围内
    const maxX = window.innerWidth - (menuRef.value?.offsetWidth || 200)
    const maxY = window.innerHeight - (menuRef.value?.offsetHeight || 60)

    menuPosition.value = {
      x: Math.max(0, Math.min(newX, maxX)),
      y: Math.max(0, Math.min(newY, maxY))
    }
  })
}

function stopDrag() {
  dragState.value.isDragging = false
  
  if (rafId) {
    cancelAnimationFrame(rafId)
    rafId = null
  }

  // 停止拖动时才保存位置（避免频繁写localStorage）
  localStorage.setItem('floating_menu_position', JSON.stringify(menuPosition.value))

  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', stopDrag)
}

// 防止拖动后触发链接点击
function handleLinkClick(e) {
  if (dragState.value.hasMoved) {
    e.preventDefault()
    e.stopPropagation()
    dragState.value.hasMoved = false
  }
}

// 页面可见性变化时刷新积分
function handleVisibilityChange() {
  if (!document.hidden && isLoggedIn.value) {
    fetchUserPoints()
  }
}

// 路由变化时刷新积分
function handleRouteChange() {
  if (isLoggedIn.value) {
    fetchUserPoints()
  }
}

// 定时刷新积分（每30秒）
let refreshTimer = null

onMounted(() => {
  // 恢复保存的位置，如果没有则使用默认位置（右上角）
  const savedPosition = localStorage.getItem('floating_menu_position')
  if (savedPosition) {
    try {
      menuPosition.value = JSON.parse(savedPosition)
    } catch {
      menuPosition.value = { x: window.innerWidth - 220, y: 60 }
    }
  } else {
    menuPosition.value = { x: window.innerWidth - 220, y: 60 }
  }

  // 初始获取积分
  fetchUserPoints()

  // 监听页面可见性变化
  document.addEventListener('visibilitychange', handleVisibilityChange)

  // 监听路由变化
  router.afterEach(handleRouteChange)

  // 定时刷新积分
  refreshTimer = setInterval(() => {
    if (!document.hidden && isLoggedIn.value) {
      fetchUserPoints()
    }
  }, 30000) // 30秒刷新一次
})

onUnmounted(() => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', stopDrag)
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})

// 暴露刷新方法供外部调用
defineExpose({
  fetchUserPoints
})
</script>

<style scoped>
.global-floating-menu {
  position: fixed;
  z-index: 9999;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(12px);
  border: 1px solid #e3e9f5;
  border-radius: 16px;
  padding: 8px 4px 8px 8px;
  box-shadow: 0 8px 24px rgba(0, 82, 217, 0.15);
  cursor: move;
  touch-action: none;
  user-select: none;
  transition: box-shadow 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  will-change: transform;
}

/* 拖动时禁用过渡动画 */
.global-floating-menu.is-dragging {
  transition: none;
}

.global-floating-menu:hover {
  box-shadow: 0 12px 32px rgba(0, 82, 217, 0.22);
}

.drag-handle {
  flex-shrink: 0;
  width: 36px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #a0b0cc;
  font-size: 14px;
  letter-spacing: -2px;
  cursor: grab;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.drag-handle:hover {
  color: #7a8fb3;
  background: rgba(0, 82, 217, 0.08);
}

.drag-handle:active {
  cursor: grabbing;
  color: #0052d9;
  background: rgba(0, 82, 217, 0.12);
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
  transition: transform 0.2s ease;
}

.avatar:hover {
  transform: scale(1.1);
}

.avatar span {
  font-size: 16px;
}
</style>
