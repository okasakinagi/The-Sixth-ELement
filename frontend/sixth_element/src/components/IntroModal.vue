<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  visible: Boolean,
  showLoginGuide: { type: Boolean, default: false },
  startAtProfile: { type: Boolean, default: false },
  targetEl: { type: Object, default: null },
})

const emit = defineEmits(['close'])

const router = useRouter()

const activeTab = ref('overview')
const modalCardRef = ref(null)
const profileCompletion = ref(0)

// 仅当非首次设备访客且资料未100%完成时显示「完善个人信息」区块
const showProfileSection = computed(() => !props.showLoginGuide && profileCompletion.value < 100)
const profileSectionRef = ref(null)
const localVisible = ref(false)
const isClosing = ref(false)
const closingStyle = ref({})

watch(() => props.visible, (val) => {
  if (val) {
    // 每次打开时重新读取完成度（可能已由 EditProfileView/UserProfileView 更新）
    try {
      profileCompletion.value = parseInt(localStorage.getItem('sixth_element_profile_completion') || '0', 10)
    } catch (_) { profileCompletion.value = 0 }
    localVisible.value = true
    isClosing.value = false
    closingStyle.value = {}
    activeTab.value = 'overview'
    if (props.startAtProfile) {
      nextTick(() => setTimeout(scrollToProfile, 250))
    }
  } else if (localVisible.value && !isClosing.value) {
    localVisible.value = false
  }
})

function scrollToProfile() {
  if (profileSectionRef.value) {
    profileSectionRef.value.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }
}

function handleClose() {
  if (isClosing.value) return
  isClosing.value = true

  if (props.targetEl && modalCardRef.value) {
    try {
      const targetRect = props.targetEl.getBoundingClientRect()
      const cardRect = modalCardRef.value.getBoundingClientRect()
      const tx = (targetRect.left + targetRect.width / 2) - (cardRect.left + cardRect.width / 2)
      const ty = (targetRect.top + targetRect.height / 2) - (cardRect.top + cardRect.height / 2)
      closingStyle.value = {
        transform: `translate(${tx}px, ${ty}px) scale(0.05)`,
        opacity: '0',
        transition: 'transform 0.42s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease',
        pointerEvents: 'none',
      }
    } catch (_) {
      // fallback: 淡出缩小
      closingStyle.value = {
        transform: 'scale(0.9)',
        opacity: '0',
        transition: 'transform 0.3s ease, opacity 0.3s ease',
        pointerEvents: 'none',
      }
    }
  } else {
    // 无目标元素时也有缩小淡出效果
    closingStyle.value = {
      transform: 'scale(0.9)',
      opacity: '0',
      transition: 'transform 0.3s ease, opacity 0.3s ease',
      pointerEvents: 'none',
    }
  }

  setTimeout(() => {
    localVisible.value = false
    closingStyle.value = {}
    isClosing.value = false
    emit('close')
  }, 430)
}

function handleOverlayClick(e) {
  if (e.target === e.currentTarget) handleClose()
}

function goToProfile() {
  localVisible.value = false
  emit('close')
  router.push('/profile/edit')
}

function goToAuth() {
  localVisible.value = false
  emit('close')
  router.push('/login')
}
</script>

