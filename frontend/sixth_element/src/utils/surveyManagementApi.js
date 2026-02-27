/**
 * 问卷管理 API 工具
 * 用于问卷管理页面的API调用
 */

const API_BASE_URL = '/api/v1';

/**
 * 获取认证Token
 */
function getAuthToken() {
  return localStorage.getItem('access_token');
}

/**
 * 获取问卷列表
 * GET /surveys
 * @param {Object} params 查询参数
 * @param {string} params.status 筛选状态 (draft/live/paused/ended)
 * @param {string} params.keyword 按标题模糊搜索
 */
export async function getSurveys(params = {}) {
  const token = getAuthToken();
  if (!token) {
    throw new Error('未登录，请先登录');
  }

  const queryParams = new URLSearchParams();
  if (params.status) queryParams.append('status', params.status);
  if (params.keyword) queryParams.append('keyword', params.keyword);

  const url = `${API_BASE_URL}/surveys${queryParams.toString() ? '?' + queryParams.toString() : ''}`;

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
    const error = await response.json();
    throw new Error(error.error || '获取问卷列表失败');
  }

  return await response.json();
}

/**
 * 获取问卷统计摘要
 * GET /surveys/summary
 */
export async function getSurveysSummary() {
  const token = getAuthToken();
  if (!token) {
    throw new Error('未登录，请先登录');
  }

  const response = await fetch(`${API_BASE_URL}/surveys/summary`, {
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
    const error = await response.json();
    throw new Error(error.error || '获取问卷统计失败');
  }

  return await response.json();
}

/**
 * 删除问卷
 * DELETE /surveys/{survey_id}
 * @param {string} surveyId 问卷ID
 */
export async function deleteSurvey(surveyId) {
  const token = getAuthToken();
  if (!token) {
    throw new Error('未登录，请先登录');
  }

  const response = await fetch(`${API_BASE_URL}/surveys/${surveyId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('登录已过期，请重新登录');
    }
    if (response.status === 404) {
      throw new Error('问卷不存在');
    }
    const error = await response.json();
    throw new Error(error.error || '删除问卷失败');
  }

  return await response.json();
}

/**
 * 暂停投放问卷
 * POST /surveys/{survey_id}/pause
 * @param {string} surveyId 问卷ID
 */
export async function pauseSurvey(surveyId) {
  const token = getAuthToken();
  if (!token) {
    throw new Error('未登录，请先登录');
  }

  const response = await fetch(`${API_BASE_URL}/surveys/${surveyId}/pause`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('登录已过期，请重新登录');
    }
    if (response.status === 404) {
      throw new Error('问卷不存在');
    }
    if (response.status === 409) {
      throw new Error('状态冲突，无法暂停');
    }
    const error = await response.json();
    throw new Error(error.error || '暂停问卷失败');
  }

  return await response.json();
}

/**
 * 恢复投放问卷
 * POST /surveys/{survey_id}/resume
 * @param {string} surveyId 问卷ID
 */
export async function resumeSurvey(surveyId) {
  const token = getAuthToken();
  if (!token) {
    throw new Error('未登录，请先登录');
  }

  const response = await fetch(`${API_BASE_URL}/surveys/${surveyId}/resume`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('登录已过期，请重新登录');
    }
    if (response.status === 404) {
      throw new Error('问卷不存在');
    }
    if (response.status === 409) {
      throw new Error('状态冲突，无法恢复');
    }
    const error = await response.json();
    throw new Error(error.error || '恢复问卷失败');
  }

  return await response.json();
}

/**
 * 发布问卷
 * POST /surveys/{survey_id}/publish
 * @param {string} surveyId 问卷ID
 * @param {Object} data 发布数据
 * @param {number} data.budget_points 预算积分
 * @param {number} data.target 目标份数
 */
export async function publishSurvey(surveyId, data) {
  const token = getAuthToken();
  if (!token) {
    throw new Error('未登录，请先登录');
  }

  const response = await fetch(`${API_BASE_URL}/surveys/${surveyId}/publish`, {
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
    if (response.status === 404) {
      throw new Error('问卷不存在');
    }
    if (response.status === 422) {
      const error = await response.json();
      throw new Error(JSON.stringify(error.error.details || error.error.message));
    }
    const error = await response.json();
    throw new Error(error.error || '发布问卷失败');
  }

  return await response.json();
}

/**
 * 获取单个问卷详情
 * GET /surveys/{survey_id}
 * @param {string} surveyId 问卷ID
 */
export async function getSurveyDetail(surveyId) {
  const token = getAuthToken();
  if (!token) {
    throw new Error('未登录，请先登录');
  }

  const response = await fetch(`${API_BASE_URL}/surveys/${surveyId}`, {
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
    if (response.status === 404) {
      throw new Error('问卷不存在');
    }
    const error = await response.json();
    throw new Error(error.error || '获取问卷详情失败');
  }

  return await response.json();
}

/**
 * 创建问卷草稿
 * POST /surveys/drafts
 * @param {Object} data
 * @param {string} data.title 问卷标题
 * @param {string} data.subtitle 问卷副标题
 */
export async function createSurveyDraft(data) {
  const token = getAuthToken();
  if (!token) {
    throw new Error('未登录，请先登录');
  }

  const response = await fetch(`${API_BASE_URL}/surveys/drafts`, {
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
    const error = await response.json();
    throw new Error(error.error || '创建草稿失败');
  }

  return await response.json();
}

/**
 * AI 生成草稿题目
 * POST /surveys/drafts/{draft_id}/ai-generate
 * @param {string} draftId 草稿ID
 * @param {Object} data
 * @param {string} data.prompt 提示词
 * @param {number} data.question_count 题目数量
 */
export async function aiGenerateDraftQuestions(draftId, data) {
  const token = getAuthToken();
  if (!token) {
    throw new Error('未登录，请先登录');
  }

  const response = await fetch(`${API_BASE_URL}/surveys/drafts/${draftId}/ai-generate`, {
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
    const error = await response.json();
    throw new Error(error.error || 'AI 生成失败');
  }

  return await response.json();
}

/**
 * 评估问卷难度和预计时间
 * GET /surveys/{survey_id}/evaluate
 * @param {string} surveyId 问卷ID
 */
export async function evaluateSurvey(surveyId) {
  const token = getAuthToken();
  if (!token) {
    throw new Error('未登录，请先登录');
  }

  const response = await fetch(`${API_BASE_URL}/surveys/${surveyId}/evaluate`, {
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
    const error = await response.json();
    throw new Error(error.error || '评估问卷失败');
  }

  return await response.json();
}
