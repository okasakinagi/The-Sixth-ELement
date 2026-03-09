<template>
  <div class="user-profile-container">
    <!-- 返回按钮 -->
    <div class="header">
      <button class="back-button" @click="goBack">
        <span class="arrow">←</span> 返回个人主页
      </button>
    </div>

    <!-- 悬浮画像完成度 -->
    <!-- 哨兵：跟随正常文档流，IntersectionObserver 监听它是否离开视口 -->
    <div ref="floatingSentinelRef" style="height:1px;pointer-events:none;visibility:hidden;"></div>
    <!-- 占位：sticky 激活时撑开原位置，防止布局跳动 -->
    <div v-if="isMobile && floatingSticky" :style="{ height: floatingPlaceholderHeight + 'px' }"></div>
    <!-- Teleport：sticky 时将卡片传送到 body 根节点，完全绕开所有 overflow 容器 -->
    <Teleport to="body" :disabled="!(isMobile && floatingSticky)">
    <div
      class="floating-progress"
      :class="{ mobile: isMobile, 'is-sticky': isMobile && floatingSticky }"
      ref="floatingProgressRef"
    >
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
    </Teleport>

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
            <div class="select-shell" :ref="(el) => setSelectRootRef('grade', el)">
              <button
                type="button"
                class="select-trigger"
                :class="{ open: isDesktopSelectOpen('grade'), filled: Boolean(formData.grade) }"
                @click="toggleSelect('grade')"
              >
                <span class="select-trigger-copy">
                  <span class="select-trigger-label">当前选择</span>
                  <span class="select-trigger-value">{{ formData.grade || '请选择年级' }}</span>
                </span>
                <span class="select-trigger-arrow">⌄</span>
              </button>

              <transition name="select-panel">
                <div v-if="isDesktopSelectOpen('grade')" class="select-panel">
                  <button
                    type="button"
                    class="select-option select-option-clear"
                    :class="{ active: !formData.grade }"
                    @click="clearSingleSelect('grade')"
                  >
                    <span class="select-option-main">暂不填写</span>
                    <span class="select-option-meta">保留为空</span>
                  </button>
                  <button
                    v-for="grade in gradeOptions"
                    :key="grade"
                    type="button"
                    class="select-option"
                    :class="{ active: formData.grade === grade }"
                    @click="selectSingleOption('grade', grade)"
                  >
                    <span class="select-option-main">{{ grade }}</span>
                    <span class="select-option-check">{{ formData.grade === grade ? '✓' : '' }}</span>
                  </button>
                </div>
              </transition>
            </div>
          </div>

          <!-- 学院 -->
          <div class="form-item full-width">
            <label class="form-label">学院</label>
            <div class="select-shell select-shell-search" :ref="(el) => setSelectRootRef('college', el)">
              <button
                type="button"
                class="select-trigger search-trigger"
                :class="{ open: isDesktopSelectOpen('college'), filled: Boolean(formData.college) }"
                @click="toggleSelect('college')"
              >
                <span class="select-trigger-copy">
                  <span class="select-trigger-label">学院信息</span>
                  <span class="select-trigger-value">{{ formData.college || '搜索或选择学院' }}</span>
                </span>
                <span class="select-trigger-arrow">⌄</span>
              </button>

              <transition name="select-panel">
                <div v-if="isDesktopSelectOpen('college')" class="select-panel select-panel-searchable">
                  <div class="select-search-box">
                    <input
                      v-model.trim="collegeKeyword"
                      type="text"
                      placeholder="输入学院名称进行搜索"
                      class="form-input select-search-input"
                      @keydown.enter.prevent="applyCollegeKeyword"
                    />
                    <button
                      type="button"
                      class="select-search-action"
                      :disabled="!collegeKeyword.trim()"
                      @click="applyCollegeKeyword"
                    >
                      使用
                    </button>
                  </div>
                  <div class="select-section-title">推荐学院</div>
                  <div class="select-option-list compact">
                    <button
                      type="button"
                      class="select-option select-option-clear"
                      :class="{ active: !formData.college }"
                      @click="clearSingleSelect('college')"
                    >
                      <span class="select-option-main">暂不填写</span>
                      <span class="select-option-meta">后续仍可补充</span>
                    </button>
                    <button
                      v-for="college in filteredCollegeOptions"
                      :key="college"
                      type="button"
                      class="select-option"
                      :class="{ active: formData.college === college }"
                      @click="selectSingleOption('college', college)"
                    >
                      <span class="select-option-main">{{ college }}</span>
                      <span class="select-option-check">{{ formData.college === college ? '✓' : '' }}</span>
                    </button>
                  </div>
                  <div v-if="showCustomCollegeAction" class="select-custom-hint">
                    未找到完全匹配项，可直接使用“{{ collegeKeyword.trim() }}”
                  </div>
                </div>
              </transition>
            </div>
            <span class="input-hint">请输入完整学院名称</span>
          </div>

          <!-- 专业 -->
          <div class="form-item full-width">
            <label class="form-label">专业</label>
            <div class="select-shell select-shell-search" :ref="(el) => setSelectRootRef('major', el)">
              <button
                type="button"
                class="select-trigger search-trigger"
                :class="{ open: isDesktopSelectOpen('major'), filled: Boolean(formData.major) }"
                @click="toggleSelect('major')"
              >
                <span class="select-trigger-copy">
                  <span class="select-trigger-label">专业信息</span>
                  <span class="select-trigger-value">{{ formData.major || '搜索或选择专业' }}</span>
                </span>
                <span class="select-trigger-arrow">⌄</span>
              </button>

              <transition name="select-panel">
                <div v-if="isDesktopSelectOpen('major')" class="select-panel select-panel-searchable">
                  <div class="select-search-box">
                    <input
                      v-model.trim="majorKeyword"
                      type="text"
                      placeholder="输入专业名称进行搜索"
                      class="form-input select-search-input"
                      @keydown.enter.prevent="applyMajorKeyword"
                    />
                    <button
                      type="button"
                      class="select-search-action"
                      :disabled="!majorKeyword.trim()"
                      @click="applyMajorKeyword"
                    >
                      使用
                    </button>
                  </div>
                  <div class="select-section-title">常见专业</div>
                  <div class="select-option-list compact">
                    <button
                      type="button"
                      class="select-option select-option-clear"
                      :class="{ active: !formData.major }"
                      @click="clearSingleSelect('major')"
                    >
                      <span class="select-option-main">暂不填写</span>
                      <span class="select-option-meta">后续仍可补充</span>
                    </button>
                    <button
                      v-for="major in filteredMajorOptions"
                      :key="major"
                      type="button"
                      class="select-option"
                      :class="{ active: formData.major === major }"
                      @click="selectSingleOption('major', major)"
                    >
                      <span class="select-option-main">{{ major }}</span>
                      <span class="select-option-check">{{ formData.major === major ? '✓' : '' }}</span>
                    </button>
                  </div>
                  <div v-if="showCustomMajorAction" class="select-custom-hint">
                    未找到完全匹配项，可直接使用“{{ majorKeyword.trim() }}”
                  </div>
                </div>
              </transition>
            </div>
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
            <div class="select-shell" :ref="(el) => setSelectRootRef('mbti', el)">
              <button
                type="button"
                class="select-trigger"
                :class="{ open: isDesktopSelectOpen('mbti'), filled: Boolean(formData.mbti) }"
                @click="toggleSelect('mbti')"
              >
                <span class="select-trigger-copy">
                  <span class="select-trigger-label">人格偏好</span>
                  <span class="select-trigger-value">{{ formData.mbti || '请选择 MBTI 类型' }}</span>
                </span>
                <span class="select-trigger-arrow">⌄</span>
              </button>

              <transition name="select-panel">
                <div v-if="isDesktopSelectOpen('mbti')" class="select-panel select-panel-grid">
                  <button
                    type="button"
                    class="select-option select-option-clear"
                    :class="{ active: !formData.mbti }"
                    @click="clearSingleSelect('mbti')"
                  >
                    <span class="select-option-main">暂不填写</span>
                    <span class="select-option-meta">保持为空</span>
                  </button>
                  <button
                    v-for="mbti in mbtiOptions"
                    :key="mbti"
                    type="button"
                    class="select-option"
                    :class="{ active: formData.mbti === mbti }"
                    @click="selectSingleOption('mbti', mbti)"
                  >
                    <span class="select-option-main">{{ mbti }}</span>
                    <span class="select-option-check">{{ formData.mbti === mbti ? '✓' : '' }}</span>
                  </button>
                </div>
              </transition>
            </div>
          </div>

          <!-- 研究方向/兴趣课程 -->
          <div class="form-item full-width">
            <label class="form-label">研究方向 / 兴趣课程（已选 {{ formData.interests.length }}/8）</label>
            <div class="tag-section">
              <div class="tag-group">
                <span
                  v-for="tag in interestTags"
                  :key="tag"
                  class="tag"
                  :class="{ active: formData.interests.includes(tag) }"
                  @click="toggleTag('interests', tag)"
                >
                  {{ tag }}
                </span>
              </div>
              <div class="custom-tag-input">
                <input
                  v-model="customInterestInput"
                  type="text"
                  placeholder="自定义添加..."
                  class="tag-input"
                  @keyup.enter="addCustomTag('interests', customInterestInput)"
                />
                <button
                  class="add-tag-btn"
                  @click="addCustomTag('interests', customInterestInput)"
                >
                  + 添加
                </button>
              </div>
              <div class="selected-tags" v-if="formData.interests.length > 0">
                <span class="tag-label">已选择：</span>
                <span
                  v-for="tag in formData.interests"
                  :key="tag"
                  class="selected-tag"
                >
                  {{ tag }}
                  <span class="remove-tag" @click="removeTag('interests', tag)">×</span>
                </span>
              </div>
            </div>
          </div>

          <!-- 社团/组织经历 -->
          <div class="form-item full-width">
            <label class="form-label">社团 / 组织经历（已选 {{ formData.organizations.length }}/8）</label>
            <div class="tag-section">
              <div class="tag-group">
                <span
                  v-for="tag in organizationTags"
                  :key="tag"
                  class="tag"
                  :class="{ active: formData.organizations.includes(tag) }"
                  @click="toggleTag('organizations', tag)"
                >
                  {{ tag }}
                </span>
              </div>
              <div class="custom-tag-input">
                <input
                  v-model="customOrganizationInput"
                  type="text"
                  placeholder="自定义添加..."
                  class="tag-input"
                  @keyup.enter="addCustomTag('organizations', customOrganizationInput)"
                />
                <button
                  class="add-tag-btn"
                  @click="addCustomTag('organizations', customOrganizationInput)"
                >
                  + 添加
                </button>
              </div>
              <div class="selected-tags" v-if="formData.organizations.length > 0">
                <span class="tag-label">已选择：</span>
                <span
                  v-for="tag in formData.organizations"
                  :key="tag"
                  class="selected-tag"
                >
                  {{ tag }}
                  <span class="remove-tag" @click="removeTag('organizations', tag)">×</span>
                </span>
              </div>
            </div>
          </div>

          <!-- 消费偏好 -->
          <div class="form-item full-width">
            <label class="form-label">消费偏好（已选 {{ formData.consumptionPreferences.length }}/8）</label>
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
            <label class="form-label">职业意向（已选 {{ formData.careerIntention.length }}/8）</label>
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
            <label class="form-label">软硬技能（已选 {{ formData.skills.length }}/8）</label>
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

    <transition name="picker-fade">
      <div v-if="mobilePickerField" class="mobile-picker-overlay" @click.self="closeSelects">
        <div class="mobile-picker-sheet">
          <div class="mobile-picker-header">
            <div>
              <div class="mobile-picker-eyebrow">资料选择</div>
              <h3 class="mobile-picker-title">{{ mobilePickerConfig.title }}</h3>
            </div>
            <button type="button" class="mobile-picker-close" @click="closeSelects">×</button>
          </div>

          <p class="mobile-picker-desc">{{ mobilePickerConfig.description }}</p>

          <div v-if="mobilePickerField === 'college'" class="mobile-picker-search">
            <input
              v-model.trim="collegeKeyword"
              type="text"
              placeholder="输入学院名称进行搜索"
              class="form-input select-search-input"
              @keydown.enter.prevent="applyCollegeKeyword"
            />
            <button
              type="button"
              class="mobile-picker-search-btn"
              :disabled="!collegeKeyword.trim()"
              @click="applyCollegeKeyword"
            >
              使用当前输入
            </button>
          </div>

          <div v-if="mobilePickerField === 'major'" class="mobile-picker-search">
            <input
              v-model.trim="majorKeyword"
              type="text"
              placeholder="输入专业名称进行搜索"
              class="form-input select-search-input"
              @keydown.enter.prevent="applyMajorKeyword"
            />
            <button
              type="button"
              class="mobile-picker-search-btn"
              :disabled="!majorKeyword.trim()"
              @click="applyMajorKeyword"
            >
              使用当前输入
            </button>
          </div>

          <div class="mobile-picker-options" :class="{ grid: mobilePickerField === 'mbti' }">
            <button
              type="button"
              class="mobile-picker-option ghost"
              :class="{ active: !mobilePickerValue }"
              @click="clearSingleSelect(mobilePickerField)"
            >
              <span>暂不填写</span>
              <span class="select-option-check">{{ !mobilePickerValue ? '✓' : '' }}</span>
            </button>
            <button
              v-for="option in mobilePickerOptions"
              :key="option"
              type="button"
              class="mobile-picker-option"
              :class="{ active: mobilePickerValue === option }"
              @click="selectSingleOption(mobilePickerField, option)"
            >
              <span>{{ option }}</span>
              <span class="select-option-check">{{ mobilePickerValue === option ? '✓' : '' }}</span>
            </button>
          </div>

          <div v-if="mobilePickerField === 'college' && showCustomCollegeAction" class="mobile-picker-tip">
            也可以直接保存“{{ collegeKeyword.trim() }}”作为学院名称。
          </div>

          <div v-if="mobilePickerField === 'major' && showCustomMajorAction" class="mobile-picker-tip">
            也可以直接保存“{{ majorKeyword.trim() }}”作为专业名称。
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, unref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { handleTokenExpired } from '@/utils/authHelper'
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

