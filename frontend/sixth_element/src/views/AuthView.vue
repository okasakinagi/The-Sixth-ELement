<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 动态文案库
const quotes = [
  "你的问卷，会被用心填写。",
  "在这里，让每一个观点都有回响。",
  "知识的传递，从一次真诚的填答开始。",
  "连接校园需求，遇见更好的洞察。",
  "每一个声音，都值得被听见。",
  "用数据驱动洞察，用洞察指引决策。",
  "问卷不只是表单，更是对话。",
  "让你的想法闪闪发光。"
]

// 表单数据
const email = ref('')
const password = ref('')
const showPassword = ref(false)

// 状态
const loading = ref(false)
const error = ref('')
const currentQuote = ref('')
const emailError = ref('')
const passwordError = ref('')

// 选中的认证模式
const authMode = ref('login') // 'login' 或 'register'

// 注册表单额外字段
const nickname = ref('')
const confirmPassword = ref('')
const nicknameError = ref('')
const confirmPasswordError = ref('')

// 初始化随机文案
onMounted(() => {
  const randomIndex = Math.floor(Math.random() * quotes.length)
  currentQuote.value = quotes[randomIndex]
})

// 切换显示密码
function togglePasswordVisibility() {
  showPassword.value = !showPassword.value
}

// 清空所有错误信息
function clearErrors() {
  emailError.value = ''
  passwordError.value = ''
  nicknameError.value = ''
  confirmPasswordError.value = ''
  error.value = ''
}

// 验证邮箱格式
function validateEmail(value) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(value)
}

// 验证登录表单
function validateLoginForm() {
  clearErrors()
  let valid = true

  if (!email.value.trim()) {
    emailError.value = '请输入邮箱地址'
    valid = false
  } else if (!validateEmail(email.value)) {
    emailError.value = '请输入正确的邮箱格式'
    valid = false
  }

  if (!password.value) {
    passwordError.value = '请输入密码'
    valid = false
  } else if (password.value.length < 6) {
    passwordError.value = '密码长度至少 6 位'
    valid = false
  }

  return valid
}

// 验证注册表单
function validateRegisterForm() {
  clearErrors()
  let valid = true

  if (!email.value.trim()) {
    emailError.value = '请输入邮箱地址'
    valid = false
  } else if (!validateEmail(email.value)) {
    emailError.value = '请输入正确的邮箱格式'
    valid = false
  }

  if (!nickname.value.trim()) {
    nicknameError.value = '请输入昵称'
    valid = false
  } else if (nickname.value.length < 2 || nickname.value.length > 20) {
    nicknameError.value = '昵称长度应为 2-20 个字符'
    valid = false
  }

  if (!password.value) {
    passwordError.value = '请输入密码'
    valid = false
  } else if (password.value.length < 6) {
    passwordError.value = '密码长度至少 6 位'
    valid = false
  }

  if (password.value !== confirmPassword.value) {
    confirmPasswordError.value = '两次输入密码不一致'
    valid = false
  }

  return valid
}

