
<script setup>
import { reactive, ref, computed, nextTick } from 'vue'

const emailSearch = ref('')
const searchResult = ref(null)

// Mock friends data
const friends = reactive([
  { 
    id: 1, 
    nickname: 'Alice', 
    title: '问卷达人',
    avatar: '👩‍💻', 
    status: 'online',
    lastMessage: 'Hey there!'
  },
  { 
    id: 2, 
    nickname: 'Bob', 
    title: '数据分析师',
    avatar: '👨‍🔧', 
    status: 'offline',
    lastMessage: 'Project update?'
  },
  { 
    id: 3, 
    nickname: 'Charlie', 
    title: '心理学研究员',
    avatar: '🧠', 
    status: 'busy',
    lastMessage: 'Call you later.'
  },
  { 
    id: 4, 
    nickname: 'Diana', 
    title: '新人',
    avatar: '🌟', 
    status: 'online',
    lastMessage: 'Thanks for the invite!'
  },
])

// Chat State
const activeChatFriend = ref(null)
const chatInput = ref('')
const chatHistory = reactive({}) // Map: friendId -> messages[]

// Initialize some mock messages
chatHistory[1] = [
  { id: 1, sender: 'them', content: 'Hi! Have you seen the new survey?', time: '10:00' },
  { id: 2, sender: 'me', content: 'Yes, just finished it.', time: '10:05' }
]

function getChatMessages(friendId) {
  if (!chatHistory[friendId]) {
    chatHistory[friendId] = []
  }
  return chatHistory[friendId]
}

function openChat(friend) {
  activeChatFriend.value = friend
  // Scroll to bottom after opening
  nextTick(scrollToBottom)
}

function closeChat() {
  activeChatFriend.value = null
}

function sendMessage() {
  if (!chatInput.value.trim() || !activeChatFriend.value) return
  
  const friendId = activeChatFriend.value.id
  const msgs = getChatMessages(friendId)
  
  msgs.push({
    id: Date.now(),
    sender: 'me',
    content: chatInput.value,
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  })
  
  // Mock reply
  setTimeout(() => {
    msgs.push({
      id: Date.now() + 1,
      sender: 'them',
      content: `Auto-reply from ${activeChatFriend.value.nickname}: Received "${chatInput.value}"`,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    })
    nextTick(scrollToBottom)
  }, 1000)
  
  chatInput.value = ''
  nextTick(scrollToBottom)
}

function scrollToBottom() {
  const container = document.querySelector('.chat-messages')
  if (container) {
    container.scrollTop = container.scrollHeight
  }
}

function handleSearch() {
  if (!emailSearch.value) return
  // Mock search logic
  if (emailSearch.value.trim().length > 0) {
    // Check if friend exists
    const existing = friends.find(f => f.nickname.toLowerCase().includes(emailSearch.value.toLowerCase()))
    if(existing) {
        alert("Found existing friend: " + existing.nickname)
        openChat(existing);
        emailSearch.value = '';
    } else {
        alert("未找到好友 (Mock Search)");
    }
  }
}
</script>

<template>
  <div class="friend-section">
    <div class="header">
      <h2>我的好友 <span class="count">({{ friends.length }})</span></h2>
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input 
          v-model="emailSearch" 
          placeholder="搜索好友..." 
          @keyup.enter="handleSearch"
        />
      </div>
    </div>

    <!-- Friend Cards Grid -->
    <div class="friends-grid">
      <div 
        v-for="friend in friends" 
        :key="friend.id" 
        class="friend-card"
        @click="openChat(friend)"
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
        
        <div class="card-footer">
          <button class="chat-btn">
            <span class="icon">💬</span> 发消息
          </button>
        </div>
      </div>
      
      <!-- Add Friend Card (Optional placeholder) -->
      <div class="friend-card add-card" @click="handleSearch">
        <div class="add-icon">+</div>
        <span>添加好友</span>
      </div>
    </div>

    <!-- Chat Modal / Drawer -->
    <Transition name="slide-up">
      <div v-if="activeChatFriend" class="chat-window">
        <div class="chat-header">
          <div class="user-info">
            <div class="avatar-small">{{ activeChatFriend.avatar }}</div>
            <div class="details">
              <span class="name">{{ activeChatFriend.nickname }}</span>
              <span class="status-text">{{ activeChatFriend.status === 'online' ? '在线' : '离线' }}</span>
            </div>
          </div>
          <button class="close-btn" @click="closeChat">×</button>
        </div>
        
        <div class="chat-messages">
          <div class="message-date">Today</div>
          <div 
            v-for="msg in getChatMessages(activeChatFriend.id)" 
            :key="msg.id" 
            class="message-bubble"
            :class="{ 'sent': msg.sender === 'me', 'received': msg.sender === 'them' }"
          >
            <div class="bubble-content">{{ msg.content }}</div>
            <div class="bubble-time">{{ msg.time }}</div>
          </div>
          <div v-if="getChatMessages(activeChatFriend.id).length === 0" class="empty-chat-state">
            👋 打个招呼吧！
          </div>
        </div>
        
        <div class="chat-input-area">
          <input 
            v-model="chatInput" 
            placeholder="输入消息..." 
            @keyup.enter="sendMessage"
            autofocus
          />
          <button class="send-btn" @click="sendMessage">➤</button>
        </div>
      </div>
    </Transition>
    
    <!-- Backdrop for chat on mobile or specific designs -->
    <div v-if="activeChatFriend" class="chat-backdrop" @click="closeChat"></div>
  </div>
</template>

<style scoped>
.friend-section {
  padding: 24px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
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

.search-box {
  position: relative;
  width: 240px;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  font-size: 14px;
}

.search-box input {
  width: 100%;
  padding: 8px 12px 8px 32px;
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
  width: 320px;
  height: 400px;
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
  background: white;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8fafc;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
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
  padding: 16px;
  overflow-y: auto;
  background: white;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-date {
  text-align: center;
  font-size: 11px;
  color: #94a3b8;
  margin: 8px 0;
}

.message-bubble {
  max-width: 80%;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.4;
  position: relative;
}

.message-bubble.received {
  align-self: flex-start;
  background: #f1f5f9;
  color: #1e293b;
  border-bottom-left-radius: 4px;
}

.message-bubble.sent {
  align-self: flex-end;
  background: #4f46e5;
  color: white;
  border-bottom-right-radius: 4px;
}

.bubble-time {
  font-size: 10px;
  margin-top: 4px;
  opacity: 0.7;
  text-align: right;
}

.empty-chat-state {
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
  margin-top: auto;
  margin-bottom: auto;
}

.chat-input-area {
  padding: 12px;
  border-top: 1px solid #f1f5f9;
  display: flex;
  gap: 8px;
  background: white;
}

.chat-input-area input {
  flex: 1;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  padding: 8px 12px;
  font-size: 13px;
  outline: none;
}
.chat-input-area input:focus {
  border-color: #6366f1;
}

.send-btn {
  background: #4f46e5;
  color: white;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}
.send-btn:hover { background: #4338ca; }

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

/* Mobile backdrop */
@media (max-width: 600px) {
  .chat-window {
    width: 100%;
    border-radius: 16px 16px 0 0;
    bottom: 0;
    right: 0;
    height: 60vh;
  }
  .chat-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.3);
    z-index: 999;
  }
}
</style>
