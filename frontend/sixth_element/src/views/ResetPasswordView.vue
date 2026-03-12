<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 重置流程状态: 'email', 'code', 'new-password', 'success'
const step = ref('email')

// 表单数据
const email = ref('')
const resetCode = ref('')
const newPassword = ref('')
const confirmPassword = ref('')

// UI状态
const loading = ref(false)
const error = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const message = ref('')

// 验证邮箱格式
function validateEmail(value) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(value)
}

// 清空错误
function clearErrors() {
  error.value = ''
  message.value = ''
}

// 第1步：请求重置码
async function requestResetCode() {
  clearErrors()
  
  if (!email.value.trim()) {
    error.value = '请输入邮箱地址'
    return
  }
  
  if (!validateEmail(email.value)) {
    error.value = '请输入正确的邮箱格式'
    return
  }

  loading.value = true
  try {
    const res = await fetch('/api/v1/auth/request-reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.value.trim() }),
    })

    const data = await res.json()

    if (!res.ok) {
      error.value = data.error || '请求失败，请检查邮箱是否正确'
      return
    }

    message.value = '验证码已发送到您的邮箱，请检查收件箱'
    step.value = 'code'
  } catch (err) {
    console.error('Request reset error:', err)
    error.value = '网络连接失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 第2步：验证重置码
async function verifyResetCode() {
  clearErrors()
  
  if (!resetCode.value.trim()) {
    error.value = '请输入验证码'
    return
  }

  loading.value = true
  try {
    const res = await fetch('/api/v1/auth/verify-reset-code', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email.value.trim(),
        reset_code: resetCode.value.trim(),
      }),
    })

    const data = await res.json()

    if (!res.ok) {
      error.value = data.error || '验证码错误或已过期'
      return
    }

    step.value = 'new-password'
    message.value = '验证成功，请设置新密码'
  } catch (err) {
    console.error('Verify code error:', err)
    error.value = '网络连接失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 第3步：设置新密码
async function resetPassword() {
  clearErrors()
  
  if (!newPassword.value) {
    error.value = '请输入新密码'
    return
  }
  
  if (newPassword.value.length < 6) {
    error.value = '密码长度至少 6 位'
    return
  }
  
  if (newPassword.value !== confirmPassword.value) {
    error.value = '两次输入密码不一致'
    return
  }

  loading.value = true
  try {
    const res = await fetch('/api/v1/auth/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email.value.trim(),
        reset_code: resetCode.value.trim(),
        new_password: newPassword.value,
      }),
    })

    const data = await res.json()

    if (!res.ok) {
      error.value = data.error || '重置失败，请稍后重试'
      return
    }

    step.value = 'success'
    message.value = '密码重置成功！'
    
    // 3秒后跳转到登录页
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  } catch (err) {
    console.error('Reset password error:', err)
    error.value = '网络连接失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 返回登录
function backToLogin() {
  router.push('/login')
}

// 重新开始
function restart() {
  step.value = 'email'
  email.value = ''
  resetCode.value = ''
  newPassword.value = ''
  confirmPassword.value = ''
  error.value = ''
  message.value = ''
}

// 处理回车键
function handleKeydown(e) {
  if (e.key === 'Enter' && !loading.value) {
    if (step.value === 'email') {
      requestResetCode()
    } else if (step.value === 'code') {
      verifyResetCode()
    } else if (step.value === 'new-password') {
      resetPassword()
    }
  }
}
</script>

<template>
  <div class="reset-container">
    <!-- 动画背景 -->
    <div class="animated-bg"></div>

    <!-- 主要内容区 -->
    <div class="reset-content">
      <!-- 返回按钮 -->
      <button class="back-btn" @click="backToLogin" title="返回登录">
        ← 返回
      </button>

      <!-- Logo 区 -->
      <div class="logo-section">
        <div class="logo">🔐</div>
        <h1 class="app-title">找回密码</h1>
      </div>

      <!-- 步骤指示器 -->
      <div class="steps-indicator">
        <div
          class="step"
          :class="{ active: step === 'email', completed: ['code', 'new-password', 'success'].includes(step) }"
        >
          <span class="step-number">1</span>
          <span class="step-label">邮箱验证</span>
        </div>
        <div class="step-connector"></div>
        <div
          class="step"
          :class="{ active: step === 'code', completed: ['new-password', 'success'].includes(step) }"
        >
          <span class="step-number">2</span>
          <span class="step-label">验证码</span>
        </div>
        <div class="step-connector"></div>
        <div
          class="step"
          :class="{ active: step === 'new-password', completed: step === 'success' }"
        >
          <span class="step-number">3</span>
          <span class="step-label">设置密码</span>
        </div>
      </div>

      <!-- 错误提示 -->
      <div v-if="error" class="error-toast">
        <span class="error-icon">⚠️</span>
        <span class="error-message">{{ error }}</span>
      </div>

      <!-- 成功提示 -->
      <div v-if="message" class="success-toast" :class="{ show: step === 'success' }">
        <span class="success-icon">✅</span>
        <span class="success-message">{{ message }}</span>
      </div>

      <!-- 表单区 -->
      <form @keydown="handleKeydown" class="reset-form">
        <!-- 第1步：邮箱输入 -->
        <div v-if="step === 'email'" class="form-section">
          <div class="form-group">
            <label for="email" class="form-label">邮箱地址</label>
            <div class="input-wrapper">
              <span class="input-icon">✉️</span>
              <input
                id="email"
                v-model="email"
                type="email"
                class="form-input"
                placeholder="请输入您的邮箱地址"
                :disabled="loading"
              />
            </div>
          </div>
          <button
            type="button"
            class="submit-btn"
            :disabled="loading"
            @click="requestResetCode"
          >
            {{ loading ? '发送中...' : '发送验证码' }}
          </button>
        </div>

        <!-- 第2步：验证码输入 -->
        <div v-if="step === 'code'" class="form-section">
          <p class="hint-text">验证码已发送到 <strong>{{ email }}</strong></p>
          <div class="form-group">
            <label for="reset-code" class="form-label">验证码</label>
            <div class="input-wrapper">
              <span class="input-icon">📬</span>
              <input
                id="reset-code"
                v-model="resetCode"
                type="text"
                class="form-input code-input"
                placeholder="请输入 6 位验证码"
                maxlength="6"
                :disabled="loading"
              />
            </div>
          </div>
          <button
            type="button"
            class="submit-btn"
            :disabled="loading"
            @click="verifyResetCode"
          >
            {{ loading ? '验证中...' : '验证码验证' }}
          </button>
        </div>

        <!-- 第3步：新密码设置 -->
        <div v-if="step === 'new-password'" class="form-section">
          <div class="form-group">
            <label for="new-password" class="form-label">新密码</label>
            <div class="input-wrapper">
              <span class="input-icon">🔒</span>
              <input
                id="new-password"
                v-model="newPassword"
                :type="showPassword ? 'text' : 'password'"
                class="form-input"
                placeholder="请输入新密码（至少 6 位）"
                :disabled="loading"
              />
              <button
                type="button"
                class="password-toggle"
                @click="showPassword = !showPassword"
                :aria-label="showPassword ? '隐藏密码' : '显示密码'"
              >
                {{ showPassword ? '👁️‍🗨️' : '🙈' }}
              </button>
            </div>
          </div>

          <div class="form-group">
            <label for="confirm-password" class="form-label">确认密码</label>
            <div class="input-wrapper">
              <span class="input-icon">🔒</span>
              <input
                id="confirm-password"
                v-model="confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                class="form-input"
                placeholder="请再次输入新密码"
                :disabled="loading"
              />
              <button
                type="button"
                class="password-toggle"
                @click="showConfirmPassword = !showConfirmPassword"
                :aria-label="showConfirmPassword ? '隐藏密码' : '显示密码'"
              >
                {{ showConfirmPassword ? '👁️‍🗨️' : '🙈' }}
              </button>
            </div>
          </div>

          <button
            type="button"
            class="submit-btn"
            :disabled="loading"
            @click="resetPassword"
          >
            {{ loading ? '重置中...' : '重置密码' }}
          </button>
        </div>

        <!-- 成功状态 -->
        <div v-if="step === 'success'" class="form-section success-section">
          <div class="success-content">
            <span class="large-icon">🎉</span>
            <h2 class="success-title">密码重置成功！</h2>
            <p class="success-desc">您的密码已成功重置，请使用新密码登录</p>
            <button
              type="button"
              class="submit-btn"
              @click="backToLogin"
            >
              返回登录
            </button>
          </div>
        </div>
      </form>

      <!-- 辅助链接 -->
      <div v-if="step !== 'success'" class="footer-links">
        <button type="button" class="link-btn" @click="backToLogin">
          返回登录
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
* {
  box-sizing: border-box;
}

.reset-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f0f5ff 0%, #ffffff 50%, #f8f9ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  position: relative;
  overflow: hidden;
}

