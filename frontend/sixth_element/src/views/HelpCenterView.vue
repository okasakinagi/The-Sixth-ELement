<template>
  <div class="help-center">
    <!-- 遮罩层 -->
    <div v-if="mobileSidebarOpen" class="sidebar-overlay" @click="toggleSidebar"></div>

    <div class="help-shell">
      <!-- 移动端菜单按钮 -->
      <button 
        v-if="isMobile"
        class="mobile-toggle-btn"
        @click="toggleSidebar"
        :title="mobileSidebarOpen ? '关闭菜单' : '打开菜单'"
        :class="{ 'open': mobileSidebarOpen }"
      >
        ▼
      </button>

      <!-- 左侧导航 -->
      <aside 
        class="help-sidebar"
        :class="{ 
          'mobile-open': mobileSidebarOpen 
        }"
      >

      <div class="sidebar-header">
        <h2>帮助中心</h2>
        <p class="sidebar-subtitle">Help Center</p>
        <div class="search-container">
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="搜索帮助内容..."
            class="search-input"
            @input="handleSearch"
          />
          <span class="search-icon">🔍</span>
          <!-- 搜索结果 -->
          <div v-if="showSearchResults && searchQuery.trim()" class="search-results">
            <div v-if="searchResults.length > 0">
              <div 
                v-for="result in searchResults" 
                :key="result.id"
                class="search-result-item"
                @click="selectSearchResult(result)"
              >
                <span class="result-category">{{ result.category }}</span>
                <span class="result-title">{{ result.title }}</span>
              </div>
            </div>
            <div v-else class="search-no-results">
              暂无相关帮助内容
            </div>
          </div>
        </div>
      </div>

      <nav class="help-menu">
        <div 
          v-for="category in displayCategories" 
          :key="category.id"
          class="menu-category"
        >
          <h3 class="category-title" @click="toggleCategory(category.id)">
            <span class="category-icon">{{ category.icon }}</span>
            {{ category.title }}
            <span class="toggle-icon" :class="{ 'expanded': expandedCategories.includes(category.id) }">
              ▶
            </span>
          </h3>
          <ul 
            class="category-items"
            :class="{ 'expanded': expandedCategories.includes(category.id) }"
          >
            <li 
              v-for="item in category.items" 
              :key="item.id"
              class="menu-item"
              :class="{ 'active': activeItemId === item.id }"
              @click="selectItem(item.id)"
            >
              {{ item.title }}
            </li>
          </ul>
        </div>
      </nav>
    </aside>

    <!-- 右侧内容 -->
    <main 
      class="help-content"
    >
      <!-- 顶部导航 -->
      <div class="top-nav">
        <a href="/task-hall" class="app-logo">第六元素</a>
      </div>
      <!-- 面包屑导航 -->
      <div class="breadcrumb">
        <span>帮助中心</span>
        <span v-if="activeCategory"> &gt; {{ activeCategory.title }}</span>
        <span v-if="activeItem"> &gt; {{ activeItem.title }}</span>
      </div>

      <!-- 文章详情 -->
      <div class="article">
        <h1 class="article-title">{{ activeItem ? activeItem.title : '选择一个帮助主题' }}</h1>
        
        <div v-if="activeItem" class="article-content">
          <div v-html="activeItem.content"></div>
        </div>
        
        <div v-else class="empty-state">
          <p>请从左侧选择一个帮助主题，或使用搜索功能查找相关内容。</p>
        </div>

        <!-- 有用反馈 -->
        <div v-if="activeItem" class="feedback-section">
          <p>这对您有帮助吗？</p>
          <div class="feedback-buttons">
            <button 
              class="feedback-btn helpful"
              :class="{ 'disabled': isFeedbackDisabled(activeItemId) }"
              :disabled="isFeedbackDisabled(activeItemId)"
              @click="submitFeedback(true)"
            >
              👍 有帮助
            </button>
            <button 
              class="feedback-btn not-helpful"
              :class="{ 'disabled': isFeedbackDisabled(activeItemId) }"
              :disabled="isFeedbackDisabled(activeItemId)"
              @click="submitFeedback(false)"
            >
              👎 没帮助
            </button>
          </div>
          <p v-if="isFeedbackDisabled(activeItemId)" class="feedback-submitted-hint">
            ✓ 已提交反馈
          </p>
        </div>

        <!-- 相关推荐 -->
        <div v-if="activeItem && relatedItems.length > 0" class="related-section">
          <h3>相关推荐</h3>
          <ul class="related-list">
            <li 
              v-for="item in relatedItems" 
              :key="item.id"
              class="related-item"
              @click="selectItem(item.id)"
            >
              {{ item.title }}
            </li>
          </ul>
        </div>
      </div>
    </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

