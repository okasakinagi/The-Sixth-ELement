<template>
  <div class="user-profile-container">
    <!-- 返回按钮 -->
    <div class="header">
      <button class="back-button" @click="goBack">
        <span class="arrow">←</span> 返回个人主页
      </button>
    </div>

    <!-- 悬浮画像完成度 -->
    <div class="floating-progress" :class="{ mobile: isMobile }">
      <div class="floating-header">
        <span class="floating-title">画像完成度</span>
        <button class="floating-action" @click="saveProfile">保存</button>
      </div>
      <div class="floating-body">
        <div class="circular-progress small">
          <svg class="progress-ring" width="84" height="84">
            <circle
              class="progress-ring-circle-bg"
              stroke="#e3f2fd"
              stroke-width="8"
              fill="transparent"
              r="34"
              cx="42"
              cy="42"
            />
            <circle
              class="progress-ring-circle"
              stroke="url(#edit-gradient)"
              stroke-width="8"
              fill="transparent"
              r="34"
              cx="42"
              cy="42"
              :stroke-dasharray="floatingCircumference"
              :stroke-dashoffset="floatingOffset"
            />
            <defs>
              <linearGradient id="edit-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#42a5f5;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#1976d2;stop-opacity:1" />
              </linearGradient>
            </defs>
          </svg>
          <div class="progress-text small">
            <span class="progress-number">{{ completionRate }}%</span>
          </div>
        </div>
        <div class="floating-info">
          <p class="floating-sub">完善度越高，推荐越精准</p>
          <p class="floating-tip">{{ completionRate >= 80 ? '很棒，几乎完成' : '继续补充关键信息' }}</p>
        </div>
      </div>
    </div>

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
            <div class="gender-grid">
              <label
                v-for="gender in genderOptions"
                :key="gender.value"
                class="gender-card"
                :class="{ active: formData.gender === gender.value }"
              >
                <input
                  type="radio"
                  :value="gender.value"
                  v-model="formData.gender"
                />
                <div class="gender-icon">{{ gender.icon }}</div>
                <div class="gender-title">{{ gender.label }}</div>
                <div class="gender-desc">{{ gender.desc }}</div>
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
            <div class="tag-section">
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
              <div class="custom-tag-input">
                <input
                  v-model="customConsumptionInput"
                  type="text"
                  placeholder="自定义添加..."
                  class="tag-input"
                  @keyup.enter="addCustomTag('consumptionPreferences', customConsumptionInput)"
                />
                <button
                  class="add-tag-btn"
                  @click="addCustomTag('consumptionPreferences', customConsumptionInput)"
                >
                  + 添加
                </button>
              </div>
              <div class="selected-tags" v-if="formData.consumptionPreferences.length > 0">
                <span class="tag-label">已选择：</span>
                <span
                  v-for="tag in formData.consumptionPreferences"
                  :key="tag"
                  class="selected-tag"
                >
                  {{ tag }}
                  <span class="remove-tag" @click="removeTag('consumptionPreferences', tag)">×</span>
                </span>
              </div>
            </div>
          </div>

          <!-- 职业意向 -->
          <div class="form-item full-width">
            <label class="form-label">职业意向</label>
            <div class="tag-section">
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
              <div class="custom-tag-input">
                <input
                  v-model="customCareerInput"
                  type="text"
                  placeholder="自定义添加..."
                  class="tag-input"
                  @keyup.enter="addCustomTag('careerIntention', customCareerInput)"
                />
                <button
                  class="add-tag-btn"
                  @click="addCustomTag('careerIntention', customCareerInput)"
                >
                  + 添加
                </button>
              </div>
              <div class="selected-tags" v-if="formData.careerIntention.length > 0">
                <span class="tag-label">已选择：</span>
                <span
                  v-for="tag in formData.careerIntention"
                  :key="tag"
                  class="selected-tag"
                >
                  {{ tag }}
                  <span class="remove-tag" @click="removeTag('careerIntention', tag)">×</span>
                </span>
              </div>
            </div>
          </div>

          <!-- 软硬技能 -->
          <div class="form-item full-width">
            <label class="form-label">软硬技能</label>
            <div class="tag-section">
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
              <div class="custom-tag-input">
                <input
                  v-model="customSkillInput"
                  type="text"
                  placeholder="自定义添加..."
                  class="tag-input"
                  @keyup.enter="addCustomTag('skills', customSkillInput)"
                />
                <button
                  class="add-tag-btn"
                  @click="addCustomTag('skills', customSkillInput)"
                >
                  + 添加
                </button>
              </div>
              <div class="selected-tags" v-if="formData.skills.length > 0">
                <span class="tag-label">已选择：</span>
                <span
                  v-for="tag in formData.skills"
                  :key="tag"
                  class="selected-tag"
                >
                  {{ tag }}
                  <span class="remove-tag" @click="removeTag('skills', tag)">×</span>
                </span>
              </div>
            </div>
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
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { getUserProfile, updateUserProfile } from '@/utils/profileApi'

const router = useRouter()

