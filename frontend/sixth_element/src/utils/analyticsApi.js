/**
 * Analytics API helpers
 * 数据分析模块的前端 API 工具函数
 */

const API_BASE = '/api/v1'

function getAuthToken() {
  return localStorage.getItem('access_token') || ''
}

/**
 * 获取问卷分析总览
 * GET /api/v1/surveys/{surveyId}/analytics/summary
 */
export async function getAnalyticsSummary(surveyId) {
  const res = await fetch(`${API_BASE}/surveys/${surveyId}/analytics/summary`, {
    headers: { Authorization: `Bearer ${getAuthToken()}` },
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || '获取总览数据失败')
  return data
}

/**
 * 获取各题统计数据
 * GET /api/v1/surveys/{surveyId}/analytics/questions?text_page=1&text_page_size=50
 */
export async function getAnalyticsQuestions(surveyId, textPage = 1, textPageSize = 50) {
  const url = `${API_BASE}/surveys/${surveyId}/analytics/questions?text_page=${textPage}&text_page_size=${textPageSize}`
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${getAuthToken()}` },
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || '获取题目统计失败')
  return data
}

/**
 * 下载导出文件（CSV 或 Excel），触发浏览器下载。
 * GET /api/v1/surveys/{surveyId}/analytics/export?format=csv|xlsx
 */
export async function downloadAnalyticsExport(surveyId, format, filename) {
  const res = await fetch(
    `${API_BASE}/surveys/${surveyId}/analytics/export?format=${format}`,
    { headers: { Authorization: `Bearer ${getAuthToken()}` } },
  )
  if (!res.ok) {
    let msg = '导出失败'
    try {
      const data = await res.json()
      msg = data.error || msg
    } catch (_) { /* ignore */ }
    throw new Error(msg)
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