// 状态管理
const searchQuery = ref('')
const expandedCategories = ref(['faq']) // 默认展开常见问题
const activeItemId = ref('')
const activeCategoryId = ref('')
const showSearchResults = ref(false)
const searchResults = ref([])
const mobileSidebarOpen = ref(false) // 控制移动端侧边栏的打开/关闭状态
const isMobile = ref(window.innerWidth <= 768) // 检测是否为移动端

// 反馈状态管理（localStorage存储，一周过期）
const FEEDBACK_STORAGE_KEY = 'help_center_feedback'
const FEEDBACK_EXPIRY_DAYS = 7

// 响应式反馈记录（用于立即更新UI）
const feedbackRecords = ref({})

// 获取已提交反馈的记录
const getFeedbackRecords = () => {
  try {
    const data = localStorage.getItem(FEEDBACK_STORAGE_KEY)
    if (!data) return {}
    const records = JSON.parse(data)
    const now = Date.now()
    // 清理过期记录
    Object.keys(records).forEach(key => {
      if (now - records[key].timestamp > FEEDBACK_EXPIRY_DAYS * 24 * 60 * 60 * 1000) {
        delete records[key]
      }
    })
    localStorage.setItem(FEEDBACK_STORAGE_KEY, JSON.stringify(records))
    return records
  } catch {
    return {}
  }
}

// 初始化响应式反馈记录
const initFeedbackRecords = () => {
  feedbackRecords.value = getFeedbackRecords()
}

// 检查某条目是否已提交反馈
const isFeedbackDisabled = (itemId) => {
  return !!feedbackRecords.value[itemId]
}

// 保存反馈记录
const saveFeedbackRecord = (itemId, isHelpful) => {
  const records = getFeedbackRecords()
  records[itemId] = { isHelpful, timestamp: Date.now() }
  localStorage.setItem(FEEDBACK_STORAGE_KEY, JSON.stringify(records))
  // 立即更新响应式状态
  feedbackRecords.value = { ...records }
}

// 拖拽相关
const menuRef = ref(null)
const menuPosition = ref({ x: 0, y: 0 })
const dragState = ref({ isDragging: false, startX: 0, startY: 0, initialX: 0, initialY: 0 })

function startDrag(e) {
  const clientX = e.type.includes('touch') ? e.touches[0]?.clientX : e.clientX
  const clientY = e.type.includes('touch') ? e.touches[0]?.clientY : e.clientY

  if (!clientX || !clientY) return

  dragState.value = {
    isDragging: true,
    startX: clientX,
    startY: clientY,
    initialX: menuPosition.value.x,
    initialY: menuPosition.value.y
  }

  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  document.addEventListener('touchmove', onDrag)
  document.addEventListener('touchend', stopDrag)
}

function onDrag(e) {
  if (!dragState.value.isDragging) return
  
  const clientX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX
  const clientY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY

  const deltaX = clientX - dragState.value.startX
  const deltaY = clientY - dragState.value.startY

  menuPosition.value = {
    x: dragState.value.initialX + deltaX,
    y: dragState.value.initialY + deltaY
  }
}

function stopDrag() {
  dragState.value.isDragging = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', stopDrag)
}

// 监听窗口大小变化
function handleResize() {
  isMobile.value = window.innerWidth <= 768
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})

// 从路由参数中获取初始分类
const initialCategory = ref(route.query.category || 'faq')
const initialItem = ref(route.query.item || '')

// 保存来源路径
const referrer = ref(localStorage.getItem('help_center_referrer') || '/task-hall')