// 移动端完成度卡片悬浮相关
// 使用 IntersectionObserver + Teleport，彻底绕开 overflow-x:hidden 的限制
const floatingProgressRef = ref(null)
const floatingSentinelRef = ref(null)
const floatingSticky = ref(false)
const floatingPlaceholderHeight = ref(0)
const activeDesktopSelect = ref('')
const mobilePickerField = ref('')
const collegeKeyword = ref('')
const majorKeyword = ref('')
let stickyObserver = null
const selectRootRefs = {}

const handleResize = () => {
  isMobile.value = window.innerWidth <= 768
  closeSelects()
  if (!isMobile.value) {
    floatingSticky.value = false
  } else {
    initStickyObserver()
  }
}

const setSelectRootRef = (field, el) => {
  if (el) {
    selectRootRefs[field] = el
    return
  }

  delete selectRootRefs[field]
}

const isDesktopSelectOpen = (field) => !isMobile.value && activeDesktopSelect.value === field

const syncCollegeKeyword = () => {
  collegeKeyword.value = formData.value.college || ''
}

const syncMajorKeyword = () => {
  majorKeyword.value = formData.value.major || ''
}

const toggleSelect = (field) => {
  if (field === 'college') {
    syncCollegeKeyword()
  }

  if (field === 'major') {
    syncMajorKeyword()
  }

  if (isMobile.value) {
    mobilePickerField.value = mobilePickerField.value === field ? '' : field
    activeDesktopSelect.value = ''
    return
  }

  activeDesktopSelect.value = activeDesktopSelect.value === field ? '' : field
  mobilePickerField.value = ''
}

