/**
 * 任务大厅 API 工具
 * 用于任务大厅页面的 API 调用
 */

import { get, post } from './apiClient'

/**
 * taskHall API - 使用统一的 `apiClient` 以便统一处理 401、token 清理与重定向
 */

/**
 * 获取任务大厅概览
 * GET /task-hall/overview
 */
export async function getTaskHallOverview(router = null) {
  return await get('/task-hall/overview', router)
}

/**
 * 获取任务列表
 * GET /task-hall/tasks
 */
export async function getTaskHallTasks(params = {}, router = null) {
  const queryParams = new URLSearchParams();
  if (params.keyword) queryParams.append('keyword', params.keyword);
  if (params.type) queryParams.append('type', params.type);
  if (params.difficulty !== undefined && params.difficulty !== null) {
    queryParams.append('difficulty', String(params.difficulty));
  }
  if (params.min_reward !== undefined && params.min_reward !== null) {
    queryParams.append('min_reward', String(params.min_reward));
  }
  if (params.max_minutes !== undefined && params.max_minutes !== null) {
    queryParams.append('max_minutes', String(params.max_minutes));
  }
  if (params.status) queryParams.append('status', params.status);
  if (params.sort) queryParams.append('sort', params.sort);
  if (params.page) queryParams.append('page', String(params.page));
  if (params.page_size) queryParams.append('page_size', String(params.page_size));

  const path = `/task-hall/tasks${queryParams.toString() ? '?' + queryParams.toString() : ''}`
  return await get(path, router)
}

/**
 * 换一批任务
 * POST /task-hall/batch/refresh
 */
export async function refreshTaskHallBatch(excludeTaskIds = [], batchSize = 15, router = null) {
  return await post('/task-hall/batch/refresh', { exclude_task_ids: excludeTaskIds, batch_size: batchSize }, router)
}


/**
 * 标记当前用户对某个问卷不感兴趣（后端会据此降低该问卷相关 tag 的权重）
 * POST /internal/similarity/dismiss
 */
export async function dismissSurvey(surveyId, router = null) {
  return await post('/internal/similarity/dismiss', { survey_id: surveyId }, router)
}


/**
 * 填写页面放弃填写时调用，减少用户-问卷相关 tag 权重
 * POST /internal/similarity/abandon
 */
export async function abandonBySurvey(surveyId, router = null) {
  return await post('/internal/similarity/abandon', { survey_id: surveyId }, router)
}

/**
 * 未登录访客获取随机任务列表（不调用 AI 推荐）
 * GET /task-hall/guest-tasks?size=N
 */
export async function getGuestTasks(size = 15) {
  const res = await fetch(`/api/v1/task-hall/guest-tasks?size=${encodeURIComponent(size)}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}