// 帮助中心数据
const categories = ref([
  {
    id: 'faq',
    title: '常见问题',
    icon: '•',
    items: [
      {
        id: 'faq-1',
        title: '如何注册账号？',
        content: `
          <p>注册账号非常简单，只需按照以下步骤操作：</p>
          <ol>
            <li>点击页面右上角的"注册"按钮</li>
            <li>填写邮箱、密码和昵称</li>
            <li>点击"Register"按钮完成注册</li>
            <li>注册成功后，系统会自动登录</li>
          </ol>
          <p>注册时请确保使用有效的邮箱地址，以便接收重要通知。</p>
        `
      },
      {
        id: 'faq-2',
        title: '忘记密码怎么办？',
        content: `
          <p>如果您忘记了密码，可以通过以下步骤重置：</p>
          <ol>
            <li>在登录页面点击"忘记密码"链接</li>
            <li>输入您的注册邮箱</li>
            <li>系统会发送重置密码的链接到您的邮箱</li>
            <li>点击链接设置新密码</li>
          </ol>
          <p>如果您没有收到邮件，请检查垃圾邮件文件夹。</p>
        `
      },
      {
        id: 'faq-3',
        title: '如何联系客服？',
        content: `
          <p>您可以通过以下方式联系我们的客服团队：</p>
          <ul>
            <li>邮箱：support6@surveyfiller.com</li>
            <li>工作时间：周一至周五 9:00-18:00</li>
          </ul>
          <p>我们会在24小时内回复您的咨询。</p>
        `
      }
    ]
  },
  {
    id: 'points',
    title: '关于积分',
    icon: '•',
    items: [
      {
        id: 'points-1',
        title: '如何获取积分？',
        content: `
          <p>您可以通过以下方式获取积分：</p>
          <ul>
            <li>填写问卷：根据问卷长度和复杂度获得相应积分</li>
            <li>邀请好友：成功邀请好友注册并完成首份问卷</li>
            <li>每日签到：连续签到可获得额外奖励</li>
            <li>参与活动：定期参与平台举办的活动</li>
          </ul>
          <p>积分会在问卷审核通过后自动发放到您的账户。</p>
        `
      },
      {
        id: 'points-2',
        title: '如何消耗积分？',
        content: `
          <p>您可以使用积分兑换以下服务：</p>
          <ul>
            <li>问卷加速审核：使用积分优先审核您的问卷</li>
            <li>高级分析报告：兑换更详细的问卷分析报告</li>
            <li>平台周边：兑换平台定制的周边产品</li>
          </ul>
          <p>积分兑换功能会不断更新，敬请期待！</p>
        `
      },
      {
        id: 'points-3',
        title: '积分结算规则',
        content: `
          <p>积分结算规则如下：</p>
          <ul>
            <li>问卷填答积分：问卷审核通过后1-3个工作日内发放</li>
            <li>邀请好友积分：好友完成首份问卷后立即发放</li>
            <li>每日签到积分：签到成功后立即发放</li>
            <li>活动积分：活动结束后3-5个工作日内发放</li>
          </ul>
          <p>如有特殊情况，积分发放可能会有所延迟，请耐心等待。</p>
        `
      }
    ]
  },
  {
    id: 'survey-publish',
    title: '问卷发布',
    icon: '•',
    items: [
      {
        id: 'publish-1',
        title: '审核规范',
        content: `
          <p>问卷审核规范如下：</p>
          <ul>
            <li>内容合规：问卷内容不得违反法律法规和公序良俗</li>
            <li>主题明确：问卷主题应清晰明确，避免模糊不清</li>
            <li>问题合理：问题设置应合理，避免引导性和敏感性问题</li>
            <li>长度适中：问卷长度应适中，一般不超过20分钟填答时间</li>
          </ul>
          <p>审核时间一般为1-2个工作日，请耐心等待。</p>
        `
      },
      {
        id: 'publish-2',
        title: '如何使用 AI 辅助',
        content: `
          <p>使用 AI 辅助创建问卷的步骤：</p>
          <ol>
            <li>进入问卷创建页面</li>
            <li>点击"AI 辅助创建"按钮</li>
            <li>输入问卷主题和相关要求</li>
            <li>点击"生成问卷"按钮</li>
            <li>系统会自动生成问卷初稿，您可以在此基础上进行修改</li>
          </ol>
          <p>AI 生成的问卷可能需要人工调整，以确保内容符合您的需求。</p>
        `
      },
      {
        id: 'publish-3',
        title: '暂停与删除逻辑',
        content: `
          <p>问卷的暂停与删除逻辑如下：</p>
          <h4>暂停问卷：</h4>
          <ul>
            <li>暂停后，问卷将不再接受新的填答</li>
            <li>已收集的问卷数据不会丢失</li>
            <li>您可以随时恢复问卷</li>
          </ul>
          <h4>删除问卷：</h4>
          <ul>
            <li>删除后，问卷将无法恢复</li>
            <li>已收集的问卷数据也会被删除</li>
            <li>删除操作需要二次确认</li>
          </ul>
          <p>请谨慎操作删除功能，建议在删除前导出问卷数据。</p>
        `
      }
    ]
  },
  {
    id: 'survey-fill',
    title: '问卷填写',
    icon: '•',
    items: [
      {
        id: 'fill-1',
        title: '填答限制',
        content: `
          <p>问卷填答限制如下：</p>
          <ul>
            <li>同一问卷：每个用户只能填写一次</li>
            <li>每日上限：每个用户每天最多填写10份问卷</li>
            <li>质量要求：填答内容应真实有效，避免随意填写</li>
            <li>时间限制：部分问卷可能设置填答时间限制</li>
          </ul>
          <p>违反填答规则可能会导致账号被暂停使用。</p>
        `
      },
      {
        id: 'fill-2',
        title: '匹配度算法简单科普',
        content: `
          <p>匹配度算法是根据以下因素计算的：</p>
          <ul>
            <li>用户画像：根据您的个人信息和历史填答记录</li>
            <li>问卷要求：问卷发布者设置的目标人群条件</li>
            <li>填答质量：您历史填答的质量和认真程度</li>
            <li>活跃度：您在平台的活跃程度</li>
          </ul>
          <p>匹配度越高，您看到的问卷越符合您的背景和兴趣。</p>
        `
      }
    ]
  },
  {
    id: 'account-security',
    title: '账号安全',
    icon: '•',
    items: [
      {
        id: 'security-1',
        title: '修改个人信息',
        content: `
          <p>修改个人信息的步骤：</p>
          <ol>
            <li>登录账号</li>
            <li>进入"个人资料"页面</li>
            <li>点击"编辑资料"按钮</li>
            <li>修改您需要更新的信息</li>
            <li>点击"保存"按钮完成修改</li>
          </ol>
          <p>部分敏感信息可能需要验证身份后才能修改。</p>
        `
      },
      {
        id: 'security-2',
        title: '账号绑定',
        content: `
          <p>账号绑定功能正在开发中，敬请期待！</p>
          <p>未来我们将支持绑定手机号、微信等第三方账号，提高账号安全性。</p>
        `
      },
      {
        id: 'security-3',
        title: '隐私政策',
        content: `
          <p>我们非常重视您的隐私保护：</p>
          <ul>
            <li>数据收集：我们只会收集必要的个人信息</li>
            <li>数据使用：您的个人信息仅用于提供服务和改进产品</li>
            <li>数据共享：我们不会向第三方分享您的个人信息</li>
            <li>数据安全：我们采取多种安全措施保护您的数据</li>
          </ul>
          <p>详细的隐私政策请查看平台的《隐私协议》。</p>
        `
      }
    ]
  }
])