// 处理登录
async function handleLogin() {
  if (!validateLoginForm()) return

  loading.value = true
  error.value = ''

  try {
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email.value.trim(),
        password: password.value,
      }),
    })

    const data = await res.json()

    if (!res.ok) {
      error.value = data.error || '登录失败，请检查用户名和密码'
      return
    }

    // 保存 token
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('user_id', data.user?.id || '')
    localStorage.setItem('user_nickname', data.user?.nickname || '')

    // 延迟导航，让用户感受到反馈
    setTimeout(() => {
      router.push('/surveys?justLoggedIn=true')
    }, 500)
  } catch (err) {
    console.error('Login error:', err)
    error.value = '网络连接失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 处理注册
async function handleRegister() {
  if (!validateRegisterForm()) return

  loading.value = true
  error.value = ''

  try {
    const res = await fetch('/api/v1/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email.value.trim(),
        nickname: nickname.value.trim(),
        password: password.value,
      }),
    })

    const data = await res.json()

    if (!res.ok) {
      error.value = data.error || '注册失败，请稍后重试'
      return
    }

    // 保存 token
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('user_id', data.user?.id || '')
    localStorage.setItem('user_nickname', data.user?.nickname || '')

    // 延迟导航
    setTimeout(() => {
      router.push('/surveys?justLoggedIn=true')
    }, 500)
  } catch (err) {
    console.error('Register error:', err)
    error.value = '网络连接失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 处理回车键登录
function handleKeydown(e) {
  if (e.key === 'Enter' && !loading.value) {
    if (authMode.value === 'login') {
      handleLogin()
    } else {
      handleRegister()
    }
  }
}

// 切换模式
function switchMode(mode) {
  authMode.value = mode
  clearErrors()
  error.value = ''
}

// 前往忘记密码页面
function goToForgotPassword() {
  router.push('/forgot-password')
}
</script>

<template>
  <div class="auth-container">
    <!-- 主要内容区 -->
    <div class="auth-content">
      <!-- Logo 区 -->
      <div class="logo-section">
        <div class="logo">📋</div>
        <h1 class="app-title">The Sixth Element</h1>
      </div>

      <!-- 文案区 -->
      <div class="copywriting">
        <h2 class="main-title">
          {{ authMode === 'login' ? '登录您的账号' : '创建新账号' }}
        </h2>
        <p class="dynamic-quote">{{ currentQuote }}</p>
      </div>

      <!-- 模式切换标签 -->
      <div class="mode-tabs">
        <button
          class="mode-tab"
          :class="{ active: authMode === 'login' }"
          @click="switchMode('login')"
        >
          登录
        </button>
        <button
          class="mode-tab"
          :class="{ active: authMode === 'register' }"
          @click="switchMode('register')"
        >
          注册
        </button>
      </div>

      <!-- 错误提示 -->
      <div v-if="error" class="error-toast">
        <span class="error-icon">⚠️</span>
        <span class="error-message">{{ error }}</span>
      </div>

      <!-- 表单区 -->
      <form @keydown="handleKeydown" class="auth-form">
        <!-- 邮箱字段 -->
        <div class="form-group">
          <label for="email" class="form-label">邮箱地址</label>
          <div class="input-wrapper">
            <span class="input-icon">✉️</span>
            <input
              id="email"
              v-model="email"
              type="email"
              class="form-input"
              :class="{ 'has-error': emailError }"
              placeholder="请输入邮箱地址"
              @blur="validateEmail(email)"
            />
          </div>
          <p v-if="emailError" class="error-text">{{ emailError }}</p>
        </div>

        <!-- 昵称字段（注册模式） -->
        <div v-if="authMode === 'register'" class="form-group">
          <label for="nickname" class="form-label">昵称</label>
          <div class="input-wrapper">
            <span class="input-icon">👤</span>
            <input
              id="nickname"
              v-model="nickname"
              type="text"
              class="form-input"
              :class="{ 'has-error': nicknameError }"
              placeholder="请输入昵称（2-20 个字符）"
            />
          </div>
          <p v-if="nicknameError" class="error-text">{{ nicknameError }}</p>
        </div>

        <!-- 密码字段 -->
        <div class="form-group">
          <label for="password" class="form-label">密码</label>
          <div class="input-wrapper">
            <span class="input-icon">🔒</span>
            <input
              id="password"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              class="form-input"
              :class="{ 'has-error': passwordError }"
              placeholder="请输入密码（至少 6 位）"
            />
            <button
              type="button"
              class="password-toggle"
              :class="{ 'password-hidden': !showPassword }"
              @click="togglePasswordVisibility"
              :aria-label="showPassword ? '隐藏密码' : '显示密码'"
            >
              👁️
            </button>
          </div>
          <p v-if="passwordError" class="error-text">{{ passwordError }}</p>
        </div>

        <!-- 确认密码字段（注册模式） -->
        <div v-if="authMode === 'register'" class="form-group">
          <label for="confirm-password" class="form-label">确认密码</label>
          <div class="input-wrapper">
            <span class="input-icon">🔒</span>
            <input
              id="confirm-password"
              v-model="confirmPassword"
              :type="showPassword ? 'text' : 'password'"
              class="form-input"
              :class="{ 'has-error': confirmPasswordError }"
              placeholder="请再次输入密码"
            />
            <button
              type="button"
              class="password-toggle"
              :class="{ 'password-hidden': !showPassword }"
              @click="togglePasswordVisibility"
              :aria-label="showPassword ? '隐藏密码' : '显示密码'"
            >
              👁️
            </button>
          </div>
          <p v-if="confirmPasswordError" class="error-text">
            {{ confirmPasswordError }}
          </p>
        </div>

        <!-- 登录特有的辅助链接 -->
        <div v-if="authMode === 'login'" class="form-helpers">
          <button type="button" class="forgot-password-btn" @click="goToForgotPassword">
            忘记密码？
          </button>
        </div>

        <!-- 提交按钮 -->
        <button
          type="button"
          :class="['submit-btn', { loading: loading }]"
          :disabled="loading"
          @click="authMode === 'login' ? handleLogin() : handleRegister()"
        >
          <span v-if="!loading" class="btn-text">
            {{ authMode === 'login' ? '登录' : '注册' }}
          </span>
          <span v-else class="loading-spinner">⏳</span>
        </button>
      </form>

      <!-- 底部链接 -->
      <div class="footer-links">
        <template v-if="authMode === 'login'">
          <p>
            没有账号？
            <button
              type="button"
              class="link-btn"
              @click="switchMode('register')"
            >
              立即注册
            </button>
          </p>
        </template>
        <template v-else>
          <p>
            已有账号？
            <button
              type="button"
              class="link-btn"
              @click="switchMode('login')"
            >
              返回登录
            </button>
          </p>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
* {
  box-sizing: border-box;
}

.auth-container {
  min-height: 100vh;
  background: #f6f8fb;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

/* 主要内容 */
.auth-content {
  max-width: 460px;
  width: 100%;
  background: #ffffff;
  border-radius: 14px;
  padding: 28px 26px;
  border: 1px solid #e3e9f5;
  box-shadow: 0 10px 26px rgba(0, 82, 217, 0.06);
}

/* Logo 区 */
.logo-section {
  text-align: center;
  margin-bottom: 32px;
}

.logo {
  font-size: 42px;
  margin-bottom: 12px;
  display: inline-block;
}

.app-title {
  font-size: 22px;
  font-weight: 700;
  color: #0b2b66;
  margin: 0;
  letter-spacing: -0.5px;
}

/* 文案区 */
.copywriting {
  text-align: center;
  margin-bottom: 28px;
}

.main-title {
  font-size: 20px;
  font-weight: 600;
  color: #0b2b66;
  margin: 0 0 12px 0;
}

.dynamic-quote {
  font-size: 13px;
  color: #5c7599;
  margin: 0;
  line-height: 1.5;
  font-weight: 400;
  letter-spacing: 0.3px;
}

/* 模式切换标签 */
.mode-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  background: #f2f6ff;
  padding: 6px;
  border-radius: 10px;
  border: 1px solid #d7e3ff;
}

.mode-tab {
  flex: 1;
  padding: 10px;
  border: none;
  background: transparent;
  color: #5c7599;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.mode-tab.active {
  background: #ffffff;
  color: #0052d9;
  box-shadow: 0 4px 12px rgba(0, 82, 217, 0.12);
}

/* 错误提示 */
.error-toast {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  background: #fff6f6;
  border-left: 4px solid #d32f2f;
  border-radius: 8px;
  margin-bottom: 20px;
}

.error-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.error-message {
  font-size: 13px;
  color: #d32f2f;
  font-weight: 500;
}

/* 表单 */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 13px;
  font-weight: 600;
  color: #0b2b66;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 12px;
  font-size: 16px;
  pointer-events: none;
}

