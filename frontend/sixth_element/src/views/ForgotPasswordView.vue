<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 步骤: 'email' | 'verify' | 'success'
const step = ref('email')

// 表单数据
const email = ref('')
const code = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)

// 验证码相关
const countdown = ref(0)
const canResend = computed(() => countdown.value === 0)
const debugCode = ref('')  // 用于显示调试验证码

// 状态
const loading = ref(false)
const error = ref('')
const emailError = ref('')
const codeError = ref('')
const passwordError = ref('')
const confirmPasswordError = ref('')

// 密码强度
const passwordStrength = computed(() => {
  if (!newPassword.value) return null
  let strength = 0
  if (newPassword.value.length >= 8) strength++
  if (/[a-z]/.test(newPassword.value)) strength++
  if (/[A-Z]/.test(newPassword.value)) strength++
  if (/[0-9]/.test(newPassword.value)) strength++
  if (/[^a-zA-Z0-9]/.test(newPassword.value)) strength++
  
  if (strength <= 1) return { level: 'weak', text: '弱', color: '#d32f2f' }
  if (strength <= 3) return { level: 'medium', text: '中', color: '#f57c00' }
  return { level: 'strong', text: '强', color: '#388e3c' }
})

// 清空错误
function clearErrors() {
  emailError.value = ''
  codeError.value = ''
  passwordError.value = ''
  confirmPasswordError.value = ''
  error.value = ''
}

// 验证邮箱
function validateEmail(value) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(value)
}

// 开始倒计时
function startCountdown() {
  countdown.value = 60
  const timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(timer)
    }
  }, 1000)
}

// 发送验证码
async function sendCode() {
  clearErrors()
  
  if (!email.value.trim()) {
    emailError.value = '请输入邮箱地址'
    return
  }
  
  if (!validateEmail(email.value)) {
    emailError.value = '请输入正确的邮箱格式'
    return
  }
  
  loading.value = true
  
  try {
    const res = await fetch('/api/v1/auth/send-reset-code', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email.value.trim(),
      }),
    })
    
    const data = await res.json()
    
    if (!res.ok) {
      error.value = data.error || '发送验证码失败'
      return
    }
    
    // 调试模式下显示验证码
    if (data.debug_code) {
      debugCode.value = data.debug_code
    }
    
    step.value = 'verify'
    startCountdown()
  } catch (err) {
    console.error('Send code error:', err)
    error.value = '网络连接失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 重新发送验证码
async function resendCode() {
  if (!canResend.value) return
  await sendCode()
}

// 验证并重置密码
async function resetPassword() {
  clearErrors()
  let valid = true
  
  if (!code.value.trim()) {
    codeError.value = '请输入验证码'
    valid = false
  } else if (code.value.trim().length !== 6) {
    codeError.value = '验证码应为6位数字'
    valid = false
  }
  
  if (!newPassword.value) {
    passwordError.value = '请输入新密码'
    valid = false
  } else if (newPassword.value.length < 6) {
    passwordError.value = '密码长度至少 6 位'
    valid = false
  }
  
  if (newPassword.value !== confirmPassword.value) {
    confirmPasswordError.value = '两次输入密码不一致'
    valid = false
  }
  
  if (!valid) return
  
  loading.value = true
  
  try {
    const res = await fetch('/api/v1/auth/reset-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email.value.trim(),
        code: code.value.trim(),
        new_password: newPassword.value,
      }),
    })
    
    const data = await res.json()
    
    if (!res.ok) {
      error.value = data.error || '重置密码失败'
      return
    }
    
    step.value = 'success'
    
    // 3秒后跳转到登录页
    setTimeout(() => {
      router.push('/login')
    }, 3000)
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

// 返回上一步
function backToEmail() {
  step.value = 'email'
  clearErrors()
  code.value = ''
  newPassword.value = ''
  confirmPassword.value = ''
}

// 切换密码显示
function togglePasswordVisibility() {
  showPassword.value = !showPassword.value
}
</script>

