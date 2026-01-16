<template>
  <div class="user-profile-container">
    <!-- 返回按钮 -->
    <div class="header">
      <button class="back-button" @click="goBack">
        <span class="arrow">←</span> 返回个人主页
      </button>
    </div>

    <!-- 主内容区域 -->
    <div class="content-wrapper">
      <!-- 引导文案 -->
      <div class="guide-banner">
        <div class="guide-icon">✨</div>
        <div class="guide-text">
          完善基础信息（学院/专业），能让 <strong>80%</strong> 的精准问卷找到你噢！
        </div>
      </div>

      <!-- 核心建议区 -->
      <div class="section-card core-section">
        <div class="section-header">
          <h2 class="section-title">核心信息</h2>
          <span class="recommended-badge">强烈推荐</span>
        </div>

        <div class="form-grid">
          <!-- 性别 -->
          <div class="form-item">
            <label class="form-label">性别</label>
            <div class="radio-group">
              <label class="radio-option" v-for="gender in genderOptions" :key="gender">
                <input type="radio" :value="gender" v-model="formData.gender" />
                <span>{{ gender }}</span>
              </label>
            </div>
          </div>

          <!-- 年龄 -->
          <div class="form-item">
            <label class="form-label">年龄</label>
            <input
              type="number"
              v-model.number="formData.age"
              placeholder="请输入您的年龄"
              class="form-input"
              min="16"
              max="100"
            />
          </div>

          <!-- 年级 -->
          <div class="form-item">
            <label class="form-label">年级</label>
            <select v-model="formData.grade" class="form-select">
              <option value="">请选择年级</option>
              <option v-for="grade in gradeOptions" :key="grade" :value="grade">{{ grade }}</option>
            </select>
          </div>

          <!-- 学院 -->
          <div class="form-item full-width">
            <label class="form-label">学院</label>
            <input
              type="text"
              v-model="formData.college"
              placeholder="例如：物理学院"
              class="form-input"
              list="college-suggestions"
            />
            <datalist id="college-suggestions">
              <option v-for="college in collegeSuggestions" :key="college" :value="college" />
            </datalist>
            <span class="input-hint">请输入完整学院名称</span>
          </div>

          <!-- 专业 -->
          <div class="form-item full-width">
            <label class="form-label">专业</label>
            <input
              type="text"
              v-model="formData.major"
              placeholder="例如：应用物理学"
              class="form-input"
            />
            <span class="input-hint">请输入完整专业名称</span>
          </div>
        </div>
      </div>

      <!-- 深度画像区 -->
      <div class="section-card deep-section">
        <div class="section-header">
          <h2 class="section-title">深度画像</h2>
          <span class="optional-badge">帮助精准匹配</span>
        </div>

        <div class="form-grid">
          <!-- MBTI -->
          <div class="form-item">
            <label class="form-label">MBTI 人格</label>
            <select v-model="formData.mbti" class="form-select">
              <option value="">请选择您的MBTI类型</option>
              <option v-for="mbti in mbtiOptions" :key="mbti" :value="mbti">{{ mbti }}</option>
            </select>
          </div>

          <!-- 研究方向/兴趣课程 -->
          <div class="form-item full-width">
            <label class="form-label">研究方向 / 兴趣课程</label>
            <input
              type="text"
              v-model="formData.interests"
              placeholder="例如：人工智能、德语初级"
              class="form-input"
            />
          </div>

          <!-- 社团/组织经历 -->
          <div class="form-item full-width">
            <label class="form-label">社团 / 组织经历</label>
            <input
              type="text"
              v-model="formData.organizations"
              placeholder="例如：校学生会、摄影社"
              class="form-input"
            />
          </div>

          <!-- 消费偏好 -->
          <div class="form-item full-width">
            <label class="form-label">消费偏好</label>
            <div class="tag-group">
              <span
                v-for="tag in consumptionTags"
                :key="tag"
                class="tag"
                :class="{ active: formData.consumptionPreferences.includes(tag) }"
                @click="toggleTag('consumptionPreferences', tag)"
              >
                {{ tag }}
              </span>
            </div>
          </div>

          <!-- 职业意向 -->
          <div class="form-item full-width">
            <label class="form-label">职业意向</label>
            <div class="tag-group">
              <span
                v-for="tag in careerTags"
                :key="tag"
                class="tag"
                :class="{ active: formData.careerIntention.includes(tag) }"
                @click="toggleTag('careerIntention', tag)"
              >
                {{ tag }}
              </span>
            </div>
          </div>

          <!-- 软硬技能 -->
          <div class="form-item full-width">
            <label class="form-label">软硬技能</label>
            <div class="tag-group">
              <span
                v-for="tag in skillTags"
                :key="tag"
                class="tag"
                :class="{ active: formData.skills.includes(tag) }"
                @click="toggleTag('skills', tag)"
              >
                {{ tag }}
              </span>
            </div>
          </div>

          <!-- 当前状态 -->
          <div class="form-item full-width">
            <label class="form-label">当前状态</label>
            <input
              type="text"
              v-model="formData.currentStatus"
              placeholder="例如：正在备战期末、失恋中、找实习中"
              class="form-input"
            />
          </div>
        </div>
      </div>

      <!-- 匹配进度可视化 -->
      <div class="progress-section">
        <div class="progress-info">
          <div class="progress-icon">🎯</div>
          <div class="progress-text">
            <div class="progress-title">个人画像完成度</div>
            <div class="progress-subtitle">完善度越高，推荐越精准</div>
          </div>
        </div>
        <div class="progress-bar-container">
          <div class="progress-bar" :style="{ width: completionRate + '%' }">
            <span class="progress-label">{{ completionRate }}%</span>
          </div>
        </div>
      </div>

      <!-- 保存按钮 -->
      <div class="action-bar">
        <button class="save-button" @click="saveProfile">保存修改</button>
      </div>
    </div>

    <!-- Toast 提示 -->
    <transition name="toast">
      <div v-if="showToast" class="toast">
        <span class="toast-icon">✓</span>
        {{ toastMessage }}
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 表单数据
const formData = ref({
  gender: '',
  age: null,
  grade: '',
  college: '',
  major: '',
  mbti: '',
  interests: '',
  organizations: '',
  consumptionPreferences: [],
  careerIntention: [],
  skills: [],
  currentStatus: ''
})