<template>
  <div
    v-if="localVisible"
    class="intro-overlay"
    :class="{ 'is-closing': isClosing }"
    @click="handleOverlayClick"
  >
    <div class="intro-card" ref="modalCardRef" :style="closingStyle">
      <!-- 关闭按钮 -->
      <button class="intro-close-btn" @click="handleClose" aria-label="关闭">✕</button>

      <!-- Tab 切换 -->
      <div class="intro-tabs">
        <button
          :class="['tab-btn', { active: activeTab === 'overview' }]"
          @click="activeTab = 'overview'"
        >整体介绍</button>
        <button
          :class="['tab-btn', { active: activeTab === 'modules' }]"
          @click="activeTab = 'modules'"
        >模块介绍</button>
      </div>

      <!-- 滚动内容区 -->
      <div class="intro-body">

        <!-- ===== 整体介绍 ===== -->
        <template v-if="activeTab === 'overview'">

          <!-- 5.1 平台介绍 -->
          <section class="intro-section">
            <h2>欢迎来到 SurveyFiller 👋</h2>
            <p class="intro-desc">SurveyFiller 是一个「问卷互助平台」。</p>
            <p class="intro-desc">在这里，你可以：</p>
            <ul class="intro-list">
              <li>📝 创建自己的问卷（也可以用 AI 帮你生成）</li>
              <li>📋 把问卷发布到社区</li>
              <li>💰 通过填写别人的问卷获得积分</li>
              <li>🚀 使用积分让更多人填写你的问卷</li>
            </ul>
            <p class="intro-desc muted">
              平台会根据你的个人信息和填写行为，通过推荐系统帮你匹配更适合填写的问卷，
              让你更快获得积分，也更快收集到问卷数据。
            </p>
          </section>

          <!-- 5.2 积分制度 -->
          <section class="intro-section">
            <h2>平台是如何运作的？💰</h2>
            <p class="intro-desc">
              SurveyFiller 使用「积分制度」。每一份问卷通过 AI 自动评估难度，等级 1 - 5：
            </p>
            <div class="difficulty-table">
              <div v-for="n in 5" :key="n" class="difficulty-row">
                <div class="diff-stars">
                  <span v-for="i in n" :key="'a' + i" class="star">★</span>
                  <span v-for="i in (5 - n)" :key="'b' + i" class="star empty">★</span>
                </div>
                <span class="diff-arrow">→</span>
                <span class="diff-reward">+{{ n }} 积分</span>
              </div>
            </div>
            <p class="intro-desc muted">填写不同难度的问卷获得对应积分，积分可以用来发布自己的问卷。</p>
            <div class="future-hint">
              🔜 未来还会支持：购买积分 · 积分返现 · 高级数据分析
            </div>
          </section>

          <!-- 5.3 完善个人信息（高亮 section）：首次设备访客或资料已满时隐藏 -->
          <section v-if="showProfileSection" class="intro-section highlight-section" ref="profileSectionRef">
            <h2>建议先完善你的个人信息 ✨</h2>
            <p class="intro-desc">
              推荐系统需要一些基础信息，才能帮你匹配更适合填写的问卷。
              个人信息越完整，系统推荐的问卷就会越精准，你也可以更快获得积分。
            </p>
            <button class="primary-btn" @click="goToProfile">完善个人信息</button>
            <p class="hint-text">也可以随时在侧边栏「👤 个人资料」中修改</p>
          </section>

          <!-- 首次访客登录引导 -->
          <section v-if="showLoginGuide" class="intro-section login-guide-section">
            <h2>准备好了吗？🎉</h2>
            <p class="intro-desc">注册账号，开始你的问卷互助之旅！</p>
            <button class="primary-btn login-btn" @click="goToAuth">立即登录 / 注册</button>
          </section>

        </template>

        <!-- ===== 模块介绍 ===== -->
        <template v-else>
          <p class="intro-desc muted intro-nav-hint">
            通过左侧的 <strong>☰ 侧边栏</strong> 切换不同功能模块。
          </p>

          <section class="intro-section module-section">
            <span class="module-icon">📋</span>
            <div class="module-content">
              <h3>任务大厅</h3>
              <p>填写问卷赚积分的地方。系统会根据你的个人信息和填写行为，推荐最适合你的问卷。</p>
              <p class="muted">不感兴趣的问卷点「×」跳过；点「换一批」查看新的推荐。</p>
            </div>
          </section>

          <section class="intro-section module-section">
            <span class="module-icon">📝</span>
            <div class="module-content">
              <h3>问卷管理</h3>
              <p>管理你创建的所有问卷，分为 <strong>未发出</strong> / <strong>已发出</strong> / <strong>已结束</strong> 三种状态。</p>
              <p class="muted">可编辑未发布问卷，或查看数据分析。</p>
            </div>
          </section>

          <section class="intro-section module-section">
            <span class="module-icon">💰</span>
            <div class="module-content">
              <h3>积分记录</h3>
              <p>记录所有积分变化，包括收入和支出。</p>
            </div>
          </section>

          <section class="intro-section module-section">
            <span class="module-icon">❓</span>
            <div class="module-content">
              <h3>帮助中心</h3>
              <p>整理了常见问题，遇到问题可以先在这里查看，我们也会持续更新。</p>
            </div>
          </section>

          <section class="intro-section module-section">
            <span class="module-icon">👤</span>
            <div class="module-content">
              <h3>个人资料</h3>
              <p>管理个人信息，还可以设置实时状态。</p>
              <p class="muted">你的个人信息会受到平台保护，系统仅在推荐问卷时参考。</p>
            </div>
          </section>
        </template>

      </div>
    </div>
  </div>
</template>

<style scoped>
/* ---- 遮罩 ---- */
.intro-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 16px;
  animation: overlayFadeIn 0.28s ease;
}

.intro-overlay.is-closing {
  background: rgba(0, 0, 0, 0);
  transition: background-color 0.42s ease;
  pointer-events: none;
}

