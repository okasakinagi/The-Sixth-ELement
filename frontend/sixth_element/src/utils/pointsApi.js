/**
 * 积分 API 工具
 * 用于积分记录页面的API调用
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
 * 获取积分汇总信息
 * GET /points/summary
 */
export async function getPointsSummary() {
  const token = getAuthToken();
  if (!token) {
    throw new Error('未登录，请先登录');
  }

  const url = `${API_BASE_URL}/points/summary`;

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
    const error = await parseJsonResponse(response);
    throw new Error(error?.error || '获取积分汇总失败');
  }

  const data = await parseJsonResponse(response);
  if (!data) {
    throw new Error('服务返回空内容');
  }
  return data;
}

/**
 * 获取积分流水记录
 * GET /points/logs
 * @param {Object} params 查询参数
 * @param {string} params.type 筛选类型 (earn/spend)
 * @param {number} params.page 页码
 * @param {number} params.page_size 每页数量
 * @param {string} params.sort 排序方式 (time_asc/amount_asc/amount_desc)
 * @param {string} params.start_date 开始日期
 * @param {string} params.end_date 结束日期
 * @param {string} params.keyword 关键词搜索
 */
export async function getPointsLogs(params = {}) {
  const token = getAuthToken();
  if (!token) {
    throw new Error('未登录，请先登录');
  }

  const queryParams = new URLSearchParams();
  if (params.type) queryParams.append('type', params.type);
  if (params.page) queryParams.append('page', params.page);
  if (params.page_size) queryParams.append('page_size', params.page_size);
  if (params.sort) queryParams.append('sort', params.sort);
  if (params.start_date) queryParams.append('start_date', params.start_date);
  if (params.end_date) queryParams.append('end_date', params.end_date);
  if (params.keyword) queryParams.append('keyword', params.keyword);

  const url = `${API_BASE_URL}/points/logs${queryParams.toString() ? '?' + queryParams.toString() : ''}`;

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
      throw new Error('参数错误，请检查输入');
    }
    const error = await parseJsonResponse(response);
    throw new Error(error?.error || '获取积分记录失败');
  }

  const data = await parseJsonResponse(response);
  if (!data) {
    throw new Error('服务返回空内容');
  }
  return data;
}

/**
 * 更新积分
 * POST /points/update
 * @param {Object} data 积分变更数据
 * @param {number} data.delta 积分变更值（正数增加，负数减少）
 * @param {string} data.reason 变更原因
 * @param {string} data.ref_type 关联类型（如 survey_fill）
 * @param {string} data.ref_id 关联 ID
 */
export async function updatePoints(data) {
  const token = getAuthToken();
  if (!token) {
    throw new Error('未登录，请先登录');
  }

  const url = `${API_BASE_URL}/points/update`;
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('登录已过期，请重新登录');
    }
    if (response.status === 400) {
      const error = await parseJsonResponse(response);
      throw new Error(error?.error || '参数错误，请检查输入');
    }
    const error = await parseJsonResponse(response);
    throw new Error(error?.error || '更新积分失败');
  }
  
  const result = await parseJsonResponse(response);
  if (!result) {
    throw new Error('服务返回空内容');
  }
  return result;
}

/**
 * 获取积分趋势聚合数据
 * GET /points/trend
 * @param {Object} params 查询参数
 * @param {string} params.granularity 粒度 (day/week/month)
 * @param {number} params.days 天数范围
 */
export async function getPointsTrend(params = {}) {
  const token = getAuthToken();
  if (!token) {
    throw new Error('未登录，请先登录');
  }

  const queryParams = new URLSearchParams();
  if (params.granularity) queryParams.append('granularity', params.granularity);
  if (params.days) queryParams.append('days', params.days);

  const url = `${API_BASE_URL}/points/trend${queryParams.toString() ? '?' + queryParams.toString() : ''}`;

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
    const error = await parseJsonResponse(response);
    throw new Error(error?.error || '获取积分趋势失败');
  }

  const data = await parseJsonResponse(response);
  if (!data) {
    throw new Error('服务返回空内容');
  }
  return data;
}
