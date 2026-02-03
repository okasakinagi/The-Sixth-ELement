/**
 * 用户积分工具函数
 * 统一管理用户积分的获取和更新
 */

/**
 * 从 localStorage 获取用户积分
 * @returns {number} 用户积分，默认返回 0
 */
export function getUserPoints() {
  try {
    const profile = localStorage.getItem('sixth_element_profile')
    if (profile) {
      const userData = JSON.parse(profile)
      return userData.points || 0
    }
  } catch (error) {
    console.error('读取用户积分失败:', error)
  }
  return 0
}

/**
 * 更新 localStorage 中的用户积分
 * @param {number} points 新的积分值
 */
export function updateUserPoints(points) {
  try {
    const profile = localStorage.getItem('sixth_element_profile')
    if (profile) {
      const userData = JSON.parse(profile)
      userData.points = points
      localStorage.setItem('sixth_element_profile', JSON.stringify(userData))
    }
  } catch (error) {
    console.error('更新用户积分失败:', error)
  }
}