const closeSelects = () => {
  activeDesktopSelect.value = ''
  mobilePickerField.value = ''
}

const selectSingleOption = (field, value) => {
  formData.value[field] = value
  if (field === 'college') {
    collegeKeyword.value = value
  }
  if (field === 'major') {
    majorKeyword.value = value
  }
  closeSelects()
}

const clearSingleSelect = (field) => {
  formData.value[field] = ''
  if (field === 'college') {
    collegeKeyword.value = ''
  }
  if (field === 'major') {
    majorKeyword.value = ''
  }
  closeSelects()
}

const filteredCollegeOptions = computed(() => {
  const keyword = collegeKeyword.value.trim().toLowerCase()
  if (!keyword) {
    return collegeSuggestions
  }

  return collegeSuggestions.filter((college) => college.toLowerCase().includes(keyword))
})

const filteredMajorOptions = computed(() => {
  const keyword = majorKeyword.value.trim().toLowerCase()
  if (!keyword) {
    return majorSuggestions
  }

  return majorSuggestions.filter((major) => major.toLowerCase().includes(keyword))
})

const showCustomCollegeAction = computed(() => {
  const keyword = collegeKeyword.value.trim()
  return Boolean(keyword) && !filteredCollegeOptions.value.includes(keyword)
})

const showCustomMajorAction = computed(() => {
  const keyword = majorKeyword.value.trim()
  return Boolean(keyword) && !filteredMajorOptions.value.includes(keyword)
})

