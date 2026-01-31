/**
 * 认证辅助工具
 * 处理token过期、清除认证信息、重定向到登录页
 */

import { useRouter } from 'vue-router'

/**
 * 处理登录过期
 * 清除本地token和用户信息，显示提示后跳转到登录页
 */
export function handleTokenExpired(router) {
  // 清除所有认证相关的localStorage数据
  localStorage.removeItem('access_token')
  localStorage.removeItem('user_id')
  localStorage.removeItem('user_nickname')
  localStorage.removeItem('sixth_element_profile')

  // 显示提示对话框
  alert('您的登录已过期，请重新登录。')

  // 重定向到登录页
  router.replace({
    name: 'auth',
    query: { redirect: router.currentRoute.value.fullPath }
  })
}

/**
 * 全局响应拦截器 - 处理401错误
 * 在任何API调用前包装，统一处理token过期
 */
export async function fetchWithAuthCheck(url, options = {}, router) {
  try {
    const response = await fetch(url, options)

    // 如果响应是401（未授权），说明token过期
    if (response.status === 401) {
      handleTokenExpired(router)
      throw new Error('登录已过期')
    }

    return response
  } catch (error) {
    throw error
  }
}

/**
 * 获取认证token
 */
export function getAuthToken() {
  return localStorage.getItem('access_token')
}

/**
 * 检查是否已登录
 */
export function isAuthenticated() {
  return !!getAuthToken()
}

/**
 * 清除所有认证数据（不显示提示，用于主动登出）
 */
export function clearAuthData() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user_id')
  localStorage.removeItem('user_nickname')
  localStorage.removeItem('sixth_element_profile')
}

/**
 * 保存用户认证数据
 */
export function saveAuthData(token, user) {
  localStorage.setItem('access_token', token)
  if (user) {
    localStorage.setItem('user_id', user.id || '')
    localStorage.setItem('user_nickname', user.nickname || '')
  }
}