<template>
  <div class="forgot-password-container">
    <div class="forgot-password-content">
      <!-- Logo 区 -->
      <div class="logo-section">
        <div class="logo">🔐</div>
        <h1 class="app-title">重置密码</h1>
      </div>
      
      <!-- 步骤指示器 -->
      <div class="steps-indicator">
        <div class="step" :class="{ active: step === 'email', completed: step !== 'email' }">
          <div class="step-number">1</div>
          <div class="step-label">验证邮箱</div>
        </div>
        <div class="step-line" :class="{ active: step !== 'email' }"></div>
        <div class="step" :class="{ active: step === 'verify', completed: step === 'success' }">
          <div class="step-number">2</div>
          <div class="step-label">重置密码</div>
        </div>
        <div class="step-line" :class="{ active: step === 'success' }"></div>
        <div class="step" :class="{ active: step === 'success' }">
          <div class="step-number">3</div>
          <div class="step-label">完成</div>
        </div>
      </div>
      
      <!-- 错误提示 -->
      <div v-if="error" class="error-toast">
        <span class="error-icon">⚠️</span>
        <span class="error-message">{{ error }}</span>
      </div>
      
      <!-- 步骤1: 输入邮箱 -->
      <div v-if="step === 'email'" class="step-content">
        <p class="step-description">请输入您注册时使用的邮箱地址，我们将发送验证码到您的邮箱</p>
        
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
              @keydown.enter="sendCode"
            />
          </div>
          <p v-if="emailError" class="error-text">{{ emailError }}</p>
        </div>
        
        <button
          type="button"
          class="submit-btn"
          :class="{ loading: loading }"
          :disabled="loading"
          @click="sendCode"
        >
          <span v-if="!loading">发送验证码</span>
          <span v-else class="loading-spinner">⏳</span>
        </button>
        
        <button type="button" class="back-btn" @click="backToLogin">
          返回登录
        </button>
      </div>
      
      <!-- 步骤2: 验证码和新密码 -->
      <div v-if="step === 'verify'" class="step-content">
        <p class="step-description">
          验证码已发送到 <strong>{{ email }}</strong>
        </p>
        
        <!-- 调试信息 -->
        <div v-if="debugCode" class="debug-info">
          🔧 开发模式验证码：<strong>{{ debugCode }}</strong>
        </div>
        
        <div class="form-group">
          <label for="code" class="form-label">验证码</label>
          <div class="input-wrapper">
            <span class="input-icon">🔢</span>
            <input
              id="code"
              v-model="code"
              type="text"
              maxlength="6"
              class="form-input"
              :class="{ 'has-error': codeError }"
              placeholder="请输入6位验证码"
            />
            <button
              type="button"
              class="resend-btn"
              :disabled="!canResend"
              @click="resendCode"
            >
              {{ canResend ? '重新发送' : `${countdown}秒后重发` }}
            </button>
          </div>
          <p v-if="codeError" class="error-text">{{ codeError }}</p>
        </div>
        
        <div class="form-group">
          <label for="new-password" class="form-label">新密码</label>
          <div class="input-wrapper">
            <span class="input-icon">🔒</span>
            <input
              id="new-password"
              v-model="newPassword"
              :type="showPassword ? 'text' : 'password'"
              class="form-input"
              :class="{ 'has-error': passwordError }"
              placeholder="请输入新密码（至少 6 位）"
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
          <div v-if="passwordStrength" class="password-strength">
            <div class="strength-bar">
              <div
                class="strength-fill"
                :style="{
                  width: passwordStrength.level === 'weak' ? '33%' : passwordStrength.level === 'medium' ? '66%' : '100%',
                  backgroundColor: passwordStrength.color
                }"
              ></div>
            </div>
            <span class="strength-text" :style="{ color: passwordStrength.color }">
              密码强度：{{ passwordStrength.text }}
            </span>
          </div>
        </div>
        
        <div class="form-group">
          <label for="confirm-password" class="form-label">确认密码</label>
          <div class="input-wrapper">
            <span class="input-icon">🔒</span>
            <input
              id="confirm-password"
              v-model="confirmPassword"
              :type="showPassword ? 'text' : 'password'"
              class="form-input"
              :class="{ 'has-error': confirmPasswordError }"
              placeholder="请再次输入新密码"
              @keydown.enter="resetPassword"
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
          <p v-if="confirmPasswordError" class="error-text">{{ confirmPasswordError }}</p>
        </div>
        
        <button
          type="button"
          class="submit-btn"
          :class="{ loading: loading }"
          :disabled="loading"
          @click="resetPassword"
        >
          <span v-if="!loading">重置密码</span>
          <span v-else class="loading-spinner">⏳</span>
        </button>
        
        <button type="button" class="back-btn" @click="backToEmail">
          返回上一步
        </button>
      </div>
      
      <!-- 步骤3: 成功 -->
      <div v-if="step === 'success'" class="step-content success-content">
        <div class="success-icon">✅</div>
        <h2 class="success-title">密码重置成功！</h2>
        <p class="success-message">您的密码已成功重置，即将跳转到登录页面...</p>
        
        <button type="button" class="submit-btn" @click="backToLogin">
          立即登录
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
* {
  box-sizing: border-box;
}