const applyCollegeKeyword = () => {
  const keyword = collegeKeyword.value.trim()
  if (!keyword) {
    return
  }

  selectSingleOption('college', keyword)
}

const applyMajorKeyword = () => {
  const keyword = majorKeyword.value.trim()
  if (!keyword) {
    return
  }

  selectSingleOption('major', keyword)
}

const mobilePickerConfig = computed(() => {
  if (mobilePickerField.value === 'grade') {
    return {
      title: '选择年级',
      description: '用更接近卡片风格的方式选择当前年级，手机端会以底部面板呈现。'
    }
  }

  if (mobilePickerField.value === 'mbti') {
    return {
      title: '选择 MBTI',
      description: '选择你的 MBTI 类型，也可以先留空，后续再补充。'
    }
  }

  if (mobilePickerField.value === 'college') {
    return {
      title: '选择学院',
      description: '可直接搜索推荐项，也可以保存你手动输入的学院名称。'
    }
  }

  if (mobilePickerField.value === 'major') {
    return {
      title: '选择专业',
      description: '可搜索常见专业，也可以直接保存你输入的完整专业名称。'
    }
  }

  return {
    title: '',
    description: ''
  }
})

const mobilePickerOptions = computed(() => {
  if (mobilePickerField.value === 'grade') {
    return gradeOptions
  }

  if (mobilePickerField.value === 'mbti') {
    return mbtiOptions
  }

  if (mobilePickerField.value === 'college') {
    return filteredCollegeOptions.value
  }

  if (mobilePickerField.value === 'major') {
    return filteredMajorOptions.value
  }

  return []
})