const STORAGE_KEY = 'sixth_element_profile'
const defaultProfile = {
  gender: '',
  age: null,
  grade: '',
  college: '',
  major: '',
  mbti: '',
  interests: [],
  organizations: [],
  consumptionPreferences: [],
  careerIntention: [],
  skills: [],
  currentStatus: ''
}

// 表单数据
const formData = ref({ ...defaultProfile })
const isMobile = ref(window.innerWidth <= 768)
const isLoading = ref(false)
const errorMessage = ref('')
const handleResize = () => {
  isMobile.value = window.innerWidth <= 768
}

// 选项配置
const genderOptions = [
  { value: '男', label: '男', icon: '♂', desc: 'He/Him' },
  { value: '女', label: '女', icon: '♀', desc: 'She/Her' },
  { value: '其他', label: '其他', icon: '☆', desc: 'Non-binary' },
  { value: '保密', label: '保密', icon: '…', desc: 'Prefer not to say' }
]
const gradeOptions = [
  '大一', '大二', '大三', '大四', '大五',
  '研一', '研二', '研三',
  '博一', '博二', '博三', '博四', '博五'
]
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

// 自定义标签输入
const customConsumptionInput = ref('')
const customCareerInput = ref('')
const customSkillInput = ref('')

// Toast
const showToast = ref(false)
const toastMessage = ref('')

// 计算完成度（与后端逻辑保持一致）
const completionRate = computed(() => {
  let filledCount = 0
  
  // 单值字段（有值即算填写）
  if (formData.value.gender) filledCount++
  if (formData.value.age) filledCount++
  if (formData.value.grade) filledCount++
  if (formData.value.college) filledCount++
  if (formData.value.major) filledCount++
  if (formData.value.mbti) filledCount++
  if (formData.value.currentStatus) filledCount++
  
  // 数组字段（数组有元素即算填写）
  if (formData.value.interests && formData.value.interests.length > 0) filledCount++
  if (formData.value.organizations && formData.value.organizations.length > 0) filledCount++
  if (formData.value.consumptionPreferences && formData.value.consumptionPreferences.length > 0) filledCount++
  if (formData.value.careerIntention && formData.value.careerIntention.length > 0) filledCount++
  if (formData.value.skills && formData.value.skills.length > 0) filledCount++
  
  const totalFields = 12
  return Math.round((filledCount / totalFields) * 100)
})

const floatingCircumference = 2 * Math.PI * 34
const floatingOffset = computed(() => floatingCircumference - (completionRate.value / 100) * floatingCircumference)

// 切换标签选择
const toggleTag = (fieldName, tag) => {
  const index = formData.value[fieldName].indexOf(tag)
  if (index > -1) {
    formData.value[fieldName].splice(index, 1)
  } else {
    formData.value[fieldName].push(tag)
  }
}

// 添加自定义标签
const addCustomTag = (fieldName, inputRef) => {
  const value = inputRef.value.trim()
  if (value && !formData.value[fieldName].includes(value)) {
    formData.value[fieldName].push(value)
    inputRef.value = ''
  }
}

// 移除标签
const removeTag = (fieldName, tag) => {
  const index = formData.value[fieldName].indexOf(tag)
  if (index > -1) {
    formData.value[fieldName].splice(index, 1)
  }
}

// 保存个人信息
const saveProfile = async () => {
  isLoading.value = true
  errorMessage.value = ''
  
  try {
    // 准备提交数据（转换为后端API格式）
    const payload = {
      gender: formData.value.gender || null,
      age: formData.value.age || null,
      grade: formData.value.grade || null,
      college: formData.value.college || null,
      major: formData.value.major || null,
      mbti: formData.value.mbti || null,
      interests: Array.isArray(formData.value.interests) ? formData.value.interests : [],
      organizations: Array.isArray(formData.value.organizations) ? formData.value.organizations : [],
      consumption_preferences: Array.isArray(formData.value.consumptionPreferences) ? formData.value.consumptionPreferences : [],
      career_intention: Array.isArray(formData.value.careerIntention) ? formData.value.careerIntention : [],
      skills: Array.isArray(formData.value.skills) ? formData.value.skills : [],
      current_status: formData.value.currentStatus || null
    }
    
    // 调用API（使用PUT完整替换）
    await updateUserProfile(payload)
    
    toastMessage.value = '信息已保存，正在返回...'
    showToast.value = true
    
    setTimeout(() => {
      showToast.value = false
      router.push('/profile')
    }, 1500)
  } catch (error) {
    console.error('保存失败:', error)
    errorMessage.value = error.message
    toastMessage.value = '保存失败: ' + error.message
    showToast.value = true
    setTimeout(() => {
      showToast.value = false
    }, 3000)
  } finally {
    isLoading.value = false
  }
}

// 返回个人主页
const goBack = () => {
  router.push('/profile')
}

