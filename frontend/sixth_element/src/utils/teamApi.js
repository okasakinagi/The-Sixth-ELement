/**
 * 团队/组队 API 工具
 * 用于团队管理、邀请、积分赠送等功能
 */

import { apiRequest } from './apiClient'

/**
 * ============ 团队基础操作 ============
 */

/**
 * 创建新团队
 * POST /teams
 * @param {Object} data - { title, description, max_members }
 */
export async function createTeam(data) {
  return apiRequest('/teams', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * 获取团队详情
 * GET /teams/{team_id}
 * @param {number} teamId - 团队ID
 */
export async function getTeamDetail(teamId) {
  return apiRequest(`/teams/${teamId}`, {
    method: 'GET',
  })
}

/**
 * 获取当前用户的团队（单团队模式）
 * GET /teams/mine
 * ★ Phase 2: 单队伍模式 - 返回用户唯一的团队
 */
export async function getMyTeam() {
  return apiRequest(`/teams/mine`, {
    method: 'GET',
  })
}

/**
 * 更新团队信息
 * PUT /teams/{team_id}
 * @param {number} teamId - 团队ID
 * @param {Object} data - { title, description, max_members }
 */
export async function updateTeam(teamId, data) {
  return apiRequest(`/teams/${teamId}/update`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

/**
 * 删除（解散）团队
 * DELETE /teams/{team_id}
 * @param {number} teamId - 团队ID
 */
export async function deleteTeam(teamId) {
  return apiRequest(`/teams/${teamId}/delete`, {
    method: 'DELETE',
  })
}

/**
 * ============ 团队成员管理 ============
 */

/**
 * 获取团队成员列表
 * GET /teams/{team_id}/members
 * @param {number} teamId - 团队ID
 */
export async function getTeamMembers(teamId) {
  return apiRequest(`/teams/${teamId}/members`, {
    method: 'GET',
  })
}

/**
 * 从团队移除成员
 * DELETE /teams/{team_id}/members/{user_id}
 * @param {number} teamId - 团队ID
 * @param {number} userId - 用户ID
 */
export async function removeTeamMember(teamId, userId) {
  return apiRequest(`/teams/${teamId}/members/${userId}/remove`, {
    method: 'DELETE',
  })
}

/**
 * 设置队伍成员角色（仅队长）
 * PATCH /teams/{team_id}/members/{user_id}/role
 * @param {number} teamId - 团队ID
 * @param {number} userId - 用户ID
 * @param {'admin' | 'member'} role - 目标角色
 */
export async function setTeamMemberRole(teamId, userId, role) {
  return apiRequest(`/teams/${teamId}/members/${userId}/role`, {
    method: 'PATCH',
    body: JSON.stringify({ role }),
  })
}

/**
 * ============ 邀请相关 ============
 */

/**
 * 发送团队邀请
 * POST /teams/{team_id}/invite
 * @param {number} teamId - 团队ID
 * @param {number} inviteeId - 邀请人的ID
 */
export async function sendTeamInvitation(teamId, inviteeId) {
  return apiRequest(`/teams/${teamId}/invite`, {
    method: 'POST',
    body: JSON.stringify({ invitee_id: inviteeId }),
  })
}

/**
 * 检查邀请冷却状态
 * GET /teams/{team_id}/invite/{invitee_id}/cooldown
 * @param {number} teamId - 团队ID
 * @param {number} inviteeId - 邀请人的ID
 * @returns {Object} { need_wait, wait_minutes, wait_until } (仅当需要等待时)
 */
export async function checkInvitationCooldown(teamId, inviteeId) {
  return apiRequest(
    `/teams/${teamId}/invite/${inviteeId}/cooldown`,
    {
      method: 'GET',
    }
  )
}

/**
 * 获取当前用户的待处理邀请列表
 * GET /teams/invitations/pending
 */
export async function getPendingInvitations() {
  return apiRequest(`/invitations`, {
    method: 'GET',
  })
}

/**
 * 接受邀请
 * PATCH /teams/invitations/{invitation_id}/accept
 * @param {number} invitationId - 邀请ID
 */
export async function acceptInvitation(invitationId) {
  return apiRequest(`/invitations/${invitationId}/accept`, {
    method: 'PATCH',
  })
}

/**
 * 拒绝邀请
 * DELETE /teams/invitations/{invitation_id}
 * @param {number} invitationId - 邀请ID
 */
export async function rejectInvitation(invitationId) {
  return apiRequest(`/invitations/${invitationId}/reject`, {
    method: 'PATCH',
  })
}

/**
 * ============ 消息相关 ============
 */

/**
 * 获取用户的所有消息（包括邀请、积分赠送等）
 * GET /messages
 * @param {Object} options - { message_type, limit, offset }
 */
export async function getMessages(options = {}) {
  const params = new URLSearchParams()
  if (options.message_type) {
    // 后端当前读取 type；同时保留 message_type 便于兼容。
    params.append('type', options.message_type)
    params.append('message_type', options.message_type)
  }

  if (options.page_size) {
    params.append('page_size', options.page_size)
  } else if (options.limit) {
    params.append('page_size', options.limit)
  }

  if (options.page) {
    params.append('page', options.page)
  } else if (options.offset !== undefined && options.limit) {
    const page = Math.floor(options.offset / options.limit) + 1
    params.append('page', String(page))
  }

  const query = params.toString()
  const url = query ? `/messages?${query}` : `/messages`

  return apiRequest(url, {
    method: 'GET',
  })
}

/**
 * 获取未读消息数量
 * GET /messages/unread-count
 */
export async function getUnreadMessageCount() {
  return apiRequest(`/messages/unread-count`, {
    method: 'GET',
  })
}

/**
 * 标记消息为已读
 * PUT /messages/{message_id}/read
 * @param {number} messageId - 消息ID
 */
export async function markMessageAsRead(messageId) {
  return apiRequest(`/messages/${messageId}/read`, {
    method: 'PATCH',
  })
}

/**
 * 删除消息
 * DELETE /messages/{message_id}
 * @param {number} messageId - 消息ID
 */
export async function deleteMessage(messageId) {
  return apiRequest(`/messages/${messageId}/delete`, {
    method: 'DELETE',
  })
}

/**
 * ============ 积分赠送 ============
 */

/**
 * 获取积分赠送限制信息
 * GET /messages/points-gift/limit
 * @returns {Object} { limit, sent_today, remaining }
 */
export async function getPointsGiftLimitInfo() {
  return apiRequest(`/messages/points-gift/limit`, {
    method: 'GET',
  })
}

/**
 * 赠送积分给用户
 * POST /messages/points-gift
 * @param {Object} data - { recipient_id, amount }
 */
export async function sendPointsGift(data) {
  const payload = {
    receiver_id: data?.receiver_id ?? data?.recipient_id,
    points_amount: data?.points_amount ?? data?.amount,
    message: data?.message ?? '',
  }

  return apiRequest(`/messages/points-gift`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

/**
 * ============ 用户搜索 ============
 */

/**
 * 通过邮箱搜索用户
 * GET /users/search?email={email}
 * @param {string} email - 用户邮箱
 * @returns {Object} { id, nickname, email, points }
 */
export async function searchUserByEmail(email) {
  return apiRequest(`/users/search?email=${encodeURIComponent(email)}`, {
    method: 'GET',
  })
}

/**
 * 格式化冷却时间显示
 * @param {Object} cooldownInfo - { need_wait, wait_minutes, wait_until }
 * @returns {string} 格式化的等待时间文本
 */
export function formatCooldownTime(cooldownInfo) {
  if (!cooldownInfo.need_wait) {
    return '可以邀请'
  }

  const { wait_minutes } = cooldownInfo
  if (wait_minutes <= 0) {
    return '可以邀请'
  }

  if (wait_minutes < 60) {
    return `需等待 ${wait_minutes} 分钟`
  }

  const hours = Math.floor(wait_minutes / 60)
  const mins = wait_minutes % 60
  if (mins === 0) {
    return `需等待 ${hours} 小时`
  }

  return `需等待 ${hours} 小时 ${mins} 分钟`
}

/**
 * 计算倒计时剩余时间（秒）
 * @param {string|number} waitUntil - 等待截止时间戳或ISO时间字符串
 * @returns {number} 剩余秒数，0表示已截止
 */
export function calculateCountdownSeconds(waitUntil) {
  const now = Date.now()
  const targetTime = new Date(waitUntil).getTime()
  const diffMs = targetTime - now

  return Math.max(0, Math.ceil(diffMs / 1000))
}

/**
 * 格式化剩余积分赠送额度
 * @param {Object} limitInfo - { limit, sent_today, remaining }
 * @returns {string} 格式化的显示文本
 */
export function formatPointsGiftRemaining(limitInfo) {
  const { limit, remaining } = limitInfo
  if (!limit) {
    return '积分赠送已关闭'
  }

  if (remaining <= 0) {
    return '今日赠送已达上限'
  }

  return `今日还可赠送 ${remaining} 积分（上限 ${limit}）`
}
