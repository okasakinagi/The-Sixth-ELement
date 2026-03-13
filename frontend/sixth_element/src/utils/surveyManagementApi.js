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

const PUBLISH_ERROR_I18N_MAP = {
  'not enough points to publish survey': '积分不足，无法发布问卷',
  'survey must have at least one question before publish': '问卷至少需要 1 道题后才能发布',
  'survey cannot be published': '当前问卷状态不允许发布',
  'reward_points is required': '缺少每份奖励积分参数',
  'budget_points must be >= reward_points * target': '预算积分必须大于等于 每份奖励积分 × 目标份数',
  'budget_points must be a number': '预算积分必须是数字',
  'reward_points must be a number': '每份奖励积分必须是数字',
  'target must be a number': '目标份数必须是数字',
  'target must be >= 1': '目标份数必须大于等于 1',
};

function localizePublishErrorText(text) {
  const normalized = String(text || '').trim();
  if (!normalized) return normalized;
  const lower = normalized.toLowerCase();
  return PUBLISH_ERROR_I18N_MAP[lower] || normalized;
}

function normalizeApiErrorText(value) {
  if (value == null) return '';

  if (typeof value === 'string') {
    const text = value.trim();
    if (!text || text === '{}' || text === '[]' || text === 'null' || text === 'undefined') {
      return '';
    }
    return localizePublishErrorText(text);
  }

  if (Array.isArray(value)) {
    const parts = value
      .map((item) => normalizeApiErrorText(item))
      .filter(Boolean);
    return Array.from(new Set(parts)).join('；');
  }

  if (typeof value === 'object') {
    const entries = Object.entries(value)
      .map(([key, val]) => {
        const msg = normalizeApiErrorText(val);
        if (!msg) return '';
        return `${key}: ${msg}`;
      })
      .filter(Boolean);
    return Array.from(new Set(entries)).join('；');
  }

  return String(value);
}

function extractApiErrorMessage(payload, fallback) {
  if (!payload || typeof payload !== 'object') {
    return fallback;
  }

  const candidates = [
    payload?.error?.details,
    payload?.error?.message,
    payload?.error,
    payload?.details,
    payload?.detail,
    payload?.message,
  ];

  for (const candidate of candidates) {
    const msg = normalizeApiErrorText(candidate);
    if (msg) return msg;
  }

  return fallback;
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
 * @param {number} data.reward_points 每份奖励积分
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
    const errorPayload = await response.json().catch(() => ({}));

    if (response.status === 401) {
      throw new Error('登录已过期，请重新登录');
    }
    if (response.status === 404) {
      throw new Error('问卷不存在');
    }
    if (response.status === 422) {
      throw new Error(extractApiErrorMessage(errorPayload, '发布参数不合法，请检查后重试'));
    }
    throw new Error(extractApiErrorMessage(errorPayload, '发布问卷失败'));
  }

  return await response.json();
}

/**
 * 取消发布问卷（退还剩余积分但不退还加速积分）
 * POST /surveys/{survey_id}/cancel
 */
export async function cancelPublish(surveyId) {
  const token = getAuthToken();
  if (!token) {
    throw new Error('未登录，请先登录');
  }

  const response = await fetch(`${API_BASE_URL}/surveys/${surveyId}/cancel`, {
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
    const error = await response.json().catch(() => ({}));
    throw new Error(error.error || '取消发布失败');
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
 * 更新问卷草稿
 * PATCH /surveys/drafts/{draft_id}
 * @param {string} draftId 草稿ID
 * @param {Object} data 更新数据 { title, subtitle, questions }
 */
export async function updateDraft(draftId, data) {
  const token = getAuthToken();
  if (!token) {
    throw new Error('未登录，请先登录');
  }

  const response = await fetch(`${API_BASE_URL}/surveys/drafts/${draftId}`, {
    method: 'PATCH',
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
      throw new Error('草稿不存在');
    }
    const error = await response.json().catch(() => ({}));
    throw new Error(error.error || '保存草稿失败');
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