.forgot-password-container {
  min-height: 100vh;
  background: #f6f8fb;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.forgot-password-content {
  max-width: 520px;
  width: 100%;
  background: #ffffff;
  border-radius: 14px;
  padding: 32px 28px;
  border: 1px solid #e3e9f5;
  box-shadow: 0 10px 26px rgba(0, 82, 217, 0.06);
}

/* Logo 区 */
.logo-section {
  text-align: center;
  margin-bottom: 28px;
}

.logo {
  font-size: 48px;
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

/* 步骤指示器 */
.steps-indicator {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
  padding: 0 20px;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
}

.step-number {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #e3e9f5;
  color: #8ea2bf;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s ease;
}

.step.active .step-number {
  background: #0052d9;
  color: white;
  box-shadow: 0 4px 12px rgba(0, 82, 217, 0.25);
}

.step.completed .step-number {
  background: #388e3c;
  color: white;
}

.step-label {
  font-size: 12px;
  color: #8ea2bf;
  font-weight: 500;
  white-space: nowrap;
}

.step.active .step-label {
  color: #0052d9;
  font-weight: 600;
}

.step.completed .step-label {
  color: #388e3c;
}

.step-line {
  flex: 1;
  height: 2px;
  background: #e3e9f5;
  margin: 0 8px;
  transition: all 0.3s ease;
}

.step-line.active {
  background: #0052d9;
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

/* 调试信息 */
.debug-info {
  background: #fff3e0;
  border-left: 4px solid #f57c00;
  padding: 12px 14px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 13px;
  color: #e65100;
}

.debug-info strong {
  font-weight: 700;
  font-size: 16px;
  letter-spacing: 2px;
}

/* 步骤内容 */
.step-content {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.step-description {
  text-align: center;
  font-size: 14px;
  color: #5c7599;
  line-height: 1.6;
  margin: 0 0 8px 0;
}

.step-description strong {
  color: #0052d9;
  font-weight: 600;
}

/* 表单 */
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
  z-index: 1;
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

.resend-btn {
  position: absolute;
  right: 8px;
  background: #f2f6ff;
  border: 1px solid #d7e3ff;
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  color: #0052d9;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.resend-btn:hover:not(:disabled) {
  background: #e3f2fd;
  border-color: #0052d9;
}

.resend-btn:disabled {
  color: #8ea2bf;
  cursor: not-allowed;
  opacity: 0.6;
}

.error-text {
  font-size: 12px;
  color: #d32f2f;
  margin: 0;
  font-weight: 500;
}

/* 密码强度 */
.password-strength {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 4px;
}

.strength-bar {
  flex: 1;
  height: 4px;
  background: #e3e9f5;
  border-radius: 2px;
  overflow: hidden;
}

.strength-fill {
  height: 100%;
  transition: all 0.3s ease;
  border-radius: 2px;
}

.strength-text {
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

/* 按钮 */
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
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 8px 20px rgba(0, 82, 217, 0.18);
  margin-top: 8px;
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

.back-btn {
  background: none;
  border: none;
  color: #0052d9;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  padding: 8px;
  transition: opacity 0.2s;
}

.back-btn:hover {
  opacity: 0.7;
  text-decoration: underline;
}

/* 成功页面 */
.success-content {
  text-align: center;
  padding: 20px 0;
}

.success-icon {
  font-size: 72px;
  margin-bottom: 20px;
  animation: successPop 0.6s ease-out;
}

@keyframes successPop {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.success-title {
  font-size: 24px;
  font-weight: 700;
  color: #388e3c;
  margin: 0 0 12px 0;
}

.success-message {
  font-size: 14px;
  color: #5c7599;
  margin: 0 0 24px 0;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .forgot-password-content {
    padding: 24px 18px;
  }
  
  .steps-indicator {
    padding: 0 10px;
  }
  
  .step-label {
    font-size: 11px;
  }
  
  .step-number {
    width: 32px;
    height: 32px;
    font-size: 13px;
  }
  
  .app-title {
    font-size: 20px;
  }
  
  .form-input {
    padding: 10px 36px 10px 36px;
    font-size: 16px; /* 防止 iOS 自动放大 */
  }
  
  .resend-btn {
    font-size: 11px;
    padding: 5px 10px;
  }
}
</style>