.form-input {
  width: 100%;
  padding: 11px 40px 11px 38px;
  border: 1px solid #d7e3ff;
  border-radius: 10px;
  font-size: 14px;
  font-family: inherit;
  color: #0b2b66;
  background: #f2f6ff;
  transition: all 0.3s ease;
  outline: none;
}

.form-input:focus {
  background: #ffffff;
  border-color: #0052d9;
  box-shadow: 0 0 0 3px rgba(0, 82, 217, 0.12);
}

.form-input.has-error {
  border-color: #d32f2f;
  background: #fff5f5;
}

.form-input.has-error:focus {
  box-shadow: 0 0 0 3px rgba(211, 47, 47, 0.1);
}

.form-input::placeholder {
  color: #8ea2bf;
}

/* 隐藏浏览器自带的密码显示按钮 */
.form-input::-ms-reveal,
.form-input::-ms-clear {
  display: none;
}

.form-input::-webkit-credentials-auto-fill-button,
.form-input::-webkit-contacts-auto-fill-button {
  visibility: hidden;
  pointer-events: none;
  position: absolute;
}

.password-toggle {
  position: absolute;
  right: 12px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.2s;
}

.password-toggle.password-hidden::after {
  content: '';
  position: absolute;
  width: 20px;
  height: 1.5px;
  background: currentColor;
  transform: rotate(-45deg);
  top: 50%;
  left: 50%;
  margin-left: -10px;
  margin-top: -0.75px;
}

.password-toggle:hover {
  opacity: 0.7;
}

.password-toggle:active {
  transform: scale(0.95);
}

.error-text {
  font-size: 12px;
  color: #d32f2f;
  margin: 0;
  font-weight: 500;
}

/* 表单辅助链接 */
.form-helpers {
  display: flex;
  justify-content: flex-end;
  padding: 0 0 4px 0;
}

.forgot-password-btn {
  background: none;
  border: none;
  color: #0052d9;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
  transition: opacity 0.2s;
  padding: 0;
}

.forgot-password-btn:hover {
  opacity: 0.7;
  text-decoration: underline;
}

/* 提交按钮 */
.submit-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #0052d9, #2f7bff);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 8px 20px rgba(0, 82, 217, 0.18);
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(0, 82, 217, 0.22);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn.loading {
  opacity: 0.8;
}

.submit-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.btn-text {
  display: inline-block;
}

.loading-spinner {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* 底部链接 */
.footer-links {
  text-align: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e3e9f5;
}

.footer-links p {
  margin: 0;
  font-size: 14px;
  color: #7f8d9d;
}

.link-btn {
  background: none;
  border: none;
  color: #0052d9;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  transition: opacity 0.2s;
  padding: 0;
  font-size: 14px;
}

.link-btn:hover {
  opacity: 0.7;
  text-decoration: underline;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .auth-content {
    padding: 24px 18px;
    border-radius: 14px;
  }

  .app-title {
    font-size: 18px;
  }

  .main-title {
    font-size: 17px;
  }

  .dynamic-quote {
    font-size: 12px;
  }

  .form-input {
    padding: 10px 36px 10px 36px;
    font-size: 16px; /* 防止 iOS 自动放大 */
  }
}
</style>
