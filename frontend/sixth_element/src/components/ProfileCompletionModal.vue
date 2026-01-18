<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const props = defineProps({
  visible: Boolean,
})

const emit = defineEmits(['close'])

const userInfo = ref(null)
const loading = ref(false)

onMounted(async () => {
  if (props.visible) {
    await fetchUserInfo()
  }
})

async function fetchUserInfo() {
  const token = localStorage.getItem('access_token')
  if (!token) return

  try {
    const res = await fetch('/api/v1/users/me', {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (res.ok) {
      userInfo.value = await res.json()
    }
  } catch (err) {
    console.error('Failed to fetch user info:', err)
  }
}

function handleGoToProfile() {
  loading.value = true
  setTimeout(() => {
    emit('close')
    router.push('/profile')
  }, 300)
}

function handleDismiss() {
  emit('close')
}
</script>

<template>
  <div v-if="visible" class="modal-overlay" @click="handleDismiss">
    <div class="modal-card" @click.stop>
      <button class="close-btn" @click="handleDismiss" aria-label="关闭">
        ✕
      </button>

      <div class="modal-icon">🎉</div>

      <h2 class="modal-title">欢迎加入！</h2>

      <p class="modal-message">
        丰富个人信息后，会为您匹配更适合的问卷噢！
      </p>

      <div v-if="userInfo" class="user-preview">
        <p class="preview-text">当前账号：<strong>{{ userInfo.nickname }}</strong></p>
      </div>

      <div class="modal-actions">
        <button class="primary-btn" @click="handleGoToProfile">
          <span v-if="!loading">去完善 →</span>
          <span v-else>加载中...</span>
        </button>
        <button class="ghost-btn" @click="handleDismiss">再想想</button>
      </div>

      <p class="modal-hint">也可以随时在个人资料中修改信息</p>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-card {
  background: white;
  border-radius: 16px;
  padding: 40px 32px;
  max-width: 400px;
  width: 100%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  position: relative;
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #a8b4c1;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.close-btn:hover {
  color: #1a202c;
}

.modal-icon {
  text-align: center;
  font-size: 48px;
  margin-bottom: 16px;
  animation: bounce 0.6s ease-out;
}

@keyframes bounce {
  0% {
    transform: scale(0);
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
  }
}

.modal-title {
  font-size: 22px;
  font-weight: 700;
  color: #1a202c;
  margin: 0 0 12px 0;
  text-align: center;
}

.modal-message {
  font-size: 14px;
  color: #7f8d9d;
  text-align: center;
  margin: 0 0 20px 0;
  line-height: 1.6;
}

.user-preview {
  background: #f5f7fa;
  padding: 12px 16px;
  border-radius: 8px;
  margin: 16px 0;
  text-align: center;
}

.preview-text {
  font-size: 13px;
  color: #7f8d9d;
  margin: 0;
}

.preview-text strong {
  color: #1e4fb4;
  font-weight: 600;
}

.modal-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 24px 0 16px 0;
}

.primary-btn {
  padding: 11px 20px;
  background: linear-gradient(135deg, #1e4fb4 0%, #1a3f8a 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 4px 12px rgba(30, 79, 180, 0.2);
}

.primary-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(30, 79, 180, 0.3);
}

.primary-btn:active {
  transform: translateY(0);
}

.ghost-btn {
  padding: 11px 20px;
  background: transparent;
  color: #7f8d9d;
  border: 1px solid #e8eef5;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.ghost-btn:hover {
  background: #f5f7fa;
  color: #1a202c;
  border-color: #d0d8e0;
}

.modal-hint {
  font-size: 12px;
  color: #a8b4c1;
  text-align: center;
  margin: 0;
}

@media (max-width: 480px) {
  .modal-card {
    padding: 32px 24px;
  }

  .modal-title {
    font-size: 20px;
  }

  .modal-icon {
    font-size: 40px;
  }
}
</style>