// 选项配置
const genderOptions = ['男', '女', '其他', '保密']
const gradeOptions = ['大一', '大二', '大三', '大四', '研一', '研二', '研三', '博士']
const mbtiOptions = [
  'INTJ', 'INTP', 'ENTJ', 'ENTP',
  'INFJ', 'INFP', 'ENFJ', 'ENFP',
  'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
  'ISTP', 'ISFP', 'ESTP', 'ESFP'
]

const collegeSuggestions = [
  '物理学院',
  '计算机科学学院',
  '数学学院',
  '化学学院',
  '生命科学学院',
  '经济管理学院',
  '人文学院',
  '外国语学院'
]

const consumptionTags = ['数码', '美妆', '奶茶', '户外', '运动', '阅读', '游戏', '音乐', '影视', '美食']
const careerTags = ['考公', '大厂', '学术', '创业', '出国', '考研', '自由职业']
const skillTags = ['Python', 'Java', 'C++', '视频剪辑', '英语口译', 'PS', 'Excel', '写作', '演讲', '摄影']

// Toast
const showToast = ref(false)
const toastMessage = ref('')

// 计算完成度
const completionRate = computed(() => {
  const fields = [
    formData.value.gender,
    formData.value.age,
    formData.value.grade,
    formData.value.college,
    formData.value.major,
    formData.value.mbti,
    formData.value.interests,
    formData.value.organizations,
    formData.value.consumptionPreferences.length > 0,
    formData.value.careerIntention.length > 0,
    formData.value.skills.length > 0,
    formData.value.currentStatus
  ]
  
  const filledCount = fields.filter(field => field).length
  return Math.round((filledCount / fields.length) * 100)
})

// 切换标签选择
const toggleTag = (fieldName, tag) => {
  const index = formData.value[fieldName].indexOf(tag)
  if (index > -1) {
    formData.value[fieldName].splice(index, 1)
  } else {
    formData.value[fieldName].push(tag)
  }
}

// 保存个人信息
const saveProfile = () => {
  // TODO: 实现保存逻辑，调用后端 API
  console.log('保存的数据:', formData.value)
  
  toastMessage.value = '信息已更新，已为您优化任务大厅的推荐逻辑'
  showToast.value = true
  
  setTimeout(() => {
    showToast.value = false
  }, 3000)
}

// 返回个人主页
const goBack = () => {
  router.push('/profile')
}
</script>

<style scoped>
.user-profile-container {
  min-height: 100vh;
  width: 100vw;
  background: linear-gradient(135deg, #e3f2fd 0%, #f5f9ff 100%);
  padding: 20px;
  overflow-x: hidden;
  position: relative;
}

/* 头部 */
.header {
  max-width: 1200px;
  width: 100%;
  margin: 0 auto 20px;
  padding: 0 10px;
}

.back-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: white;
  border: 1px solid #2196f3;
  border-radius: 8px;
  color: #2196f3;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.back-button:hover {
  background: #2196f3;
  color: white;
  transform: translateX(-5px);
}

.arrow {
  font-size: 18px;
  font-weight: bold;
}

/* 内容区域 */
.content-wrapper {
  max-width: 1200px;
  width: calc(100% - 20px);
  margin: 0 auto;
  padding: 0 10px;
  box-sizing: border-box;
}