/* 动画背景 */
.animated-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 30%, rgba(30, 79, 180, 0.05) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(13, 71, 161, 0.03) 0%, transparent 50%);
  animation: float 20s ease-in-out infinite;
  pointer-events: none;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) translateX(0px);
  }
  50% {
    transform: translateY(10px) translateX(5px);
  }
}

/* 主要内容 */
.reset-content {
  position: relative;
  z-index: 1;
  max-width: 480px;
  width: 100%;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 40px 30px;
  box-shadow: 0 20px 60px rgba(30, 79, 180, 0.08);
  backdrop-filter: blur(10px);
}

/* 返回按钮 */
.back-btn {
  position: absolute;
  top: 20px;
  left: 20px;
  background: none;
  border: none;
  color: #7f8d9d;
  font-size: 14px;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 6px;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #f5f7fa;
  color: #1e4fb4;
}

/* Logo 区 */
.logo-section {
  text-align: center;
  margin-bottom: 28px;
  margin-top: 8px;
}

.logo {
  font-size: 48px;
  margin-bottom: 12px;
  display: inline-block;
  animation: bounce 2s ease-in-out infinite;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-8px);
  }
}

.app-title {
  font-size: 24px;
  font-weight: 700;
  color: #1a202c;
  margin: 0;
  letter-spacing: -0.5px;
}

