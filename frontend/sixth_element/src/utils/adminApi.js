const API_BASE = '/api/v1/admin'

async function request(endpoint, options = {}) {
  const token = localStorage.getItem('admin_token')
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers,
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  })

  if (response.status === 401) {
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_user')
    window.location.href = '/admin/login'
    return null
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: '请求失败' }))
    console.error('API Error:', response.status, response.statusText, errorData)
    throw new Error(errorData.error || `请求失败 (${response.status})`)
  }

  return response.json()
}

export async function adminLogin(email, password) {
  return fetch(`${API_BASE}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  }).then(r => r.json())
}

export async function getDashboardStats() {
  return request('/dashboard/stats')
}

export async function getDashboardTrend(days = 7) {
  return request(`/dashboard/trend?days=${days}`)
}

export async function exportDashboard(days = 7) {
  return request(`/dashboard/export?days=${days}`)
}

export async function getUserList(page = 1, pageSize = 20, search = '', profileMin = '', profileMax = '') {
  let url = `/users?page=${page}&page_size=${pageSize}&search=${encodeURIComponent(search)}`
  if (profileMin !== '') url += `&profile_completion_min=${profileMin}`
  if (profileMax !== '') url += `&profile_completion_max=${profileMax}`
  return request(url)
}

export async function getUserDetail(userId) {
  return request(`/users/${userId}`)
}

export async function updateUserStatus(userId, status) {
  return request(`/users/${userId}/status`, {
    method: 'POST',
    body: JSON.stringify({ status }),
  })
}

export async function promoteUserToAdmin(userId) {
  return request(`/users/${userId}/promote-admin`, {
    method: 'POST',
  })
}

export async function updateUserInfo(userId, data) {
  return request(`/users/${userId}/info`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function deleteUser(userId) {
  return request(`/users/${userId}/delete`, {
    method: 'POST',
  })
}

export async function batchUpdateUserStatus(userIds, status) {
  return request(`/users/batch/status`, {
    method: 'POST',
    body: JSON.stringify({ user_ids: userIds, status }),
  })
}

export async function batchAdjustPoints(userIds, delta, reason = '管理员批量调整') {
  return request(`/users/batch/points`, {
    method: 'POST',
    body: JSON.stringify({ user_ids: userIds, delta, reason }),
  })
}

export async function getSurveyList(page = 1, pageSize = 20, status = '', search = '', startDate = '', endDate = '') {
  let url = `/surveys?page=${page}&page_size=${pageSize}`
  if (status) url += `&status=${status}`
  if (search) url += `&search=${encodeURIComponent(search)}`
  if (startDate) url += `&start_date=${startDate}`
  if (endDate) url += `&end_date=${endDate}`
  return request(url)
}

export async function getSurveyDetail(surveyId) {
  return request(`/surveys/${surveyId}`)
}

export async function createSurvey(data) {
  return request('/surveys/create', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateSurvey(surveyId, data) {
  return request(`/surveys/${surveyId}/update`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function deleteSurvey(surveyId) {
  return request(`/surveys/${surveyId}/delete`, {
    method: 'POST',
  })
}

export async function forceCloseSurvey(surveyId) {
  return request(`/surveys/${surveyId}/close`, {
    method: 'POST',
  })
}

export async function getRecommendAnalytics(days = 7) {
  return request(`/analytics/recommend?days=${days}`)
}

export async function getRecommendBehaviorEvents(days = 7, page = 1, pageSize = 20, eventType = '', scene = '') {
  let url = `/analytics/recommend/events?days=${days}&page=${page}&page_size=${pageSize}`
  if (eventType) url += `&event_type=${encodeURIComponent(eventType)}`
  if (scene) url += `&scene=${encodeURIComponent(scene)}`
  return request(url)
}

export async function getAiAnalytics(days = 7) {
  return request(`/analytics/ai?days=${days}`)
}

export async function getRiskControl(type = 'short_duration') {
  return request(`/risk?type=${type}`)
}

export async function getRiskRules() {
  return request('/risk/rules')
}

export async function createRiskRule(data) {
  return request('/risk/rules', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateRiskRule(ruleId, data) {
  return request(`/risk/rules/${ruleId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteRiskRule(ruleId) {
  return request(`/risk/rules/${ruleId}`, {
    method: 'DELETE',
  })
}

export async function toggleRiskRule(ruleId) {
  return request(`/risk/rules/${ruleId}/toggle`, {
    method: 'POST',
  })
}

export async function getAnnouncementList(page = 1, pageSize = 20) {
  return request(`/announcements?page=${page}&page_size=${pageSize}`)
}

export async function createAnnouncement(data) {
  return request('/announcements/create', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getOperationLogs(page = 1, pageSize = 20, action = '', targetType = '') {
  let url = `/operation_logs?page=${page}&page_size=${pageSize}`
  if (action) url += `&action=${encodeURIComponent(action)}`
  if (targetType) url += `&target_type=${encodeURIComponent(targetType)}`
  return request(url)
}

export async function getPendingSurveys(page = 1, pageSize = 20) {
  return request(`/surveys/pending?page=${page}&page_size=${pageSize}`)
}

export async function approveSurvey(surveyId) {
  return request(`/surveys/${surveyId}/approve`, {
    method: 'POST',
  })
}

export async function rejectSurvey(surveyId, reason) {
  return request(`/surveys/${surveyId}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  })
}

export function isAdminLoggedIn() {
  return !!localStorage.getItem('admin_token')
}

export function getAdminUser() {
  const user = localStorage.getItem('admin_user')
  return user ? JSON.parse(user) : null
}

export function adminLogout() {
  localStorage.removeItem('admin_token')
  localStorage.removeItem('admin_user')
}

export async function getNotificationList(page = 1, pageSize = 20, status = '') {
  let url = `/notifications?page=${page}&page_size=${pageSize}`
  if (status) url += `&status=${status}`
  return request(url)
}

export async function markNotificationRead(messageId) {
  return request(`/notifications/${messageId}/read`, {
    method: 'POST',
  })
}

export async function markAllNotificationsRead() {
  return request('/notifications/mark-all-read', {
    method: 'POST',
  })
}

export async function exportUsersData() {
  return request('/users/export')
}

export async function exportSurveysData() {
  return request('/surveys/export')
}