/* 引导横幅 */
.guide-banner {
  background: linear-gradient(135deg, #42a5f5 0%, #2196f3 100%);
  color: white;
  padding: 20px 30px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 30px;
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
}

.guide-icon {
  font-size: 32px;
}

.guide-text {
  font-size: 16px;
  line-height: 1.5;
}

.guide-text strong {
  font-size: 20px;
  font-weight: bold;
}

/* 卡片区域 */
.section-card {
  background: white;
  border-radius: 16px;
  padding: 30px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.core-section {
  border-left: 4px solid #2196f3;
  box-shadow: 0 4px 16px rgba(33, 150, 243, 0.15);
}

.deep-section {
  background: #fafbff;
  border-left: 4px solid #90caf9;
}

/* 区块标题 */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e3f2fd;
}

.section-title {
  font-size: 24px;
  font-weight: bold;
  color: #1565c0;
  margin: 0;
}

.recommended-badge {
  background: linear-gradient(135deg, #ff6b6b, #ff8e53);
  color: white;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: bold;
}

.optional-badge {
  background: #e3f2fd;
  color: #2196f3;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

/* 表单网格 */
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-item.full-width {
  grid-column: 1 / -1;
}

.form-label {
  font-size: 14px;
  font-weight: 600;
  color: #424242;
}

.form-input,
.form-select {
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
  background: white;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #2196f3;
  box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
}

.input-hint {
  font-size: 12px;
  color: #9e9e9e;
  margin-top: -4px;
}

/* 单选按钮组 */
.radio-group {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.radio-option {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 14px;
}

.radio-option input[type="radio"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #2196f3;
}

/* 标签组 */
.tag-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag {
  padding: 8px 16px;
  background: #e3f2fd;
  color: #1976d2;
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  user-select: none;
}

.tag:hover {
  background: #bbdefb;
  transform: translateY(-2px);
}

.tag.active {
  background: linear-gradient(135deg, #2196f3, #1976d2);
  color: white;
  border-color: #1565c0;
  font-weight: 600;
}

/* 进度区域 */
.progress-section {
  background: white;
  border-radius: 16px;
  padding: 25px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.progress-info {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}

.progress-icon {
  font-size: 36px;
}

.progress-title {
  font-size: 18px;
  font-weight: bold;
  color: #1565c0;
}

.progress-subtitle {
  font-size: 13px;
  color: #757575;
  margin-top: 2px;
}

.progress-bar-container {
  height: 30px;
  background: #e3f2fd;
  border-radius: 15px;
  overflow: hidden;
  position: relative;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #42a5f5 0%, #2196f3 50%, #1976d2 100%);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 15px;
  transition: width 0.5s ease;
  border-radius: 15px;
}

.progress-label {
  color: white;
  font-weight: bold;
  font-size: 14px;
}

/* 操作栏 */
.action-bar {
  text-align: center;
  margin-top: 30px;
}

.save-button {
  padding: 14px 60px;
  background: linear-gradient(135deg, #2196f3, #1976d2);
  color: white;
  border: none;
  border-radius: 25px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.4);
}

.save-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(33, 150, 243, 0.5);
}

.save-button:active {
  transform: translateY(0);
}

/* Toast 提示 */
.toast {
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #4caf50, #45a049);
  color: white;
  padding: 16px 30px;
  border-radius: 12px;
  box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
  font-size: 15px;
  font-weight: 500;
  z-index: 1000;
  display: flex;
  align-items: center;
  gap: 10px;
}

.toast-icon {
  font-size: 20px;
  font-weight: bold;
}

/* Toast 动画 */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .user-profile-container {
    padding: 15px 10px;
  }

  .header {
    padding: 0 5px;
  }

  .content-wrapper {
    padding: 0 5px;
  }

  .form-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }

  .section-card {
    padding: 20px 15px;
  }

  .guide-banner {
    flex-direction: column;
    text-align: center;
    padding: 15px 20px;
  }

  .guide-icon {
    font-size: 28px;
  }

  .guide-text {
    font-size: 14px;
  }

  .section-title {
    font-size: 20px;
  }

  .form-input,
  .form-select {
    font-size: 16px; /* 防止 iOS 自动缩放 */
  }

  .save-button {
    width: 100%;
    padding: 14px 20px;
  }

  .progress-bar-container {
    height: 25px;
  }

  .progress-label {
    font-size: 12px;
  }
}

@media (max-width: 480px) {
  .user-profile-container {
    padding: 10px 5px;
  }

  .guide-banner {
    padding: 12px 15px;
  }

  .guide-text {
    font-size: 13px;
  }

  .section-card {
    padding: 15px 12px;
  }

  .section-title {
    font-size: 18px;
  }

  .recommended-badge,
  .optional-badge {
    font-size: 11px;
    padding: 5px 12px;
  }

  .tag {
    padding: 6px 12px;
    font-size: 12px;
  }

  .back-button {
    padding: 8px 16px;
    font-size: 13px;
  }

  .action-bar {
    margin-top: 20px;
  }
}
</style>