@keyframes overlayFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* ---- 卡片 ---- */
.intro-card {
  background: #fff;
  border-radius: 20px;
  width: 100%;
  max-width: 520px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.18);
  position: relative;
  overflow: hidden;
  transform-origin: center center;
  animation: cardSlideIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes cardSlideIn {
  from { opacity: 0; transform: translateY(24px) scale(0.94); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

/* ---- 关闭按钮 ---- */
.intro-close-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(0, 0, 0, 0.07);
  border: none;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  font-size: 13px;
  cursor: pointer;
  color: #555;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  flex-shrink: 0;
}
.intro-close-btn:hover { background: rgba(0, 0, 0, 0.14); }

/* ---- Tabs ---- */
.intro-tabs {
  display: flex;
  border-bottom: 1px solid #e8eef5;
  padding: 0 20px;
  flex-shrink: 0;
  background: #fff;
}

.tab-btn {
  flex: 1;
  padding: 14px 0;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  font-size: 14px;
  font-weight: 600;
  color: #8fa4c0;
  cursor: pointer;
  transition: all 0.2s;
}
.tab-btn.active {
  color: #1e4fb4;
  border-bottom-color: #1e4fb4;
}
.tab-btn:hover:not(.active) { color: #3a5cbf; }

/* ---- 内容滚动区 ---- */
.intro-body {
  overflow-y: auto;
  padding: 20px 20px 24px;
  flex: 1;
  -webkit-overflow-scrolling: touch;
}
.intro-body::-webkit-scrollbar { width: 4px; }
.intro-body::-webkit-scrollbar-thumb { background: #d0daea; border-radius: 4px; }

/* ---- Section ---- */
.intro-section {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f4fa;
}
.intro-section:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }

.intro-section h2 {
  font-size: 16px;
  font-weight: 700;
  color: #1a202c;
  margin: 0 0 10px;
}

.intro-desc {
  font-size: 13px;
  color: #47577a;
  line-height: 1.75;
  margin: 5px 0;
}
.intro-desc.muted, .muted { color: #8fa4c0; font-size: 12px; }

.intro-list {
  list-style: none;
  padding: 0;
  margin: 8px 0;
}
.intro-list li {
  font-size: 13px;
  color: #47577a;
  padding: 3px 0;
  line-height: 1.65;
}

/* ---- 难度表 ---- */
.difficulty-table {
  background: #f8faff;
  border-radius: 10px;
  padding: 10px 14px;
  margin: 10px 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.difficulty-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.diff-stars { flex: 0 0 auto; display: flex; gap: 1px; }
.star { font-size: 13px; color: #f5a623; line-height: 1; }
.star.empty { color: #dce4f0; }
.diff-arrow { color: #b0c4de; font-size: 13px; min-width: 16px; text-align: center; }
.diff-reward { font-size: 12px; color: #1e4fb4; font-weight: 600; }

.future-hint {
  background: #f0f4ff;
  border-radius: 8px;
  padding: 9px 13px;
  margin-top: 10px;
  font-size: 12px;
  color: #4a6098;
  line-height: 1.5;
}

/* ---- 高亮 section ---- */
.highlight-section {
  background: linear-gradient(135deg, #f0f4ff 0%, #e8f0fe 100%);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #c8d8f5 !important;
  border-bottom: 1px solid #c8d8f5 !important;
}

/* ---- 登录引导 section ---- */
.login-guide-section {
  background: linear-gradient(135deg, #fff8e8 0%, #fff3cc 100%);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #ffd880 !important;
  border-bottom: 1px solid #ffd880 !important;
  text-align: center;
}

/* ---- 按钮 ---- */
.primary-btn {
  display: block;
  width: 100%;
  padding: 11px;
  background: linear-gradient(135deg, #1e4fb4 0%, #1a3f8a 100%);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 12px;
  transition: all 0.25s;
  box-shadow: 0 4px 12px rgba(30, 79, 180, 0.25);
}
.primary-btn:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(30, 79, 180, 0.35); }
.primary-btn:active { transform: translateY(0); }

.login-btn {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.28);
}
.login-btn:hover { box-shadow: 0 6px 16px rgba(245, 158, 11, 0.42); }

.hint-text {
  font-size: 11px;
  color: #8fa4c0;
  text-align: center;
  margin: 7px 0 0;
}

/* ---- 模块介绍 ---- */
.intro-nav-hint { margin-bottom: 14px; }

.module-section {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.module-icon {
  font-size: 26px;
  flex-shrink: 0;
  line-height: 1.2;
  padding-top: 1px;
}
.module-content h3 {
  font-size: 14px;
  font-weight: 700;
  color: #1a202c;
  margin: 0 0 5px;
}
.module-content p {
  font-size: 13px;
  color: #47577a;
  margin: 3px 0;
  line-height: 1.6;
}

.profile-btn {
  margin-top: 8px;
  padding: 7px 14px;
  background: transparent;
  color: #1e4fb4;
  border: 1px solid #1e4fb4;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.profile-btn:hover { background: #1e4fb4; color: #fff; }

/* ---- 手机适配（底部 sheet 样式） ---- */
@media (max-width: 540px) {
  .intro-overlay {
    padding: 0;
    align-items: flex-end;
  }
  .intro-card {
    border-radius: 20px 20px 0 0;
    max-height: 88vh;
    max-width: 100%;
  }
  .intro-tabs { padding: 0 16px; }
  .intro-body { padding: 16px 16px 32px; }
  .intro-section h2 { font-size: 15px; }
  .tab-btn { font-size: 13px; }
  .module-icon { font-size: 22px; }
}
</style>