// 计算属性
const activeCategory = computed(() => {
  if (!activeItemId.value) return null
  
  for (const category of categories.value) {
    for (const item of category.items) {
      if (item.id === activeItemId.value) {
        return category
      }
    }
  }
  return null
})

const activeItem = computed(() => {
  if (!activeItemId.value) return null
  
  for (const category of categories.value) {
    for (const item of category.items) {
      if (item.id === activeItemId.value) {
        return item
      }
    }
  }
  return null
})

const relatedItems = computed(() => {
  if (!activeItem.value || !activeCategory.value) return []
  
  return activeCategory.value.items
    .filter(item => item.id !== activeItem.value.id)
    .slice(0, 3)
})

const displayCategories = computed(() => {
  if (searchQuery.value.trim() && showSearchResults.value) {
    // 如果有搜索查询且显示搜索结果，不显示分类列表
    return []
  }
  return categories.value
})

// 方法
const toggleCategory = (categoryId) => {
  if (expandedCategories.value.includes(categoryId)) {
    expandedCategories.value = expandedCategories.value.filter(id => id !== categoryId)
  } else {
    expandedCategories.value.push(categoryId)
  }
}

const selectItem = (itemId) => {
  activeItemId.value = itemId
  showSearchResults.value = false
  searchQuery.value = ''
  
  // 在移动端选择后自动关闭侧边栏
  if (isMobile.value) {
    mobileSidebarOpen.value = false
  }
  
  // 确保对应分类展开
  for (const category of categories.value) {
    for (const item of category.items) {
      if (item.id === itemId && !expandedCategories.value.includes(category.id)) {
        expandedCategories.value.push(category.id)
        break
      }
    }
  }
}