const mobilePickerValue = computed(() => {
  if (!mobilePickerField.value) {
    return ''
  }

  return formData.value[mobilePickerField.value] || ''
})

const handleOutsideSelectClick = (event) => {
  const field = activeDesktopSelect.value
  if (!field) {
    return
  }

  const root = selectRootRefs[field]
  if (root && !root.contains(event.target)) {
    activeDesktopSelect.value = ''
  }
}

const handleEscClose = (event) => {
  if (event.key === 'Escape') {
    closeSelects()
  }
}

function initStickyObserver() {
  nextTick(() => {
    if (!floatingSentinelRef.value || !isMobile.value) return
    floatingPlaceholderHeight.value = (floatingProgressRef.value?.offsetHeight ?? 100) + 8
    stickyObserver?.disconnect()
    stickyObserver = new IntersectionObserver((entries) => {
      floatingSticky.value = !entries[0].isIntersecting
    }, { threshold: 0 })
    stickyObserver.observe(floatingSentinelRef.value)
  })
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

const collegeSuggestions = Array.from(new Set([
  '计算机学院',
  '软件学院',
  '人工智能学院',
  '数据科学与大数据学院',
  '信息工程学院',
  '电子信息学院',
  '通信工程学院',
  '自动化学院',
  '电气工程学院',
  '机械工程学院',
  '材料科学与工程学院',
  '环境科学与工程学院',
  '土木工程学院',
  '建筑学院',
  '化学化工学院',
  '生命科学学院',
  '生物医学工程学院',
  '医学院',
  '药学院',
  '公共卫生学院',
  '数学与统计学院',
  '物理学院',
  '天文与空间科学学院',
  '地理科学学院',
  '海洋学院',
  '资源与环境学院',
  '经济学院',
  '经济管理学院',
  '管理学院',
  '商学院',
  '工商管理学院',
  '金融学院',
  '法学院',
  '马克思主义学院',
  '新闻与传播学院',
  '文学与新闻传播学院',
  '外文学院',
  '人文学院',
  '哲学学院',
  '历史学院',
  '教育学院',
  '心理学院',
  '社会学院',
  '国际关系学院',
  '艺术学院',
  '艺术设计学院',
  '音乐学院',
  '体育学院',
  '农业与生物学院',
  '园艺学院',
  '食品科学与工程学院',
  '旅游学院',
  '公共管理学院',
  '网络空间安全学院',
  '信息学院',
  '电影学院',
  '国际中文教育学院',
  '航空航天学院',
  '海洋与地球学院',
  '物理学院',
  '计算机科学学院',
  '数学学院',
  '化学学院',
  '生命科学学院',
  '经济管理学院',
  '人文学院',
  '外国语学院'
]))

const majorSuggestions = Array.from(new Set([
  '计算机科学与技术',
  '软件工程',
  '网络工程',
  '信息安全',
  '人工智能',
  '数据科学与大数据技术',
  '电子信息工程',
  '通信工程',
  '自动化',
  '电气工程及其自动化',
  '机械设计制造及其自动化',
  '智能制造工程',
  '材料科学与工程',
  '新能源材料与器件',
  '土木工程',
  '建筑学',
  '环境工程',
  '化学工程与工艺',
  '应用化学',
  '生物工程',
  '生物科学',
  '临床医学',
  '口腔医学',
  '药学',
  '护理学',
  '预防医学',
  '数学与应用数学',
  '统计学',
  '信息与计算科学',
  '应用物理学',
  '物理学',
  '天文学',
  '地理信息科学',
  '海洋科学',
  '经济学',
  '国际经济与贸易',
  '金融学',
  '财政学',
  '工商管理',
  '市场营销',
  '会计学',
  '财务管理',
  '人力资源管理',
  '电子商务',
  '法学',
  '知识产权',
  '社会学',
  '社会工作',
  '心理学',
  '应用心理学',
  '教育学',
  '学前教育',
  '汉语言文学',
  '新闻学',
  '传播学',
  '广告学',
  '英语',
  '日语',
  '翻译',
  '历史学',
  '哲学',
  '行政管理',
  '公共事业管理',
  '国际政治',
  '数字媒体技术',
  '数字媒体艺术',
  '视觉传达设计',
  '环境设计',
  '产品设计',
  '音乐表演',
  '体育教育',
  '食品科学与工程',
  '园林',
  '农学',
  '旅游管理'
]))

const consumptionTags = ['数码', '美妆', '奶茶', '户外', '运动', '阅读', '游戏', '音乐', '影视', '美食']
const careerTags = ['考公', '大厂', '学术', '创业', '出国', '考研', '自由职业']
const skillTags = ['Python', 'Java', 'C++', '视频剪辑', '英语口译', 'PS', 'Excel', '写作', '演讲', '摄影']

// 新增预置标签
const interestTags = ['人工智能', '机器学习', '数据分析', '心理学', '经济学', '法学', '文学', '艺术设计', '新媒体', '外语学习']
const organizationTags = ['校学生会', '院学生会', '社团联合会', '志愿者协会', '辩论队', '摄影社', '音乐社', '篮球队', '足球队', '创业团队']

// 自定义标签输入
const customConsumptionInput = ref('')
const customCareerInput = ref('')
const customSkillInput = ref('')
const customInterestInput = ref('')
const customOrganizationInput = ref('')

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
  
  // 数组字段（数组有元素即算填写）
  if (formData.value.interests && formData.value.interests.length > 0) filledCount++
  if (formData.value.organizations && formData.value.organizations.length > 0) filledCount++
  if (formData.value.consumptionPreferences && formData.value.consumptionPreferences.length > 0) filledCount++
  if (formData.value.careerIntention && formData.value.careerIntention.length > 0) filledCount++
  if (formData.value.skills && formData.value.skills.length > 0) filledCount++
  
  const totalFields = 11
  return Math.floor((filledCount / totalFields) * 100)
})

