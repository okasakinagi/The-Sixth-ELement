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

/**
 * 获取积分流水记录
 * GET /points/logs
 * @param {Object} params 查询参数
 * @param {string} params.type 筛选类型 (earn/spend)
 * @param {number} params.page 页码
 * @param {number} params.page_size 每页数量
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
    const error = await response.json();
    throw new Error(error.error || '获取积分记录失败');
  }

  return await response.json();
}

/**
 * 创建举报
 * POST /reports
 * @param {Object} data 举报数据
 * @param {string} data.target_type 举报目标类型 (survey/user)
 * @param {string} data.target_id 被举报对象ID
 * @param {string} data.reason 举报原因
 */
export async function createReport(data) {
  const token = getAuthToken();
  if (!token) {
    throw new Error('未登录，请先登录');
  }

  const response = await fetch(`${API_BASE_URL}/reports`, {
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
    if (response.status === 422) {
      const error = await response.json();
      throw new Error(JSON.stringify(error.error.details || error.error.message));
    }
    const error = await response.json();
    throw new Error(error.error || '提交举报失败');
  }

  return await response.json();
}