const handleSearch = () => {
  const query = searchQuery.value.trim().toLowerCase()
  
  if (query) {
    showSearchResults.value = true
    searchResults.value = []
    
    // 搜索所有分类和条目
    for (const category of categories.value) {
      for (const item of category.items) {
        // 搜索标题和内容
        if (item.title.toLowerCase().includes(query) || 
            item.content.toLowerCase().includes(query)) {
          searchResults.value.push({
            id: item.id,
            title: item.title,
            category: category.title,
            categoryId: category.id
          })
        }
      }
    }
  } else {
    showSearchResults.value = false
    searchResults.value = []
  }
}

const selectSearchResult = (result) => {
  selectItem(result.id)
  // 在移动端选择搜索结果后自动关闭侧边栏
  if (isMobile.value) {
    mobileSidebarOpen.value = false
  }
}

const toggleSidebar = () => {
  // 在移动端切换侧边栏打开/关闭状态
  if (isMobile.value) {
    mobileSidebarOpen.value = !mobileSidebarOpen.value
  }
}

const submitFeedback = (isHelpful) => {
  if (isFeedbackDisabled(activeItemId.value)) return
  
  // 保存反馈记录
  saveFeedbackRecord(activeItemId.value, isHelpful)
  
  console.log('反馈:', isHelpful ? '有帮助' : '没帮助', '条目:', activeItemId.value)
  // 这里可以添加反馈提交到后端的逻辑
  alert(isHelpful ? '感谢您的反馈！' : '我们会努力改进，感谢您的反馈！')
}

// 生命周期
onMounted(() => {
  // 初始化反馈记录
  initFeedbackRecords()
  
  // 从路由参数初始化
  if (initialCategory.value) {
    expandedCategories.value.push(initialCategory.value)
  }
  
  if (initialItem.value) {
    selectItem(initialItem.value)
  } else if (initialCategory.value) {
    // 如果只有分类参数，选择第一个 item
    const category = categories.value.find(c => c.id === initialCategory.value)
    if (category && category.items.length > 0) {
      selectItem(category.items[0].id)
    }
  } else {
    // 默认选择第一个分类的第一个 item
    if (categories.value.length > 0 && categories.value[0].items.length > 0) {
      selectItem(categories.value[0].items[0].id)
    }
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})

// 监听路由变化
watch(
  () => route.query,
  (newQuery) => {
    if (newQuery.category) {
      initialCategory.value = newQuery.category
      expandedCategories.value.push(newQuery.category)
    }
    
    if (newQuery.item) {
      selectItem(newQuery.item)
    }
  },
  { deep: true }
)
</script>

<style scoped>
.help-center {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4eaf1 100%);
  padding: 48px 20px 64px;
  position: relative;
}

/* PC端可拖动头像积分小窗口 */
.draggable-menu {
  position: fixed;
  z-index: 100;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(12px);
  border: 1px solid #e3e9f5;
  border-radius: 16px;
  padding: 8px 12px;
  box-shadow: 0 8px 24px rgba(0, 82, 217, 0.15);
  cursor: move;
  touch-action: none;
  user-select: none;
  transition: box-shadow 0.2s ease;
  display: flex;
  align-items: center;
  gap: 10px;
}

.draggable-menu:hover {
  box-shadow: 0 12px 32px rgba(0, 82, 217, 0.22);
}

.drag-handle {
  position: absolute;
  left: 4px;
  top: 50%;
  transform: translateY(-50%);
  color: #a0b0cc;
  font-size: 14px;
  letter-spacing: -2px;
  cursor: grab;
}

