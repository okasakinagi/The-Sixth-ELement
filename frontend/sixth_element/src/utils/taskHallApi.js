/**
 * 任务大厅 API 工具
 * 用于任务大厅页面的 API 调用
 */

const API_BASE_URL = '/api/v1';

/**
 * 获取认证Token
 */
function getAuthToken() {
  return localStorage.getItem('access_token');
}

async function parseJsonResponse(response) {
  const raw = await response.text();
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch (error) {
    throw new Error('服务返回了非 JSON 内容');
  }
}

/**
 * 获取任务大厅概览
 * GET /task-hall/overview
 */
export async function getTaskHallOverview() {
  const token = getAuthToken();
  if (!token) {
    throw new Error('未登录，请先登录');
  }

  const response = await fetch(`${API_BASE_URL}/task-hall/overview`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('登录已过期，请重新登录');
    }
    const error = await parseJsonResponse(response);
    throw new Error(error?.error || '获取任务大厅概览失败');
  }

  const data = await parseJsonResponse(response);
  if (!data) {
    throw new Error('服务返回空内容');
  }
  return data;
}

/**
 * 获取任务列表
 * GET /task-hall/tasks
 */
export async function getTaskHallTasks(params = {}) {
  const token = getAuthToken();
  if (!token) {
    throw new Error('未登录，请先登录');
  }

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

  const url = `${API_BASE_URL}/task-hall/tasks${queryParams.toString() ? '?' + queryParams.toString() : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('登录已过期，请重新登录');
    }
    if (response.status === 422) {
      throw new Error('参数错误，请检查筛选条件');
    }
    const error = await parseJsonResponse(response);
    throw new Error(error?.error || '获取任务列表失败');
  }

  const data = await parseJsonResponse(response);
  if (!data) {
    throw new Error('服务返回空内容');
  }
  return data;
}

/**
 * 换一批任务
 * POST /task-hall/batch/refresh
 */
export async function refreshTaskHallBatch(excludeTaskIds = [], batchSize = 15) {
  const token = getAuthToken();
  if (!token) {
    throw new Error('未登录，请先登录');
  }

  const response = await fetch(`${API_BASE_URL}/task-hall/batch/refresh`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      exclude_task_ids: excludeTaskIds,
      batch_size: batchSize,
    }),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('登录已过期，请重新登录');
    }
    if (response.status === 422) {
      throw new Error('参数错误，请检查请求内容');
    }
    const error = await parseJsonResponse(response);
    throw new Error(error?.error || '换一批任务失败');
  }

  const data = await parseJsonResponse(response);
  if (!data) {
    throw new Error('服务返回空内容');
  }
  return data;
}


/**
 * 标记当前用户对某个问卷不感兴趣（后端会据此降低该问卷相关 tag 的权重）
 * POST /internal/similarity/dismiss
 */
export async function dismissSurvey(surveyId) {
  const token = getAuthToken();
  if (!token) {
    throw new Error('未登录，请先登录');
  }

  const response = await fetch(`${API_BASE_URL}/internal/similarity/dismiss`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ survey_id: surveyId }),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('登录已过期，请重新登录');
    }
    const error = await parseJsonResponse(response);
    throw new Error(error?.error || '请求失败');
  }

  return await parseJsonResponse(response);
}


/**
 * 填写页面放弃填写时调用，减少用户-问卷相关 tag 权重
 * POST /internal/similarity/abandon
 */
export async function abandonBySurvey(surveyId) {
  const token = getAuthToken();
  if (!token) {
    throw new Error('未登录，请先登录');
  }

  const response = await fetch(`${API_BASE_URL}/internal/similarity/abandon`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ survey_id: surveyId }),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('登录已过期，请重新登录');
    }
    const error = await parseJsonResponse(response);
    throw new Error(error?.error || '请求失败');
  }

  return await parseJsonResponse(response);
}
