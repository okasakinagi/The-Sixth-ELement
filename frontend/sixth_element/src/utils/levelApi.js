/**
 * 等级与任务 API
 */
import { get, post } from './apiClient'

/** GET /user/level — 查询当前等级/EXP/称号 */
export async function getUserLevel(router = null) {
  return await get('/user/level', router)
}

/** GET /tasks/daily — 今日任务列表 */
export async function getDailyTasks(router = null) {
  return await get('/tasks/daily', router)
}

/** GET /tasks/weekly — 本周任务列表 */
export async function getWeeklyTasks(router = null) {
  return await get('/tasks/weekly', router)
}

/** POST /tasks/:code/claim — 领取任务奖励 */
export async function claimTask(taskCode, router = null) {
  return await post(`/tasks/${taskCode}/claim`, {}, router)
}