.drag-handle:active {
  cursor: grabbing;
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

.help-shell {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 28px;
  align-items: start;
}

/* 左侧导航 */
.help-sidebar {
  width: 260px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 32px;
  height: auto;
  max-height: calc(100vh - 64px);
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: none;
  -ms-overflow-style: none;
  z-index: 5;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.help-sidebar::-webkit-scrollbar {
  display: none;
}

.help-sidebar:hover {
  scrollbar-width: thin;
  -ms-overflow-style: auto;
}

.help-sidebar:hover::-webkit-scrollbar {
  display: block;
  width: 6px;
}

.help-sidebar::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.help-sidebar::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.help-sidebar::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 确保侧边栏不遮挡内容 */
.help-sidebar {
  overflow: visible;
}

.sidebar-header {
  padding: 28px 24px 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  position: relative;
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
}

.sidebar-header h2 {
  margin: 0 0 4px 0;
  font-size: 20px;
  color: white;
  font-weight: 700;
  font-family: 'Newsreader', serif;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.sidebar-subtitle {
  margin: 0 0 20px 0;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 400;
  font-family: 'Newsreader', serif;
  letter-spacing: 1px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.search-container {
  position: relative;
  width: 100%;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.search-input {
  width: 100%;
  padding: 10px 40px 10px 16px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: transparent;
}

.search-input:focus {
  transform: translateX(4px);
}

.search-icon {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #4299e1;
  font-size: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.search-input:focus + .search-icon {
  transform: translateY(-50%) scale(1.1);
  color: #3182ce;
}

/* 搜索结果样式 */
.search-results {
  position: static;
  margin-top: 12px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  max-height: 300px;
  overflow-y: auto;
  /* 增加滚动条样式以提高可识别性 */
  scrollbar-width: thin;
  scrollbar-color: #c1c1c1 #f0f4f8;
}

/* 为搜索结果添加滚动条样式 */
.search-results::-webkit-scrollbar {
  width: 6px;
}

.search-results::-webkit-scrollbar-track {
  background: #f0f4f8;
  border-radius: 3px;
}

.search-results::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.search-results::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 搜索结果项样式 */
.search-result-item {
  padding: 16px 20px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 13px;
  display: flex;
  flex-direction: column;
  border-radius: 8px;
  margin: 4px;
}

.search-result-item:hover {
  background: linear-gradient(135deg, #f0f4ff 0%, #e8e6ff 100%);
  transform: translateX(4px);
}

.result-category {
  font-size: 11px;
  color: #4299e1;
  margin-bottom: 6px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.result-title {
  font-size: 13px;
  color: #1a202c;
  font-weight: 500;
  line-height: 1.4;
}

.search-no-results {
  padding: 32px 20px;
  text-align: center;
  color: #66788f;
  font-size: 14px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 8px;
  margin: 4px;
}

.help-menu {
  flex: 1;
  padding: 20px 12px;
}

.menu-category {
  margin-bottom: 16px;
  border-radius: 16px;
  overflow: hidden;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 249, 255, 0.9) 100%);
  backdrop-filter: blur(12px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(220, 224, 230, 0.8);
}

.menu-category:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(66, 153, 225, 0.15);
  border-color: rgba(66, 153, 225, 0.3);
}

.category-title {
  display: flex;
  align-items: center;
  padding: 20px 24px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 600;
  color: #1a202c;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  border-radius: 12px 12px 0 0;
  background: rgba(255, 255, 255, 0.7);
}

.category-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 24px;
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  border-radius: 0 2px 2px 0;
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.category-title:hover {
  background: linear-gradient(135deg, #f0f4ff 0%, #e8e6ff 100%);
  padding-left: 28px;
  transform: translateX(4px);
}

.category-title:hover::before {
  opacity: 1;
  transform: translateY(-50%) scaleY(1.1);
}

.category-icon {
  width: 24px;
  text-align: center;
  margin-right: 12px;
  font-size: 24px;
  color: #4299e1;
  line-height: 1;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.category-title:hover .category-icon {
  transform: scale(1.1);
}

.toggle-icon {
    margin-left: auto;
    font-size: 14px;
    color: #4299e1;
    opacity: 0;
    transform: translateX(-10px) rotate(0deg);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    width: 16px;
    height: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .toggle-icon.expanded {
    transform: translateX(-10px) rotate(90deg);
  }

  .category-title:hover .toggle-icon {
    opacity: 1;
    transform: translateX(0) rotate(0deg) scale(1.1);
    color: #3182ce;
  }

  .category-title:hover .toggle-icon.expanded {
    transform: translateX(0) rotate(90deg) scale(1.1);
  }

.category-items {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.category-items.expanded {
  max-height: 500px;
  overflow: visible;
}

/* 确保侧边栏能够正确滚动 */
.help-sidebar {
  overflow-y: auto;
  /* 添加滚动条样式以提高可识别性 */
  scrollbar-width: thin;
  scrollbar-color: #c1c1c1 #f0f4f8;
}

/* 为侧边栏添加滚动条样式 */
.help-sidebar::-webkit-scrollbar {
  width: 6px;
}

.help-sidebar::-webkit-scrollbar-track {
  background: #f0f4f8;
  border-radius: 3px;
}

.help-sidebar::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.help-sidebar::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.menu-item {
  padding: 12px 20px 12px 48px;
  cursor: pointer;
  font-size: 13px;
  color: #4a5568;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 0 8px 8px 0;
  position: relative;
  overflow: hidden;
}

.menu-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  transform: scaleY(0);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.menu-item:hover {
  background: linear-gradient(135deg, #f8f9ff 0%, #f0f0ff 100%);
  color: #1a202c;
  padding-left: 52px;
  transform: translateX(4px);
}

.menu-item:hover::before {
  transform: scaleY(1);
}

.menu-item.active {
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  color: white;
  font-weight: 500;
  padding-left: 52px;
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(66, 153, 225, 0.3);
}

.menu-item.active::before {
  transform: scaleY(1);
  background: white;
}



/* 右侧内容 */
.help-content {
  width: min(960px, 100%);
  justify-self: center;
  padding: 40px;
  overflow-y: auto;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4eaf1 100%);
  border-radius: 20px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
}



.top-nav {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 32px;
}

/* 移动端切换按钮 */
.mobile-toggle-btn {
  position: fixed;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  width: 40px;
  height: 40px;
  background: white;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: #4299e1;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 1003;
}

.mobile-toggle-btn:hover {
  transform: translateX(-50%) scale(1.05);
  box-shadow: 0 6px 16px rgba(66, 153, 225, 0.3);
  background: #f8f9ff;
}

.mobile-toggle-btn.open {
  transform: translateX(-50%) rotate(180deg);
}

.app-logo {
  font-size: 18px;
  font-weight: 700;
  color: #1a202c;
  text-decoration: none;
  cursor: pointer;
}

.breadcrumb {
  font-size: 14px;
  color: #4299e1;
  margin-bottom: 32px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(66, 153, 225, 0.2);
  font-weight: 500;
  letter-spacing: 0.5px;
}

.article {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.article:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

.article-title {
  font-size: 34px;
  color: #1a202c;
  margin: 0 0 32px 0;
  font-weight: 700;
  line-height: 1.3;
}

.article-content {
  font-size: 15px;
  line-height: 1.8;
  color: #66788f;
  background: rgba(255, 255, 255, 0.5);
  padding: 24px;
  border-radius: 12px;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.05);
}

.article-content h4 {
  margin: 32px 0 16px 0;
  font-size: 20px;
  color: #1a202c;
  font-weight: 600;
}

.article-content p {
  margin: 16px 0;
  line-height: 1.8;
}

.article-content ul,
.article-content ol {
  margin: 16px 0 16px 32px;
}

.article-content li {
  margin: 8px 0;
  line-height: 1.6;
}

.article-content ul li::before {
  content: '•';
  color: #4299e1;
  font-weight: bold;
  display: inline-block;
  width: 1em;
  margin-left: -1em;
}

.empty-state {
  text-align: center;
  padding: 80px 40px;
  color: #66788f;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  margin: 20px;
}

.feedback-section {
  margin-top: 40px;
  padding-top: 32px;
  border-top: 1px solid rgba(66, 153, 225, 0.2);
}

.feedback-section p {
  margin-bottom: 16px;
  font-size: 14px;
  color: #4a5568;
  font-weight: 500;
}

.feedback-buttons {
  display: flex;
  gap: 16px;
}

.feedback-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 12px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.feedback-btn.helpful {
  background: linear-gradient(135deg, #66bb6a 0%, #43a047 100%);
  color: white;
}

.feedback-btn.helpful:hover {
  background: linear-gradient(135deg, #43a047 0%, #388e3c 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(76, 175, 80, 0.3);
}

.feedback-btn.not-helpful {
  background: linear-gradient(135deg, #ef5350 0%, #c62828 100%);
  color: white;
}

.feedback-btn.not-helpful:hover {
  background: linear-gradient(135deg, #c62828 0%, #b71c1c 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(244, 67, 54, 0.3);
}

/* 反馈按钮禁用状态 */
.feedback-btn.disabled {
  background: #e0e0e0 !important;
  color: #9e9e9e !important;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
  opacity: 0.7;
}

.feedback-btn.disabled:hover {
  transform: none !important;
  box-shadow: none !important;
}

.feedback-submitted-hint {
  margin-top: 12px;
  font-size: 13px;
  color: #4caf50;
  font-weight: 500;
}

.related-section {
  margin-top: 40px;
  padding-top: 32px;
  border-top: 1px solid rgba(66, 153, 225, 0.2);
}

.related-section h3 {
  font-size: 18px;
  color: #1a202c;
  margin: 0 0 20px 0;
  font-weight: 600;
}

.related-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.related-item {
  padding: 16px 20px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  color: #4299e1;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: rgba(66, 153, 225, 0.05);
  border: 1px solid rgba(66, 153, 225, 0.1);
}

.related-item:hover {
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  color: white;
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(66, 153, 225, 0.3);
  text-decoration: none;
}

.related-item:last-child {
  margin-bottom: 0;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .help-shell {
    grid-template-columns: 1fr;
    max-width: 960px;
    gap: 20px;
  }

  .help-sidebar {
    position: static;
    width: 100%;
    max-height: none;
  }

  .help-content {
    width: 100%;
    padding: 32px;
  }

  .article {
    padding: 32px;
  }

  .article-title {
    font-size: 24px;
  }
}

/* 遮罩层样式 */
.sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 1000;
  transition: opacity 0.3s ease;
}

@media (max-width: 768px) {
  .help-shell {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .help-sidebar {
    width: 100%;
    height: 350px;
    left: 0;
    top: -350px;
    position: fixed;
    z-index: 1002;
    transition: top 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border-radius: 0 0 16px 16px;
  }

  .help-sidebar.mobile-open {
    top: 0;
  }

  .help-content {
    margin-left: 0;
    padding: 24px;
    padding-top: 70px;
  }

  .article {
    padding: 24px;
    border-radius: 12px;
  }

  .article-title {
    font-size: 20px;
  }

  /* 调整移动端侧边栏内容 */
  .sidebar-header {
    padding: 24px 20px;
    border-radius: 0 0 0 0;
  }

  .sidebar-header h2 {
    margin-bottom: 16px;
    font-size: 18px;
  }

  .search-input {
    font-size: 13px;
    padding: 8px 32px 8px 16px;
  }

  .category-title {
    padding: 12px 16px;
    font-size: 13px;
  }

  .menu-item {
    padding: 10px 16px 10px 40px;
    font-size: 12px;
  }

  /* 移动端遮罩层样式 */
  .sidebar-overlay {
    z-index: 1001;
  }
}

@media (max-width: 480px) {
  .help-content {
    padding: 16px;
    padding-top: 60px;
  }

  .article {
    padding: 16px;
    border-radius: 8px;
  }

  .article-title {
    font-size: 18px;
  }

  .feedback-buttons {
    flex-direction: column;
    gap: 12px;
  }

  .feedback-btn {
    width: 100%;
    text-align: center;
    padding: 10px 20px;
  }

  .sidebar-toggle-btn {
    width: 36px;
    height: 36px;
    font-size: 14px;
  }

  .sidebar-header {
    padding: 20px 16px;
  }

  .sidebar-header h2 {
    font-size: 16px;
    margin-bottom: 12px;
  }
}

/* 滚动条美化 */
.help-sidebar::-webkit-scrollbar {
  width: 6px;
}

.help-sidebar::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.help-sidebar::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.help-sidebar::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.help-content::-webkit-scrollbar {
  width: 8px;
}

.help-content::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.help-content::-webkit-scrollbar-thumb {
  background: #2196f3;
  border-radius: 4px;
}

.help-content::-webkit-scrollbar-thumb:hover {
  background: #1976d2;
}
</style>