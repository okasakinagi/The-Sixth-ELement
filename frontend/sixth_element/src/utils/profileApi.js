/**
 * API 工具 - 用户画像相关接口
 */

const API_BASE_URL = '/api/v1'

/**
 * 获取认证Token
 */
function getAuthToken() {
  return localStorage.getItem('access_token')
}

/**
 * 获取当前用户画像
 * GET /api/v1/users/me/profile
 */
export async function getUserProfile() {
  const token = getAuthToken()
  if (!token) {
    throw new Error('未登录，请先登录')
  }

  const response = await fetch(`${API_BASE_URL}/users/me/profile`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('登录已过期，请重新登录')
    }
    const error = await response.json()
    throw new Error(error.error || '获取画像失败')
  }

  return await response.json()
}

/**
 * 更新用户画像（部分更新）
 * PATCH /api/v1/users/me/profile
 */
export async function updateUserProfile(profileData) {
  const token = getAuthToken()
  if (!token) {
    throw new Error('未登录，请先登录')
  }

  const response = await fetch(`${API_BASE_URL}/users/me/profile`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(profileData),
  })

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('登录已过期，请重新登录')
    }
    if (response.status === 422) {
      const error = await response.json()
      throw new Error(JSON.stringify(error.error.details || error.error.message))
    }
    const error = await response.json()
    throw new Error(error.error || '更新画像失败')
  }

  return await response.json()
}

/**
 * 覆盖式更新用户画像
 * PUT /api/v1/users/me/profile
 */
export async function replaceUserProfile(profileData) {
  const token = getAuthToken()
  if (!token) {
    throw new Error('未登录，请先登录')
  }

  const response = await fetch(`${API_BASE_URL}/users/me/profile`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(profileData),
  })

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('登录已过期，请重新登录')
    }
    if (response.status === 422) {
      const error = await response.json()
      throw new Error(JSON.stringify(error.error.details || error.error.message))
    }
    const error = await response.json()
    throw new Error(error.error || '更新画像失败')
  }

  return await response.json()
}

/**
 * 获取当前用户基本信息
 * GET /api/v1/users/me
 */
export async function getCurrentUser() {
  const token = getAuthToken()
  if (!token) {
    throw new Error('未登录，请先登录')
  }

  const response = await fetch(`${API_BASE_URL}/users/me`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('登录已过期，请重新登录')
    }
    const error = await response.json()
    throw new Error(error.error || '获取用户信息失败')
  }

  return await response.json()
}

/**
 * 搜索匹配的用户画像
 * GET /api/v1/users/me/profile/matches
 */
export async function searchMatchingProfiles(criteria = {}) {
  const token = getAuthToken()
  if (!token) {
    throw new Error('未登录，请先登录')
  }

  const params = new URLSearchParams()
  if (criteria.college) params.append('college', criteria.college)
  if (criteria.major) params.append('major', criteria.major)
  if (criteria.mbti) params.append('mbti', criteria.mbti)
  if (criteria.min_completion) params.append('min_completion', criteria.min_completion)

  const url = `${API_BASE_URL}/users/me/profile/matches${params.toString() ? '?' + params.toString() : ''}`

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('登录已过期，请重新登录')
    }
    const error = await response.json()
    throw new Error(error.error || '搜索匹配失败')
  }

  return await response.json()
}