/* 步骤指示器 */
.steps-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 28px;
  flex-wrap: wrap;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.step-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #e8eef5;
  color: #7f8d9d;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s;
}

.step.active .step-number {
  background: #1e4fb4;
  color: white;
}

.step.completed .step-number {
  background: #4caf50;
  color: white;
}

.step-label {
  font-size: 12px;
  color: #7f8d9d;
  text-align: center;
  min-width: 50px;
}

.step.active .step-label {
  color: #1e4fb4;
  font-weight: 600;
}

.step.completed .step-label {
  color: #4caf50;
}

.step-connector {
  width: 24px;
  height: 2px;
  background: #e8eef5;
  margin: 0 4px;
}

/* 错误和成功提示 */
.error-toast {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  background: #fff5f5;
  border-left: 4px solid #d32f2f;
  border-radius: 6px;
  margin-bottom: 20px;
  animation: slideInDown 0.3s ease-out;
}

.success-toast {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  background: #f1f8e9;
  border-left: 4px solid #4caf50;
  border-radius: 6px;
  margin-bottom: 20px;
  animation: slideInDown 0.3s ease-out;
}

@keyframes slideInDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.error-icon,
.success-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.error-message,
.success-message {
  font-size: 13px;
  font-weight: 500;
}

.error-message {
  color: #d32f2f;
}

.success-message {
  color: #558b2f;
}

/* 表单 */
.reset-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 18px;
  animation: fadeIn 0.3s ease-out;
}

.success-section {
  gap: 0;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.success-content {
  text-align: center;
  padding: 20px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.large-icon {
  font-size: 64px;
  display: block;
  animation: bounce 2s ease-in-out infinite;
}

.success-title {
  font-size: 20px;
  font-weight: 600;
  color: #1a202c;
  margin: 0;
}

.success-desc {
  font-size: 14px;
  color: #7f8d9d;
  margin: 0;
  line-height: 1.5;
}

.hint-text {
  font-size: 13px;
  color: #7f8d9d;
  margin: 0;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  text-align: center;
}

.hint-text strong {
  color: #1e4fb4;
  font-weight: 600;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 13px;
  font-weight: 600;
  color: #1a202c;
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
  border: 2px solid #e8eef5;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  color: #1a202c;
  background: #fafbfc;
  transition: all 0.3s ease;
  outline: none;
}

.form-input:focus {
  background: white;
  border-color: #1e4fb4;
  box-shadow: 0 0 0 3px rgba(30, 79, 180, 0.1);
}

.form-input:disabled {
  background: #f5f7fa;
  cursor: not-allowed;
  opacity: 0.6;
}

.form-input::placeholder {
  color: #a8b4c1;
}

.code-input {
  letter-spacing: 8px;
  font-family: 'Courier New', monospace;
  font-size: 16px;
  text-align: center;
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

.password-toggle:hover {
  opacity: 0.7;
}

.password-toggle:active {
  transform: scale(0.95);
}

/* 提交按钮 */
.submit-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #1e4fb4 0%, #1a3f8a 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 4px 12px rgba(30, 79, 180, 0.2);
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(30, 79, 180, 0.3);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

/* 底部链接 */
.footer-links {
  text-align: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e8eef5;
}

.link-btn {
  background: none;
  border: none;
  color: #1e4fb4;
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

/* 响应式 */
@media (max-width: 480px) {
  .reset-content {
    padding: 30px 20px;
    border-radius: 16px;
  }

  .app-title {
    font-size: 20px;
  }

  .steps-indicator {
    font-size: 12px;
  }

  .step-number {
    width: 28px;
    height: 28px;
    font-size: 12px;
  }

  .step-label {
    font-size: 10px;
    min-width: 40px;
  }

  .form-input {
    padding: 10px 36px 10px 36px;
    font-size: 16px;
  }
}
</style>
