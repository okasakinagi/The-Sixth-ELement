
<script setup>
import { reactive, ref, computed, nextTick, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import * as teamApi from '@/utils/teamApi'

const router = useRouter()
const route = useRoute()
const emailSearch = ref('')
const searchResult = ref(null)
const currentUserId = Number(localStorage.getItem('user_id') || 0)

// Points Gift State
const showPointsGiftModal = ref(false)
const giftAmount = ref(50)
const giftLoading = ref(false)
const giftError = ref('')
const pointsLimitInfo = ref({})

// Team Invitation State
const showInvitationModal = ref(false)
const invitationLoading = ref(false)
const invitationError = ref('')
const selectedTeamId = ref(null)
const myTeam = ref(null)

// 动态好友列表 - 从消息API加载
const friends = ref([])
const loadingFriends = ref(false)
const friendsError = ref('')
const friendsLoadingTimer = ref(null)

const actionConfirm = reactive({
  visible: false,
  type: '',
  title: '',
  message: '',
  confirmText: '确认',
  payload: null,
  loading: false,
  error: '',
})

const resultDialog = reactive({
  visible: false,
  title: '',
  message: '',
})

function showResultDialog(title, message) {
  resultDialog.title = title
  resultDialog.message = message
  resultDialog.visible = true
}

function closeResultDialog() {
  resultDialog.visible = false
  resultDialog.title = ''
  resultDialog.message = ''
}

function closeActionConfirm() {
  actionConfirm.visible = false
  actionConfirm.type = ''
  actionConfirm.title = ''
  actionConfirm.message = ''
  actionConfirm.confirmText = '确认'
  actionConfirm.payload = null
  actionConfirm.loading = false
  actionConfirm.error = ''
}

function isFriendInteractionMessage(msg) {
  if (!msg?.sender_id || !msg?.sender_nickname) {
    return false
  }
  if (currentUserId > 0 && Number(msg.sender_id) === currentUserId) {
    return false
  }
  if (msg.message_type !== 'system') {
    return true
  }
  // 系统类型里仅保留“用户间互动”消息，避免把纯平台通知混进好友列表。
  return msg.ref_type === 'user' || msg.ref_type === 'team_invite'
}

function ensureFriendInList(friend) {
  if (!friend || !friend.id) {
    return
  }
  if (currentUserId > 0 && Number(friend.id) === currentUserId) {
    return
  }
  if (friends.value.some((f) => Number(f.id) === Number(friend.id))) {
    return
  }
  friends.value.unshift({
    id: friend.id,
    nickname: friend.nickname,
    title: friend.title || '朋友',
    avatar: friend.avatar || (friend.nickname?.charAt(0) || '👤'),
    status: friend.status || 'online',
    isSystemFriend: false,
    unreadCount: 0,
  })
}

/**
 * 从消息中提取好友列表
 * 好友定义：有互相发过的消息（系统消息除外）
 */
async function loadFriendsFromMessages() {
  try {
    console.log('[LFF] 开始加载好友列表...')
    loadingFriends.value = true
    friendsError.value = ''
    
    // 添加10秒超时机制，防止请求永远卡住
    friendsLoadingTimer.value = setTimeout(() => {
      if (loadingFriends.value) {
        console.warn('[LFF] 好友列表加载超时(10s)，自动取消')
        loadingFriends.value = false
        friendsError.value = '加载超时，请刷新页面'
        friends.value = []
      }
    }, 10000)
    
    const response = await teamApi.getMessages({
      limit: 100,
      offset: 0
    })
    
    console.log('[LFF] 获取消息成功:', response.messages?.length ?? 0, '条')
    
    const messages = response.messages || []
    const friendsMap = new Map()
    
    // 提取与用户互动过的发送者（含邀请/赠送后的系统回执记录）
    messages.forEach(msg => {
      if (isFriendInteractionMessage(msg)) {
        // 如果这个发送者还不在好友列表中，就加入
        if (!friendsMap.has(msg.sender_id)) {
          friendsMap.set(msg.sender_id, {
            id: msg.sender_id,
            nickname: msg.sender_nickname,
            title: '朋友',
            avatar: msg.sender_nickname?.charAt(0) || '👤',
            status: 'online',
            isSystemFriend: false,
            unreadCount: 0,
          })
        }

        if (msg.status === 'unread') {
          const friend = friendsMap.get(msg.sender_id)
          friend.unreadCount = (friend.unreadCount || 0) + 1
        }
      }
    })
    
    // 构建最终的好友列表
    let friendsList = Array.from(friendsMap.values())
    
    // 添加系统消息虚拟好友（放在第一个）
    const systemMessages = messages.filter(m => m.message_type === 'system')
    if (systemMessages.length > 0) {
      friendsList.unshift({
        id: 'system',
        nickname: '系统消息',
        title: '系统通知',
        avatar: '📢',
        status: 'online',
        isSystemFriend: true,
        unreadCount: systemMessages.filter(m => m.status === 'unread').length,
      })
    }
    
    console.log('[LFF] 好友列表加载完成:', friendsList.length, '个好友')
    friends.value = friendsList

    const openFriendId = route.query.openFriendId
    if (openFriendId) {
      const targetFriendId = Number(openFriendId)
      if (targetFriendId) {
        const target = friends.value.find((f) => Number(f.id) === targetFriendId)
        if (target) {
          openFriendDialog(target)
          router.replace({ name: route.name, query: {} })
        }
      }
    }
  } catch (error) {
    friendsError.value = error.message || '加载好友失败'
    console.error('[LFF] 加载好友错误:', error)
    friends.value = []
  } finally {
    // 清除超时计时器
    if (friendsLoadingTimer.value) {
      clearTimeout(friendsLoadingTimer.value)
      friendsLoadingTimer.value = null
    }
    loadingFriends.value = false
  }
}

// Chat State - 从API加载消息
const messages = ref([]) // 当前对话的消息列表
const loadingMessages = ref(false)
const messagesError = ref('')
const currentChatType = ref('') // 当前聊天类型：'friend' 或 'system'

const timelineMessages = computed(() => {
  return [...messages.value].sort((a, b) => {
    const ta = new Date(a.created_at).getTime()
    const tb = new Date(b.created_at).getTime()
    return ta - tb
  })
})

// 邀请响应状态
const invitationResponseLoading = ref(false)
const invitationResponseError = ref('')

function scrollChatToBottom() {
  nextTick(() => {
    const container = document.querySelector('.chat-messages')
    if (container) {
      container.scrollTop = container.scrollHeight
    }
  })
}

/**
 * 加载与特定好友或系统消息的消息
 * @param {number|string} friendId - 好友ID (或 'system')
 * @param {boolean} isSystemFriend - 是否是系统消息虚拟好友
 */
async function loadChatMessages(friendId, isSystemFriend = false) {
  try {
    loadingMessages.value = true
    messagesError.value = ''
    
    // 调用API获取消息
    const response = await teamApi.getMessages({
      limit: 50,
      offset: 0
    })
    
    // 根据聊天类型过滤消息
    let filteredMessages = response.messages || []
    
    if (isSystemFriend) {
      // 系统消息虚拟好友：只显示系统消息
      currentChatType.value = 'system'
      filteredMessages = filteredMessages.filter(m => m.message_type === 'system')
    } else {
      // 普通好友：显示来自该好友的所有消息（邀请、积分赠送等）
      currentChatType.value = 'friend'
      filteredMessages = filteredMessages.filter(m => m.sender_id === friendId)
    }

    filteredMessages = filteredMessages.sort((a, b) => {
      const ta = new Date(a.created_at).getTime()
      const tb = new Date(b.created_at).getTime()
      return ta - tb
    })
    
    messages.value = filteredMessages

    const unreadIds = filteredMessages
      .filter(m => m.status === 'unread' && m.id)
      .map(m => m.id)

    if (unreadIds.length > 0) {
      await Promise.all(unreadIds.map(id => teamApi.markMessageAsRead(id).catch(() => null)))
      await loadFriendsFromMessages()
    }
  } catch (error) {
    messagesError.value = error.message || '加载消息失败'
    console.error('加载消息错误:', error)
    messages.value = []
  } finally {
    loadingMessages.value = false
    scrollChatToBottom()
  }
}

/**
 * 获取格式化的消息内容（支持不同消息类型）
 */
function formatMessage(msg) {
  if (!msg) return {}
  
  switch (msg.message_type) {
    case 'team_invite':
      return {
        type: 'invite',
        sender: msg.sender_nickname || '系统',
        content: `邀请你加入队伍`,
        displayText: `${msg.sender_nickname} 邀请你加入队伍`,
        teamId: msg.ref_id,
        messageId: msg.id,
        isAccepted: msg.is_accepted
      }
    
    case 'points_gift':
      return {
        type: 'points',
        sender: msg.sender_nickname || '系统',
        content: `赠送了 ${msg.points_amount} 积分`,
        displayText: `${msg.sender_nickname} 赠送了 ${msg.points_amount} 积分`,
        points: msg.points_amount,
        messageId: msg.id
      }
    
    case 'system':
    default:
      return {
        type: 'text',
        sender: msg.sender_nickname || '系统',
        content: msg.content || msg.title,
        messageId: msg.id
      }
  }
}

/**
 * 接受邀请消息
 * @param {number} messageId - 消息ID
 * @param {number} invitationId - 邀请ID（从msg.ref_id获取）
 */
async function acceptInviteFromMessage(messageId, invitationId) {
  try {
    invitationResponseLoading.value = true
    invitationResponseError.value = ''
    
    // 调用接受邀请API - 使用 invitationId (msg.ref_id)
    await teamApi.acceptInvitation(invitationId)
    
    window.dispatchEvent(new CustomEvent('team:updated'))
    await loadMyTeam() // 重新加载我的队伍
    await loadFriendsFromMessages()
    if (activeDialogFriend.value) {
      await loadChatMessages(activeDialogFriend.value.id, !!activeDialogFriend.value.isSystemFriend)
    }
    showResultDialog('加入成功', '你已成功加入队伍。组队后你填写问卷获得的积分会自动记录到队长的账户中。')
  } catch (error) {
    invitationResponseError.value = error.message || '接受邀请失败'
    console.error('接受邀请错误:', error)
    throw error
  } finally {
    invitationResponseLoading.value = false
  }
}

/**
 * 拒绝邀请消息
 */
async function rejectInviteFromMessage(messageId, invitationId) {
  try {
    invitationResponseLoading.value = true
    invitationResponseError.value = ''
    
    await teamApi.rejectInvitation(invitationId)
    await loadFriendsFromMessages()
    if (activeDialogFriend.value) {
      await loadChatMessages(activeDialogFriend.value.id, !!activeDialogFriend.value.isSystemFriend)
    }
    showResultDialog('已拒绝邀请', '邀请状态已更新。')
  } catch (error) {
    invitationResponseError.value = error.message || '拒绝邀请失败'
    console.error('拒绝邀请错误:', error)
  } finally {
    invitationResponseLoading.value = false
  }
}

// Dialog State - 用于显示聊天和功能
const activeDialogFriend = ref(null)

function openFriendDialog(friend) {
  activeDialogFriend.value = friend
  // 加载消息（系统消息虚拟好友需要特殊处理）
  loadChatMessages(friend.id, friend.isSystemFriend || false)
  // 非系统好友才需要加载队伍信息（用于邀请功能）
  if (!friend.isSystemFriend) {
    loadMyTeam()
  }
}

function closeFriendDialog() {
  activeDialogFriend.value = null
  showPointsGiftModal.value = false
  showInvitationModal.value = false
  invitationError.value = ''
}

// 页面加载时初始化好友列表
loadFriendsFromMessages()

async function handleTeamUpdated() {
  await loadFriendsFromMessages()
  if (activeDialogFriend.value) {
    await loadChatMessages(
      activeDialogFriend.value.id,
      !!activeDialogFriend.value.isSystemFriend
    )
  }
}

onMounted(() => {
  window.addEventListener('team:updated', handleTeamUpdated)
})

onBeforeUnmount(() => {
  window.removeEventListener('team:updated', handleTeamUpdated)
})

watch(
  () => route.query.openFriendId,
  () => {
    if (route.query.openFriendId) {
      loadFriendsFromMessages()
    }
  }
)

watch(
  () => timelineMessages.value.length,
  () => {
    if (activeDialogFriend.value && !loadingMessages.value) {
      scrollChatToBottom()
    }
  }
)

// 加载我的队伍信息
const myTeamLoadingTimer = ref(null)

async function loadMyTeam() {
  try {
    console.log('[TeamLoad] 开始加载队伍信息...')
    
    // 添加5秒超时机制
    myTeamLoadingTimer.value = setTimeout(() => {
      console.warn('[TeamLoad] 队伍加载超时(5s)，取消等待')
      myTeam.value = null
    }, 5000)
    
    const result = await teamApi.getMyTeam()
    console.log('[TeamLoad] 队伍信息获取成功:', result)
    
    if (result.team) {
      myTeam.value = result.team
      console.log('[TeamLoad] 用户已加入队伍:', result.team.title)
    } else {
      myTeam.value = null
      console.log('[TeamLoad] 用户未加入任何队伍')
    }
  } catch (error) {
    console.error('[TeamLoad] 加载队伍信息失败:', error)
    console.error('[TeamLoad] 错误详情:', {
      message: error.message,
      status: error.status,
      stack: error.stack
    })
    myTeam.value = null
  } finally {
    // 清除超时计时器
    if (myTeamLoadingTimer.value) {
      clearTimeout(myTeamLoadingTimer.value)
      myTeamLoadingTimer.value = null
    }
  }
}

// 打开积分赠送modal
async function openPointsGiftModal() {
  try {
    giftError.value = ''
    giftLoading.value = true
    
    // 获取今日积分赠送限制信息
    const limitInfo = await teamApi.getPointsGiftLimitInfo()
    pointsLimitInfo.value = limitInfo
    
    // 限制赠送数量为剩余可赠送的，或最多100分
    giftAmount.value = Math.min(100, limitInfo.remaining || 0)
    
    showPointsGiftModal.value = true
  } catch (error) {
    giftError.value = error.message || '获取赠送限制失败'
    console.error('获取积分限制错误:', error)
  } finally {
    giftLoading.value = false
  }
}

function closePointsGiftModal() {
  showPointsGiftModal.value = false
  giftError.value = ''
}

// 搜索状态
const searching = ref(false)
const searchError = ref('')
const searchTimeoutTimer = ref(null)
const searchHintPulse = ref(false)

function pulseSearchIcon() {
  searchHintPulse.value = true
  setTimeout(() => {
    searchHintPulse.value = false
  }, 650)
}

function handleSearch() {
  if (!emailSearch.value) {
    // 如果没有输入，聚焦搜索框方便用户输入
    const input = document.querySelector('.search-box input')
    if (input) input.focus()
    pulseSearchIcon()
    return
  }
  performSearch()
}

async function performSearch() {
  const email = emailSearch.value.trim()
  if (!email) {
    searchError.value = '请输入邮箱地址'
    return
  }
  
  try {
    console.log('[Search] 开始搜索邮箱:', email)
    searching.value = true
    searchError.value = ''
    
    // 添加8秒超时保护
    searchTimeoutTimer.value = setTimeout(() => {
      if (searching.value) {
        console.warn('[Search] 搜索超时(8s)，取消操作')
        searching.value = false
        searchError.value = '搜索超时，请检查网络连接后重试'
      }
    }, 8000)
    
    // 调用API搜索用户
    const result = await teamApi.searchUserByEmail(email)
    console.log('[Search] 搜索成功，找到用户:', result.nickname)
    
    // 检查这个用户是否已在好友列表中
    const existingFriend = friends.value.find(f => f.id === result.id)
    
    if (existingFriend) {
      console.log('[Search] 用户已是好友，打开对话')
      // 已是好友，直接打开对话
      openFriendDialog(existingFriend)
    } else {
      console.log('[Search] 新用户，添加到好友列表')
      // 新用户，添加到好友列表并打开对话
      const newFriend = {
        id: result.id,
        nickname: result.nickname,
        title: '朋友',
        avatar: result.nickname?.charAt(0) || '👤',
        status: 'online',
        isSystemFriend: false
      }
      
      friends.value.push(newFriend)
      openFriendDialog(newFriend)
    }
    
    emailSearch.value = ''
  } catch (error) {
    console.error('[Search] 搜索失败:', error)
    console.error('[Search] 错误详情:', {
      message: error.message,
      status: error.status,
      stack: error.stack
    })
    
    if (error.status === 404) {
      searchError.value = '邮箱不存在'
    } else if (error.status === 422) {
      searchError.value = error.message || '无效的邮箱'
    } else {
      searchError.value = error.message || '搜索失败'
    }
  } finally {
    // 清除超时计时器
    if (searchTimeoutTimer.value) {
      clearTimeout(searchTimeoutTimer.value)
      searchTimeoutTimer.value = null
    }
    searching.value = false
    console.log('[Search] 搜索完成，loading状态已重置为 false')
  }
}

// 打开积分赠送 modal
async function openInvitationModal() {
  if (!activeDialogFriend.value || !myTeam.value) {
    invitationError.value = '请先创建或加入一个队伍'
    return
  }
  
  showInvitationModal.value = true
}

// 发送组队邀请
async function sendTeamInvitation() {
  if (!activeDialogFriend.value || !myTeam.value) {
    invitationError.value = '邀请信息不完整'
    return
  }
  
  try {
    invitationLoading.value = true
    invitationError.value = ''

    ensureFriendInList(activeDialogFriend.value)
    
    await teamApi.sendTeamInvitation(myTeam.value.id, activeDialogFriend.value.id)

    await loadFriendsFromMessages()
    await loadChatMessages(activeDialogFriend.value.id, false)
    
    // 邀请成功
    showInvitationModal.value = false
    showResultDialog('邀请已发送', `已邀请 ${activeDialogFriend.value.nickname} 加入队伍。若对方接受，其后续填写积分将自动记入队长统计。`)
  } catch (error) {
    invitationError.value = error.message || '发送邀请失败'
    console.error('发送邀请错误:', error)
  } finally {
    invitationLoading.value = false
  }
}

function openAcceptInviteConfirm(messageId, invitationId, senderNickname) {
  let confirmMessage = `确认接受 ${senderNickname || '该用户'} 的队伍邀请吗？接受后，你后续填写问卷获得的积分将自动记录到队长统计。`
  if (myTeam.value?.id) {
    confirmMessage = `你当前在队伍「${myTeam.value.title}」。确认后将先退出当前队伍，再加入 ${senderNickname || '对方'} 所在队伍；后续填写问卷获得的积分将自动记录到新队长统计。`
  }

  actionConfirm.type = 'accept_invite'
  actionConfirm.title = '确认接受队伍邀请'
  actionConfirm.message = confirmMessage
  actionConfirm.confirmText = '确认接受'
  actionConfirm.payload = { messageId, invitationId }
  actionConfirm.error = ''
  actionConfirm.visible = true
}

function openPointsGiftConfirm() {
  if (!activeDialogFriend.value || giftAmount.value <= 0) {
    giftError.value = '请输入有效的积分数量'
    return
  }
  if (giftAmount.value > (pointsLimitInfo.value.remaining || 0)) {
    giftError.value = `剩余赠送额度不足，最多可赠送 ${pointsLimitInfo.value.remaining} 积分`
    return
  }

  actionConfirm.type = 'points_gift'
  actionConfirm.title = '确认赠送积分'
  actionConfirm.message = `确认向 ${activeDialogFriend.value.nickname} 赠送 ${giftAmount.value} 积分吗？该操作会立即扣减你的积分余额。`
  actionConfirm.confirmText = '确认赠送'
  actionConfirm.payload = {
    receiverId: activeDialogFriend.value.id,
    nickname: activeDialogFriend.value.nickname,
    amount: giftAmount.value,
  }
  actionConfirm.error = ''
  actionConfirm.visible = true
}

async function runConfirmedAction() {
  if (!actionConfirm.payload) {
    closeActionConfirm()
    return
  }

  try {
    actionConfirm.loading = true
    actionConfirm.error = ''

    if (actionConfirm.type === 'accept_invite') {
      const { messageId, invitationId } = actionConfirm.payload
      await acceptInviteFromMessage(messageId, invitationId)
      closeActionConfirm()
      return
    }

    if (actionConfirm.type === 'points_gift') {
      const { receiverId, amount } = actionConfirm.payload
      await sendPointsGiftWithPayload(receiverId, amount)
      closeActionConfirm()
      return
    }
  } catch (error) {
    actionConfirm.error = error?.message || '操作失败，请稍后重试'
  } finally {
    actionConfirm.loading = false
  }
}

async function sendPointsGiftWithPayload(receiverId, amount) {
  giftLoading.value = true
  giftError.value = ''
  try {
    ensureFriendInList(activeDialogFriend.value)
    await teamApi.sendPointsGift({
      receiver_id: receiverId,
      points_amount: amount,
    })
    closePointsGiftModal()
    await loadFriendsFromMessages()
    if (activeDialogFriend.value) {
      await loadChatMessages(activeDialogFriend.value.id, !!activeDialogFriend.value.isSystemFriend)
    }
    showResultDialog('赠送成功', `成功赠送 ${amount} 积分给 ${activeDialogFriend.value.nickname}。`)
  } finally {
    giftLoading.value = false
  }
}
</script>

<template>
  <div class="friend-section">
    <div class="header">
      <h2>我的好友 <span class="count">({{ friends.length }})</span></h2>
      <div class="search-area">
        <div class="search-box">
          <span class="search-icon" :class="{ searching: searching, pulse: searchHintPulse }">🔍</span>
          <input 
            v-model="emailSearch" 
            placeholder="请输入邮箱搜索好友..." 
            @keyup.enter="handleSearch"
            :disabled="searching"
          />
          <button 
            v-show="emailSearch && !searching" 
            class="search-btn"
            @click="handleSearch"
            title="搜索用户"
          >
            搜索
          </button>
          <div v-show="searching" class="search-loading">
            <span class="spinner-mini"></span>
          </div>
        </div>
        <div v-if="searchError" class="search-error">
          ⚠️ {{ searchError }}
        </div>
      </div>
    </div>

    <!-- Friend Cards Grid -->
    <div class="friends-grid">
      <div 
        v-for="friend in friends" 
        :key="friend.id" 
        class="friend-card"
        @click="openFriendDialog(friend)"
      >
        <div class="card-top">
          <div class="avatar-wrapper">
            <div class="avatar">{{ friend.avatar }}</div>
            <div class="status-dot" :class="friend.status"></div>
          </div>
          <div class="actions">
            <!-- Hover actions could go here -->
            <span class="more-icon">...</span>
          </div>
        </div>
        
        <div class="card-info">
          <h3 class="nickname">{{ friend.nickname }}</h3>
          <p class="title">{{ friend.title }}</p>
        </div>

        <span v-if="friend.unreadCount > 0" class="unread-badge">{{ friend.unreadCount }}</span>
        
        <div class="card-footer">
          <button class="chat-btn">
            <span class="icon">💬</span> 交互
          </button>
        </div>
      </div>
      
      <!-- Add Friend Card (Optional placeholder) -->
      <div class="friend-card add-card" @click="handleSearch">
        <div class="add-icon">+</div>
        <span>添加好友</span>
      </div>
    </div>

    <!-- Friend Chat Window - 保留聊天感觉 -->
    <Transition name="slide-up">
      <div v-if="activeDialogFriend" class="chat-window">
        <div class="chat-header">
          <div class="user-info">
            <div class="avatar-small">{{ activeDialogFriend.avatar }}</div>
            <div class="details">
              <span class="name">{{ activeDialogFriend.nickname }}</span>
              <span v-if="activeDialogFriend.isSystemFriend" class="status-text">系统消息</span>
              <span v-else class="status-text">{{ activeDialogFriend.status === 'online' ? '在线' : '离线' }}</span>
            </div>
          </div>
          <button class="close-btn" @click="closeFriendDialog">×</button>
        </div>
        
        <!-- Chat Messages -->
        <div class="chat-messages">
          <div class="message-date">Today</div>
          
          <!-- Loading state -->
          <div v-if="loadingMessages" class="messages-loading">
            <span class="spinner"></span> 加载消息中...
          </div>
          
          <!-- Error state -->
          <div v-else-if="messagesError" class="messages-error">
            ⚠️ {{ messagesError }}
          </div>
          
          <!-- Messages list -->
          <div v-else-if="timelineMessages.length > 0">
            <template v-for="msg in timelineMessages" :key="msg.id">
              <!-- 系统会话中的消息 -->
              <div
                v-if="currentChatType === 'system'"
                :class="['system-message', { 'accepted': msg.is_accepted }]"
              >
                <div class="system-content">
                  <strong>{{ msg.title }}</strong>
                  <p style="margin: 4px 0 0 0; font-size: 12px;">{{ msg.content }}</p>
                </div>
                <div class="system-time">{{ new Date(msg.created_at).toLocaleTimeString() }}</div>
              </div>

              <!-- 好友会话：队伍邀请 -->
              <div
                v-else-if="msg.message_type === 'team_invite'"
                :class="['system-message', 'invite-message', { 'accepted': msg.is_accepted }]"
              >
                <div class="system-icon">👥</div>
                <div class="system-content">
                  <strong>{{ msg.sender_nickname }}</strong> 邀请你加入队伍
                </div>

                <div v-if="msg.can_accept_invite" class="invite-actions">
                  <button
                    class="invite-btn accept-btn"
                    @click="openAcceptInviteConfirm(msg.id, msg.ref_id, msg.sender_nickname)"
                    :disabled="invitationResponseLoading"
                  >
                    {{ invitationResponseLoading ? '处理中...' : '✓ 接受' }}
                  </button>
                  <button
                    class="invite-btn reject-btn"
                    @click="rejectInviteFromMessage(msg.id, msg.ref_id)"
                    :disabled="invitationResponseLoading"
                  >
                    {{ invitationResponseLoading ? '处理中...' : '✕ 拒绝' }}
                  </button>
                </div>
                <div v-else-if="msg.invitation_status === 'accepted' || msg.is_accepted" class="invite-accepted">✓ 已接受</div>
                <div v-else-if="msg.invitation_status === 'rejected'" class="invite-accepted">已拒绝</div>
                <div v-else-if="msg.invitation_status === 'expired'" class="invite-accepted">已过期</div>
                <div v-else class="invite-accepted">邀请记录</div>

                <div class="system-time">{{ new Date(msg.created_at).toLocaleTimeString() }}</div>
              </div>

              <!-- 好友会话：积分赠送 -->
              <div v-else-if="msg.message_type === 'points_gift'" class="system-message points-message">
                <div class="system-icon">🎁</div>
                <div class="system-content">
                  <strong>{{ msg.sender_nickname }}</strong> 赠送了你
                  <span class="points-highlight">{{ msg.points_amount }}</span> 积分
                </div>
                <div class="system-time">{{ new Date(msg.created_at).toLocaleTimeString() }}</div>
              </div>

              <!-- 好友会话：普通系统文本 -->
              <div v-else class="message-bubble received">
                <div class="bubble-content">{{ msg.content }}</div>
                <div class="bubble-time">{{ new Date(msg.created_at).toLocaleTimeString() }}</div>
              </div>
            </template>
          </div>
          
          <!-- Empty state -->
          <div v-else class="empty-chat-state">
            👋 暂无消息
          </div>
        </div>
        
        <!-- Action Buttons - 只有功能按钮，没有消息输入框 -->
        <div v-if="!activeDialogFriend.isSystemFriend" class="chat-actions">
          <p class="actions-hint">与 {{ activeDialogFriend.nickname }} 互动：</p>
          <div class="action-buttons">
            <!-- 赠送积分按钮 -->
            <button 
              class="action-btn gift-action"
              @click="openPointsGiftModal"
              title="赠送积分给好友"
            >
              <span class="icon">🎁</span>
              <span class="label">赠送积分</span>
            </button>
            
            <!-- 邀请加入队伍按钮 -->
            <button 
              class="action-btn invite-action"
              @click="openInvitationModal"
              :disabled="!myTeam"
              :title="!myTeam ? '请先加入或创建一个队伍' : '邀请加入队伍'"
            >
              <span class="icon">👥</span>
              <span class="label">邀请加入队伍</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Team Invitation Modal -->
    <Transition name="modal-fade">
      <div v-if="showInvitationModal" class="modal-overlay" @click.self="() => {showInvitationModal = false}">
        <div class="modal-card">
          <div class="modal-header">
            <h3>邀请加入队伍</h3>
            <button class="close-btn" @click="() => {showInvitationModal = false}">×</button>
          </div>
          
          <div class="modal-body">
            <div v-if="invitationError" class="error-message">
              ⚠️ {{ invitationError }}
            </div>
            
            <div v-if="myTeam" class="invitation-info">
              <p class="info-item">
                <span class="label">邀请人：</span>
                <strong>{{ activeDialogFriend?.nickname }}</strong>
              </p>
              <p class="info-item">
                <span class="label">队伍：</span>
                <strong>{{ myTeam.title }}</strong>
              </p>
              <p class="info-item">
                <span class="label">队徽：</span>
                <span class="team-icon">{{ myTeam.icon }}</span>
              </p>
            </div>
          </div>
          
          <div class="modal-footer">
            <button class="cancel-btn" @click="() => {showInvitationModal = false}">取消</button>
            <button 
              class="confirm-btn" 
              :disabled="invitationLoading || !myTeam"
              @click="sendTeamInvitation"
            >
              {{ invitationLoading ? '发送中...' : '确认邀请' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Points Gift Modal -->
    <Transition name="modal-fade">
      <div v-if="showPointsGiftModal" class="modal-overlay" @click.self="closePointsGiftModal">
        <div class="modal-card">
          <div class="modal-header">
            <h3>赠送积分</h3>
            <button class="close-btn" @click="closePointsGiftModal">×</button>
          </div>
          
          <div class="modal-body">
            <div class="gift-info">
              <p class="recipient-info">赠送给：<strong>{{ activeDialogFriend?.nickname }}</strong></p>
              
              <div v-if="giftError" class="error-message">
                ⚠️ {{ giftError }}
              </div>
              
              <div class="form-group">
                <label>赠送积分数量</label>
                <div class="input-with-unit">
                  <input 
                    v-model.number="giftAmount" 
                    type="number" 
                    min="0"
                    :max="pointsLimitInfo.remaining || 0"
                    placeholder="输入积分数量"
                  />
                  <span class="unit">积分</span>
                </div>
              </div>
              
              <div class="limit-info">
                <p><strong>今日限制：</strong> {{ pointsLimitInfo.limit || 200 }} 积分</p>
                <p><strong>已赠送：</strong> {{ pointsLimitInfo.sent_today || 0 }} 积分</p>
                <p class="remaining">
                  <strong>还可赠送：</strong> 
                  <span :class="{ 'low': (pointsLimitInfo.remaining || 0) < 50 }">
                    {{ pointsLimitInfo.remaining || 0 }} 积分
                  </span>
                </p>
              </div>
            </div>
          </div>
          
          <div class="modal-footer">
            <button class="cancel-btn" @click="closePointsGiftModal">取消</button>
            <button 
              class="confirm-btn" 
              :disabled="giftLoading || giftAmount <= 0 || giftAmount > (pointsLimitInfo.remaining || 0)"
              @click="openPointsGiftConfirm"
            >
              {{ giftLoading ? '赠送中...' : '确认赠送' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Action Confirm Modal -->
    <Transition name="modal-fade">
      <div v-if="actionConfirm.visible" class="modal-overlay" @click.self="closeActionConfirm">
        <div class="modal-card">
          <div class="modal-header">
            <h3>{{ actionConfirm.title }}</h3>
            <button class="close-btn" @click="closeActionConfirm">×</button>
          </div>
          <div class="modal-body">
            <p>{{ actionConfirm.message }}</p>
            <div v-if="actionConfirm.error" class="error-message">
              ⚠️ {{ actionConfirm.error }}
            </div>
          </div>
          <div class="modal-footer">
            <button class="cancel-btn" @click="closeActionConfirm" :disabled="actionConfirm.loading">取消</button>
            <button class="confirm-btn" @click="runConfirmedAction" :disabled="actionConfirm.loading">
              {{ actionConfirm.loading ? '处理中...' : actionConfirm.confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Result Modal -->
    <Transition name="modal-fade">
      <div v-if="resultDialog.visible" class="modal-overlay" @click.self="closeResultDialog">
        <div class="modal-card">
          <div class="modal-header">
            <h3>{{ resultDialog.title }}</h3>
            <button class="close-btn" @click="closeResultDialog">×</button>
          </div>
          <div class="modal-body">
            <p>{{ resultDialog.message }}</p>
          </div>
          <div class="modal-footer">
            <button class="confirm-btn" @click="closeResultDialog">我知道了</button>
          </div>
        </div>
      </div>
    </Transition>
    
    <!-- Backdrop for mobile has been removed as it's not needed with fixed positioning -->
  </div>
</template>

<style scoped>
.friend-section {
  padding: 24px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  gap: 16px;
}

.header h2 {
  font-size: 20px;
  color: #1e293b;
  font-weight: 700;
  margin: 0;
}

.count {
  color: #94a3b8;
  font-size: 14px;
  font-weight: 500;
}

.search-area {
  width: 320px;
  max-width: 100%;
}

.search-box {
  position: relative;
  width: 100%;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  font-size: 14px;
  transform-origin: center;
}

.search-icon.searching {
  animation: searchPulse 0.9s ease-in-out infinite;
}

.search-icon.pulse {
  animation: searchHintPulse 0.65s ease-in-out;
}

.search-box input {
  width: 100%;
  padding: 8px 88px 8px 32px;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  font-size: 13px;
  transition: all 0.2s;
  background: white;
}

.search-box input:focus {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
  outline: none;
}

.search-box input:disabled {
  background: #f1f5f9;
  cursor: not-allowed;
}

.search-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 52px;
  height: 28px;
  padding: 0 10px;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 14px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.search-btn:hover {
  background: #4f46e5;
}

.search-loading {
  position: absolute;
  right: 24px;
  top: 50%;
  transform: translateY(-50%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
}

.spinner-mini {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid #e2e8f0;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

.search-error {
  margin-top: 8px;
  padding: 8px 12px;
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fca5a5;
  border-radius: 6px;
  font-size: 12px;
}

@keyframes searchPulse {
  0% { transform: translateY(-50%) scale(1); opacity: 0.9; }
  50% { transform: translateY(-50%) scale(1.18); opacity: 1; }
  100% { transform: translateY(-50%) scale(1); opacity: 0.9; }
}

@keyframes searchHintPulse {
  0% { transform: translateY(-50%) scale(1); color: #94a3b8; }
  40% { transform: translateY(-50%) scale(1.35); color: #4f46e5; }
  100% { transform: translateY(-50%) scale(1); color: #94a3b8; }
}

/* Grid Layout */
.friends-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}

/* Friend Card */
.friend-card {
  background: white;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.friend-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 20px -8px rgba(0, 0, 0, 0.1);
  border-color: #cbd5e1;
}

.add-card {
  border: 2px dashed #cbd5e1;
  background: #f8fafc;
  justify-content: center;
  gap: 12px;
  color: #64748b;
  min-height: 200px;
}
.add-card:hover {
  border-color: #6366f1;
  color: #6366f1;
}
.add-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #94a3b8;
  transition: all 0.2s;
}
.add-card:hover .add-icon {
  background: #e0e7ff;
  color: #6366f1;
}

.card-top {
  width: 100%;
  display: flex;
  justify-content: center;
  position: relative;
  margin-bottom: 12px;
}

.avatar-wrapper {
  position: relative;
}

.avatar {
  width: 64px;
  height: 64px;
  background: #f1f5f9;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  border: 3px solid white;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
}

.status-dot {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid white;
}
.status-dot.online { background: #22c55e; }
.status-dot.offline { background: #94a3b8; }
.status-dot.busy { background: #ef4444; }

.more-icon {
  position: absolute;
  top: -10px;
  right: -10px;
  color: #cbd5e1;
  padding: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}
.friend-card:hover .more-icon { opacity: 1; }

.card-info {
  margin-bottom: 16px;
}

.unread-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 999px;
  background: #ef4444;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  line-height: 20px;
  text-align: center;
  box-shadow: 0 2px 6px rgba(239, 68, 68, 0.35);
}

.nickname {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}

.title {
  margin: 0;
  font-size: 12px;
  color: #64748b;
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 10px;
  display: inline-block;
}

.card-footer {
  width: 100%;
  margin-top: auto;
}

.chat-btn {
  width: 100%;
  padding: 8px;
  background: #f8fafc;
  color: #475569;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.2s;
}

.friend-card:hover .chat-btn {
  background: #4f46e5;
  color: white;
  border-color: #4f46e5;
}

/* Chat Window - Fixed position floating like Facebook Messenger or similar */
.chat-window {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 340px;
  height: 500px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  z-index: 1000;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.chat-header {
  padding: 12px 16px;
  background: #f8fafc;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.gift-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 4px 8px;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.gift-btn:hover {
  opacity: 1;
}

.avatar-small {
  width: 32px;
  height: 32px;
  font-size: 18px;
  background: #e2e8f0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.details {
  display: flex;
  flex-direction: column;
}

.details .name {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.2;
}

.details .status-text {
  font-size: 11px;
  color: #64748b;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  color: #94a3b8;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}
.close-btn:hover { color: #64748b; }

.chat-messages {
  flex: 1;
  padding: 12px 16px;
  overflow-y: auto;
  background: white;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.message-date {
  text-align: center;
  font-size: 12px;
  color: #94a3b8;
  margin: 8px 0;
  padding: 0 8px;
}

.message-bubble {
  display: flex;
  gap: 8px;
  align-items: flex-end;
  margin-bottom: 4px;
  animation: slideIn 0.3s ease-out;
}

.message-bubble.sent {
  flex-direction: row-reverse;
  justify-content: flex-start;
}

.message-bubble.received {
  flex-direction: row;
  justify-content: flex-start;
}

.bubble-content {
  max-width: 70%;
  padding: 8px 12px;
  border-radius: 12px;
  word-wrap: break-word;
  font-size: 13px;
  line-height: 1.4;
}

.message-bubble.sent .bubble-content {
  background: #3b82f6;
  color: white;
  border-bottom-right-radius: 4px;
}

.message-bubble.received .bubble-content {
  background: #e2e8f0;
  color: #1e293b;
  border-bottom-left-radius: 4px;
}

.bubble-time {
  font-size: 11px;
  color: #94a3b8;
  padding: 0 4px;
}

.empty-chat-state {
  text-align: center;
  font-size: 14px;
  color: #94a3b8;
  padding: 40px 20px;
}

/* System Messages - 系统消息样式 */
.system-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  margin: 8px 0;
  background: #f0f9ff;
  border-radius: 8px;
  border-left: 3px solid #0369a1;
  font-size: 13px;
  color: #1e293b;
}

.system-icon {
  font-size: 24px;
}

.system-content {
  text-align: center;
}

.system-time {
  font-size: 11px;
  color: #94a3b8;
}

/* 积分消息 */
.points-message {
  border-left-color: #f59e0b;
  background: #fffbeb;
}

.points-highlight {
  font-weight: 700;
  color: #f59e0b;
  font-size: 14px;
}

/* 邀请消息 */
.invite-message {
  border-left-color: #0284c7;
}

.invite-message.accepted {
  opacity: 0.6;
  background: #f1f5f9;
}

.invite-actions {
  display: flex;
  gap: 8px;
  width: 100%;
}

.invite-btn {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.accept-btn {
  background: #ecfdf5;
  color: #047857;
  border-color: #6ee7b7;
}

.accept-btn:hover:not(:disabled) {
  background: #d1fae5;
}

.reject-btn {
  background: #fef2f2;
  color: #dc2626;
  border-color: #fca5a5;
}

.reject-btn:hover:not(:disabled) {
  background: #fee2e2;
}

.invite-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.invite-accepted {
  text-align: center;
  font-size: 12px;
  color: #059669;
  font-weight: 600;
  padding: 8px 12px;
  background: #ecfdf5;
  border-radius: 6px;
}

/* Loading 状态 */
.messages-loading {
  text-align: center;
  padding: 20px;
  color: #64748b;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid #e2e8f0;
  border-top-color: #4f46e5;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.messages-error {
  text-align: center;
  padding: 16px;
  color: #991b1b;
  background: #fee2e2;
  border-radius: 6px;
  font-size: 13px;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.details .name {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.2;
}

.details .status-text {
  font-size: 11px;
  color: #64748b;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  color: #94a3b8;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}
.close-btn:hover { color: #64748b; }

/* Chat Actions - 底部功能按钮区域 */
.chat-actions {
  padding: 12px 16px;
  background: white;
  border-top: 1px solid #f1f5f9;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.actions-hint {
  text-align: center;
  font-size: 12px;
  color: #64748b;
  margin: 0 0 8px 0;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-btn {
  padding: 10px 16px;
  border-radius: 8px;
  border: none;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn .icon {
  font-size: 18px;
}

.action-btn .label {
  flex: 1;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.gift-action {
  background: linear-gradient(135deg, #fcd34d 0%, #f59e0b 100%);
  color: #92400e;
}

.gift-action:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px -1px rgba(245, 158, 11, 0.3);
}

.invite-action {
  background: linear-gradient(135deg, #93c5fd 0%, #60a5fa 100%);
  color: #0c4a6e;
}

.invite-action:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px -1px rgba(96, 165, 250, 0.3);
}

/* Transitions */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

/* Modal Overlay and Card */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.modal-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  width: 90%;
  max-width: 400px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 16px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}

.modal-body {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
}

.gift-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.recipient-info {
  margin: 0;
  font-size: 13px;
  color: #475569;
  padding: 12px;
  background: #f1f5f9;
  border-radius: 8px;
}

.error-message {
  padding: 12px;
  background: #fee2e2;
  color: #991b1b;
  border-radius: 8px;
  font-size: 13px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
}

.input-with-unit {
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-with-unit input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
}

.input-with-unit input:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.unit {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

.invitation-info {
  padding: 16px;
  background: #f0f9ff;
  border-radius: 8px;
  border-left: 3px solid #0369a1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  margin: 0;
  font-size: 13px;
  color: #475569;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-item .label {
  font-weight: 500;
  color: #1e293b;
}

.team-icon {
  font-size: 28px;
  display: inline-block;
}

.limit-info {
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  border-left: 3px solid #4f46e5;
}

.limit-info p {
  margin: 4px 0;
  font-size: 12px;
  color: #475569;
}

.limit-info .remaining strong {
  color: #4f46e5;
}

.limit-info .remaining .low {
  color: #ef4444;
  font-weight: 600;
}

.modal-footer {
  padding: 12px 16px;
  background: #f8fafc;
  border-top: 1px solid #f1f5f9;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.cancel-btn,
.confirm-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn {
  background: white;
  color: #475569;
  border: 1px solid #e2e8f0;
}

.cancel-btn:hover {
  background: #f1f5f9;
}

.confirm-btn {
  background: #4f46e5;
  color: white;
}

.confirm-btn:hover:not(:disabled) {
  background: #4338ca;
}

.confirm-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
  opacity: 0.6;
}

/* Mobile backdrop */
@media (max-width: 600px) {
  .friend-section {
    padding: 16px;
  }

  .header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .search-area {
    width: 100%;
  }

  .search-box input {
    padding-right: 84px;
  }

  .search-btn {
    min-width: 48px;
    height: 26px;
    font-size: 11px;
  }

  .search-error {
    font-size: 11px;
  }

  .chat-window {
    width: 100%;
    border-radius: 16px 16px 0 0;
    bottom: 0;
    right: 0;
    height: 60vh;
  }
}
</style>
