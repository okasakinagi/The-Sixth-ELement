/**
 * 任务大厅 API 工具
 */

import { get, post } from './apiClient'

/**
 * 获取任务大厅概览
 * GET /task-hall/overview
 */
export function getTaskHallOverview(router = null) {
  return get('/task-hall/overview', router)
}

/**
 * 获取任务列表
 * GET /task-hall/tasks
 */
export function getTaskHallTasks(params = {}, router = null) {
  const query = new URLSearchParams()
  if (params.keyword) query.append('keyword', params.keyword)
  if (params.type) query.append('type', params.type)
  if (params.difficulty !== undefined && params.difficulty !== null) {
    query.append('difficulty', String(params.difficulty))
  }
  if (params.min_reward !== undefined && params.min_reward !== null) {
    query.append('min_reward', String(params.min_reward))
  }
  if (params.max_minutes !== undefined && params.max_minutes !== null) {
    query.append('max_minutes', String(params.max_minutes))
  }
  if (params.status) query.append('status', params.status)
  if (params.sort) query.append('sort', params.sort)
  if (params.page) query.append('page', String(params.page))
  if (params.page_size) query.append('page_size', String(params.page_size))

  const suffix = query.toString() ? `?${query.toString()}` : ''
  return get(`/task-hall/tasks${suffix}`, router)
}

/**
 * 换一批任务
 * POST /task-hall/batch/refresh
 */
export function refreshTaskHallBatch(excludeTaskIds = [], batchSize = 15, router = null) {
  return post(
    '/task-hall/batch/refresh',
    {
      exclude_task_ids: excludeTaskIds,
      batch_size: batchSize,
    },
    router
  )
}