// 加载用户画像数据
const loadProfile = async () => {
  isLoading.value = true
  try {
    const profile = await getUserProfile()
    
    // 映射后端数据到表单格式
    formData.value = {
      gender: profile.gender || '',
      age: profile.age || null,
      grade: profile.grade || '',
      college: profile.college || '',
      major: profile.major || '',
      mbti: profile.mbti || '',
      interests: profile.interests || [],
      organizations: profile.organizations || [],
      consumptionPreferences: profile.consumption_preferences || [],
      careerIntention: profile.career_intention || [],
      skills: profile.skills || [],
      currentStatus: profile.current_status || ''
    }
  } catch (error) {
    console.error('加载画像失败:', error)
    errorMessage.value = error.message
    
    // 如果是认证错误，跳转到登录页
    if (error.message.includes('登录')) {
      setTimeout(() => {
        router.push('/auth')
      }, 2000)
    }
  } finally {
    isLoading.value = false
  }
}

// 初始化时加载数据
onMounted(() => {
  loadProfile()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.user-profile-container {
  min-height: 100vh;
  width: 100%;
  background: linear-gradient(135deg, #e3f2fd 0%, #f5f9ff 100%);
  padding: 28px 20px 36px;
  overflow-x: hidden;
  position: relative;
}

/* 头部 */
.header {
  width: 100%;
  max-width: 100%;
  margin: 0 0 20px;
  padding: 0 12px;
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
  width: 100%;
  max-width: 100%;
  margin: 0;
  padding: 0 12px;
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
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
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

.gender-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
}

.gender-card {
  position: relative;
  padding: 16px 14px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.gender-card input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.gender-card:hover {
  border-color: #2196f3;
  box-shadow: 0 6px 14px rgba(33, 150, 243, 0.12);
  transform: translateY(-2px);
}

.gender-card.active {
  border-color: #2196f3;
  background: linear-gradient(135deg, #e3f2fd 0%, #f5f9ff 100%);
  box-shadow: 0 8px 16px rgba(33, 150, 243, 0.16);
}

.gender-icon {
  font-size: 20px;
  color: #1976d2;
}

.gender-title {
  font-weight: 700;
  color: #1f2b3a;
}

.gender-desc {
  font-size: 12px;
  color: #6b7a90;
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

/* 标签区域 */
.tag-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 自定义标签输入 */
.custom-tag-input {
  display: flex;
  gap: 8px;
  align-items: center;
}

.tag-input {
  flex: 1;
  padding: 10px 14px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
}

.tag-input:focus {
  outline: none;
  border-color: #2196f3;
  box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
}

.add-tag-btn {
  padding: 10px 18px;
  background: linear-gradient(135deg, #42a5f5, #2196f3);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.add-tag-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
}

/* 已选择的标签 */
.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px;
  background: #f5f9ff;
  border-radius: 8px;
  border: 1px solid #e3f2fd;
  align-items: center;
}

.tag-label {
  font-size: 13px;
  color: #757575;
  font-weight: 600;
  white-space: nowrap;
}

.selected-tag {
  padding: 6px 12px;
  background: linear-gradient(135deg, #2196f3, #1976d2);
  color: white;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.remove-tag {
  cursor: pointer;
  font-size: 18px;
  font-weight: bold;
  line-height: 1;
  transition: all 0.2s ease;
}

.remove-tag:hover {
  transform: scale(1.2);
  color: #ffeb3b;
}

/* 进度区域 */
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

/* 悬浮画像进度 */
.floating-progress {
  position: fixed;
  right: 24px;
  bottom: 24px;
  width: 260px;
  background: #ffffff;
  border: 1px solid #e3e9f5;
  border-radius: 16px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.12);
  padding: 14px;
  z-index: 30;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.floating-progress.mobile {
  right: 14px;
  bottom: 14px;
  width: 220px;
}

.floating-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.floating-title {
  font-weight: 700;
  color: #0b2b66;
  font-size: 14px;
}

.floating-action {
  border: none;
  background: linear-gradient(135deg, #42a5f5, #2196f3);
  color: #fff;
  border-radius: 10px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.28);
  transition: all 0.25s ease;
}

.floating-action:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(33, 150, 243, 0.35);
}

.floating-body {
  display: flex;
  align-items: center;
  gap: 12px;
}

.circular-progress.small {
  width: 84px;
  height: 84px;
  position: relative;
}

.progress-ring {
  transform: rotate(-90deg);
}

.progress-ring-circle {
  transition: stroke-dashoffset 0.5s ease;
  stroke-linecap: round;
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-text.small .progress-number {
  font-size: 20px;
  font-weight: 700;
  color: #1976d2;
}

.floating-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.floating-sub {
  margin: 0;
  font-size: 13px;
  color: #5c7599;
}

.floating-tip {
  margin: 0;
  font-size: 14px;
  color: #1565c0;
  font-weight: 700;
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
    padding: 16px 10px 22px;
  }

  .header {
    padding: 0 8px;
  }

  .content-wrapper {
    padding: 0 8px;
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

@media (max-width: 640px) {
  .floating-progress {
    position: sticky;
    width: 100%;
    right: auto;
    bottom: auto;
    margin: 14px 0;
  }
}

@media (max-width: 480px) {
  .user-profile-container {
    padding: 12px 6px 18px;
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