const floatingCircumference = 2 * Math.PI * 34
const floatingOffset = computed(() => floatingCircumference - (completionRate.value / 100) * floatingCircumference)
const MAX_TAGS_PER_TYPE = 8

const showTagLimitToast = () => {
  toastMessage.value = `每类标签最多选择 ${MAX_TAGS_PER_TYPE} 个`
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 2000)
}

// 切换标签选择
const toggleTag = (fieldName, tag) => {
  if (!Array.isArray(formData.value[fieldName])) {
    formData.value[fieldName] = []
  }

  const index = formData.value[fieldName].indexOf(tag)
  if (index > -1) {
    formData.value[fieldName].splice(index, 1)
  } else {
    if (formData.value[fieldName].length >= MAX_TAGS_PER_TYPE) {
      showTagLimitToast()
      return
    }
    formData.value[fieldName].push(tag)
  }
}

// 添加自定义标签
const addCustomTag = (fieldName, inputValue) => {
  const rawValue = unref(inputValue)
  const value = String(rawValue || '').trim()

  if (!Array.isArray(formData.value[fieldName])) {
    formData.value[fieldName] = []
  }

  if (!value) {
    return
  }

  if (value.length > 64) {
    toastMessage.value = '自定义标签最多 64 个字符'
    showToast.value = true
    setTimeout(() => {
      showToast.value = false
    }, 2000)
    return
  }

  if (!formData.value[fieldName].includes(value)) {
    if (formData.value[fieldName].length >= MAX_TAGS_PER_TYPE) {
      showTagLimitToast()
      return
    }
    formData.value[fieldName].push(value)
    if (fieldName === 'interests') customInterestInput.value = ''
    if (fieldName === 'organizations') customOrganizationInput.value = ''
    if (fieldName === 'consumptionPreferences') customConsumptionInput.value = ''
    if (fieldName === 'careerIntention') customCareerInput.value = ''
    if (fieldName === 'skills') customSkillInput.value = ''
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
    
    // 调用API（PATCH 更新）
    await updateUserProfile(payload)
    localStorage.setItem('sixth_element_profile_completion', String(completionRate.value))
    toastMessage.value = '信息已保存，正在返回...'
    showToast.value = true
    
    setTimeout(() => {
      showToast.value = false
      router.push('/profile')
    }, 1500)
  } catch (error) {
    console.error('保存失败:', error)
    
    // 检查是否是登录过期
    if (error.message.includes('登录已过期')) {
      handleTokenExpired(router)
      return
    }
    
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
    
    // 检查是否是登录过期
    if (error.message.includes('登录已过期')) {
      handleTokenExpired(router)
      return
    }
    
    // 其他认证错误，跳转到登录页
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
  document.addEventListener('mousedown', handleOutsideSelectClick)
  document.addEventListener('keydown', handleEscClose)
  if (isMobile.value) initStickyObserver()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  document.removeEventListener('mousedown', handleOutsideSelectClick)
  document.removeEventListener('keydown', handleEscClose)
  stickyObserver?.disconnect()
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

.select-shell {
  position: relative;
}

.select-trigger {
  width: 100%;
  min-height: 64px;
  padding: 14px 16px;
  border: 2px solid #dbe7f5;
  border-radius: 14px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  text-align: left;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: 0 6px 14px rgba(19, 85, 151, 0.06);
}

.select-trigger:hover {
  border-color: #90caf9;
  transform: translateY(-1px);
  box-shadow: 0 10px 22px rgba(33, 150, 243, 0.12);
}

.select-trigger.open,
.select-trigger:focus-visible {
  outline: none;
  border-color: #2196f3;
  box-shadow: 0 0 0 4px rgba(33, 150, 243, 0.12);
}

.select-trigger.filled {
  background: linear-gradient(135deg, #eef6ff 0%, #ffffff 100%);
}

.select-trigger-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.select-trigger-label {
  font-size: 12px;
  font-weight: 700;
  color: #6a86a8;
  letter-spacing: 0.02em;
}

.select-trigger-value {
  font-size: 15px;
  font-weight: 600;
  color: #183b63;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.select-trigger-arrow {
  flex-shrink: 0;
  font-size: 18px;
  color: #4a89c7;
  transition: transform 0.25s ease;
}

.select-trigger.open .select-trigger-arrow {
  transform: rotate(180deg);
}

.search-trigger {
  min-height: 70px;
}

.select-panel {
  position: absolute;
  top: calc(100% + 10px);
  left: 0;
  right: 0;
  z-index: 25;
  padding: 12px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid #d9e8f7;
  box-shadow: 0 18px 40px rgba(15, 61, 112, 0.18);
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: min(360px, 60vh);
  overflow-y: auto;
}

.select-panel-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.select-panel-searchable {
  gap: 12px;
}

.select-option-list.compact {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.select-option {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid #d9e7f5;
  border-radius: 12px;
  background: #f8fbff;
  color: #183b63;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.select-option:hover {
  border-color: #90caf9;
  background: #eef6ff;
}

.select-option.active {
  border-color: #2196f3;
  background: linear-gradient(135deg, #2196f3 0%, #42a5f5 100%);
  color: #ffffff;
  box-shadow: 0 10px 20px rgba(33, 150, 243, 0.2);
}

.select-option-main {
  font-size: 14px;
  font-weight: 600;
}

.select-option-meta {
  font-size: 12px;
  color: #6b7a90;
}

.select-option.active .select-option-meta {
  color: rgba(255, 255, 255, 0.82);
}

.select-option-check {
  min-width: 16px;
  text-align: right;
  font-size: 14px;
  font-weight: 700;
}

.select-option-clear {
  border-style: dashed;
}

.select-search-box {
  display: flex;
  gap: 10px;
  align-items: center;
}

.select-search-input {
  flex: 1;
  margin: 0;
}

.select-search-action,
.mobile-picker-search-btn {
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #42a5f5, #2196f3);
  color: #fff;
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.select-search-action:disabled,
.mobile-picker-search-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.select-search-action:not(:disabled):hover,
.mobile-picker-search-btn:not(:disabled):hover {
  transform: translateY(-1px);
}

.select-section-title {
  font-size: 12px;
  font-weight: 700;
  color: #6a86a8;
  letter-spacing: 0.04em;
}

.select-custom-hint,
.mobile-picker-tip {
  font-size: 12px;
  color: #5d7698;
  background: #f5f9ff;
  border-radius: 12px;
  padding: 10px 12px;
  border: 1px dashed #c6dcf5;
}

.select-panel-enter-active,
.select-panel-leave-active {
  transition: all 0.2s ease;
}

.select-panel-enter-from,
.select-panel-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.mobile-picker-overlay {
  position: fixed;
  inset: 0;
  z-index: 1200;
  background: rgba(15, 30, 55, 0.44);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 16px 12px calc(16px + env(safe-area-inset-bottom));
}

.mobile-picker-sheet {
  width: min(100%, 560px);
  max-height: 82vh;
  border-radius: 24px 24px 18px 18px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  padding: 18px 16px 16px;
  box-shadow: 0 -12px 36px rgba(15, 61, 112, 0.24);
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.mobile-picker-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.mobile-picker-eyebrow {
  font-size: 12px;
  font-weight: 700;
  color: #6a86a8;
}

.mobile-picker-title {
  margin: 4px 0 0;
  font-size: 20px;
  color: #163962;
}

.mobile-picker-close {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: #eef6ff;
  color: #3d6f9f;
  font-size: 22px;
  cursor: pointer;
}

.mobile-picker-desc {
  margin: 0;
  color: #5d7698;
  font-size: 13px;
  line-height: 1.5;
}

.mobile-picker-search {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.mobile-picker-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  padding-right: 2px;
}

.mobile-picker-options.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.mobile-picker-option {
  width: 100%;
  padding: 14px 16px;
  border: 1px solid #d7e6f6;
  border-radius: 14px;
  background: #ffffff;
  color: #183b63;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-size: 15px;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
}

.mobile-picker-option.active {
  background: linear-gradient(135deg, #2196f3, #42a5f5);
  color: #ffffff;
  border-color: #2196f3;
}

.mobile-picker-option.ghost {
  background: #f6faff;
  border-style: dashed;
}

.picker-fade-enter-active,
.picker-fade-leave-active {
  transition: opacity 0.2s ease;
}

.picker-fade-enter-from,
.picker-fade-leave-to {
  opacity: 0;
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
  /* 移动端：在文档流中展示，由 IntersectionObserver 决定何时 Teleport 到 body */
  position: relative;
  right: unset;
  bottom: unset;
  width: 100%;
  box-sizing: border-box;
  margin-bottom: 16px;
  border-radius: 12px;
}

/* sticky 激活时已被 Teleport 到 body，position:fixed 不受任何 overflow 约束 */
.floating-progress.mobile.is-sticky {
  position: fixed;
  top: 60px;
  right: auto;
  left: 12px;
  width: 260px;
  margin-bottom: 0;
  z-index: 999;
  animation: floatIn 0.18s ease;
}

@keyframes floatIn {
  from { opacity: 0.75; transform: translateY(-6px); }
  to   { opacity: 1;    transform: translateY(0); }
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
  .form-select,
  .select-trigger,
  .mobile-picker-option {
    font-size: 16px; /* 防止 iOS 自动缩放 */
  }

  .select-panel {
    display: none;
  }

  .select-search-box {
    flex-direction: column;
    align-items: stretch;
  }

  .search-trigger {
    min-height: 74px;
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

  .mobile-picker-sheet {
    border-radius: 22px 22px 16px 16px;
    padding: 16px 14px 14px;
  }

  .mobile-picker-options.grid {
    grid-template-columns: 1fr 1fr;
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

  .mobile-picker-options.grid {
    grid-template-columns: 1fr;
  }
}
</style>
