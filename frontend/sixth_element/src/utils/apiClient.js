/**
 * 统一的 API 请求工具
 * 集成了认证检查、错误处理、token过期检查等
 */

import { useRouter } from 'vue-router'

const API_BASE_URL = '/api/v1'

/**
 * 统一的 fetch 封装，自动处理token、错误等
 * @param {string} url API路径
 * @param {Object} options fetch选项
 * @param {Object} router Vue Router实例（用于重定向）
 * @returns {Promise} 响应数据
 */
export async function apiRequest(url, options = {}, router = null) {
  const token = localStorage.getItem('access_token')
  
  // 构建完整URL
  const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`
  
  // 合并请求头
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }
  
  // 如果有token，添加认证头
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  try {
    const response = await fetch(fullUrl, {
      ...options,
      headers,
    })
    
    // 处理401 - token过期
    if (response.status === 401) {
      // 清除认证数据
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_id')
      localStorage.removeItem('user_nickname')
      localStorage.removeItem('sixth_element_profile')
      
      // 如果有router实例，显示提示并跳转到登录页
      if (router) {
        alert('您的登录已过期，请重新登录。')
        router.replace({
          name: 'auth',
          query: { redirect: router.currentRoute.value.fullPath }
        })
      }
      
      throw new Error('登录已过期，请重新登录')
    }
    
    // 处理其他HTTP错误
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}`
      try {
        const errorData = await response.json()
        errorMessage = errorData.error || errorData.message || errorMessage
      } catch {
        // JSON解析失败，使用默认错误消息
      }
      throw new Error(errorMessage)
    }
    
    // 尝试解析JSON响应
    const data = await response.json()
    return data
  } catch (error) {
    // 重新抛出错误，让调用方处理
    throw error
  }
}

/**
 * GET请求
 */
export function get(url, router = null) {
  return apiRequest(url, { method: 'GET' }, router)
}

/**
 * POST请求
 */
export function post(url, data = {}, router = null) {
  return apiRequest(url, {
    method: 'POST',
    body: JSON.stringify(data),
  }, router)
}

/**
 * PATCH请求
 */
export function patch(url, data = {}, router = null) {
  return apiRequest(url, {
    method: 'PATCH',
    body: JSON.stringify(data),
  }, router)
}

/**
 * DELETE请求
 */
export function deleteRequest(url, router = null) {
  return apiRequest(url, { method: 'DELETE' }, router)
}
