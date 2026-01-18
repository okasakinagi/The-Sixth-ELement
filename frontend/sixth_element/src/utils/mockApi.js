/**
 * Mock API - 本地模拟后端响应
 * 用于前端开发测试，无需真实后端
 */

// 模拟数据库中的用户
const mockUsers = {
  'test@example.com': {
    id: 'u_12345678',
    email: 'test@example.com',
    nickname: '测试用户',
    password: 'password123',
    credit_score: 85,
    points: 500,
    activity_points: 120,
  },
  'demo@qq.com': {
    id: 'u_87654321',
    email: 'demo@qq.com',
    nickname: '演示账号',
    password: '123456',
    credit_score: 92,
    points: 1200,
    activity_points: 350,
  },
}

/**
 * 模拟登录接口
 * POST /api/v1/auth/login
 */
export async function mockLogin(email, password) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const user = mockUsers[email]

      if (!user) {
        reject({
          error: '邮箱未注册',
          status: 401,
        })
        return
      }

      if (user.password !== password) {
        reject({
          error: '密码错误',
          status: 401,
        })
        return
      }

      // 登录成功
      const token = `mock_token_${Date.now()}`
      const response = {
        access_token: token,
        user: {
          id: user.id,
          email: user.email,
          nickname: user.nickname,
          credit_score: user.credit_score,
          points: user.points,
          activity_points: user.activity_points,
          has_honor: user.credit_score >= 85,
        },
      }

      resolve(response)
    }, 800) // 模拟网络延迟
  })
}

/**
 * 模拟注册接口
 * POST /api/v1/auth/register
 */
export async function mockRegister(email, nickname, password) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      // 检查邮箱是否已存在
      if (mockUsers[email]) {
        reject({
          error: '邮箱已被注册',
          status: 422,
        })
        return
      }

      // 创建新用户
      const newUser = {
        id: `u_${Math.random().toString(36).substr(2, 8)}`,
        email,
        nickname,
        password,
        credit_score: 80,
        points: 0,
        activity_points: 0,
      }

      // 保存到模拟数据库
      mockUsers[email] = newUser

      // 注册成功，自动返回登录状态
      const token = `mock_token_${Date.now()}`
      const response = {
        access_token: token,
        user: {
          id: newUser.id,
          email: newUser.email,
          nickname: newUser.nickname,
          credit_score: newUser.credit_score,
          points: newUser.points,
          activity_points: newUser.activity_points,
          has_honor: newUser.credit_score >= 85,
        },
      }

      resolve(response)
    }, 800)
  })
}

/**
 * 模拟获取当前用户信息
 * GET /api/v1/users/me
 */
export async function mockGetMe(token) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (!token) {
        reject({
          error: '未授权',
          status: 401,
        })
        return
      }

      // 从 token 中恢复用户信息（实际应该查询数据库）
      // 这里简单地返回第一个用户作为演示
      const user = Object.values(mockUsers)[0]

      resolve({
        id: user.id,
        email: user.email,
        nickname: user.nickname,
        credit_score: user.credit_score,
        points: user.points,
        activity_points: user.activity_points,
        has_honor: user.credit_score >= 85,
      })
    }, 400)
  })
}

/**
 * 模拟获取积分记录
 * GET /api/v1/points/logs
 */
export async function mockPointsLogs(token, type = null) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const logs = [
        {
          id: 'log_001',
          type: 'earn',
          reason: '完成问卷《校园生活满意度调查》',
          amount: 50,
          delta: 50,
          created_at: '2026-01-15T14:30:00Z',
          related_id: 'survey_001',
          related_type: 'survey_fill',
        },
        {
          id: 'log_002',
          type: 'spend',
          reason: '发布问卷《餐饮偏好调查》',
          amount: 30,
          delta: -30,
          created_at: '2026-01-14T10:15:00Z',
          related_id: 'survey_002',
          related_type: 'survey_publish',
        },
        {
          id: 'log_003',
          type: 'earn',
          reason: '完成问卷《课程评价调查》',
          amount: 60,
          delta: 60,
          created_at: '2026-01-13T16:45:00Z',
          related_id: 'survey_003',
          related_type: 'survey_fill',
        },
        {
          id: 'log_004',
          type: 'earn',
          reason: '完成问卷《宿舍满意度调查》',
          amount: 40,
          delta: 40,
          created_at: '2026-01-12T09:20:00Z',
          related_id: 'survey_004',
          related_type: 'survey_fill',
        },
        {
          id: 'log_005',
          type: 'spend',
          reason: '发布问卷《运动习惯调查》',
          amount: 50,
          delta: -50,
          created_at: '2026-01-11T13:00:00Z',
          related_id: 'survey_005',
          related_type: 'survey_publish',
        },
      ]

      // 按类型筛选
      let filtered = logs
      if (type === 'earn') {
        filtered = logs.filter((log) => log.delta > 0)
      } else if (type === 'spend') {
        filtered = logs.filter((log) => log.delta < 0)
      }

      resolve({
        logs: filtered,
        total: filtered.length,
      })
    }, 500)
  })
}

/**
 * 模拟获取问卷列表
 * GET /api/v1/surveys
 */
export async function mockSurveys(token) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const surveys = [
        {
          id: 'survey_101',
          title: '校园食堂满意度调查',
          description: '帮助我们了解你对校园食堂的看法',
          reward_points: 50,
          deadline: '2026-02-15',
          status: 'active',
          estimated_minutes: 5,
          owner: '教务处',
        },
        {
          id: 'survey_102',
          title: '宿舍管理反馈问卷',
          description: '你的意见对我们很重要',
          reward_points: 40,
          deadline: '2026-02-10',
          status: 'active',
          estimated_minutes: 8,
          owner: '学生事务',
        },
        {
          id: 'survey_103',
          title: '课程质量评价',
          description: '评价你所学课程的质量',
          reward_points: 60,
          deadline: '2026-02-20',
          status: 'active',
          estimated_minutes: 10,
          owner: '教学部门',
        },
      ]

      resolve({
        surveys,
        total: surveys.length,
      })
    }, 400)
  })
}

/**
 * 模拟获取单个问卷详情
 * GET /api/v1/surveys/:id
 */
export async function mockGetSurvey(token, surveyId) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const surveys = {
        survey_001: {
          id: 'survey_001',
          title: '校园生活满意度调查',
          description: '我们想了解你对校园生活各方面的满意度',
          owner_id: 'u_99999999',
          owner_name: '学生会',
          link: 'https://form.example.com/survey_001',
          reward_points: 50,
          deadline: '2026-02-15T23:59:59Z',
          status: 'active',
          estimated_minutes: 5,
          created_at: '2026-01-10T10:00:00Z',
        },
        survey_002: {
          id: 'survey_002',
          title: '餐饮偏好调查',
          description: '帮助改进校园餐饮服务',
          owner_id: 'u_12345678',
          owner_name: '测试用户',
          link: 'https://form.example.com/survey_002',
          reward_points: 30,
          deadline: '2026-02-10T23:59:59Z',
          status: 'active',
          estimated_minutes: 3,
          created_at: '2026-01-14T15:00:00Z',
        },
      }

      const survey = surveys[surveyId]

      if (!survey) {
        reject({
          error: '问卷不存在',
          status: 404,
        })
        return
      }

      resolve(survey)
    }, 300)
  })
}

/**
 * 启用 Mock API 拦截器
 * 将在全局 fetch 之前运行，自动拦截 /api/v1 请求
 */
export function enableMockApi() {
  const originalFetch = window.fetch

  window.fetch = function (url, options = {}) {
    // 只拦截 /api/v1 请求
    if (!url.includes('/api/v1/')) {
      return originalFetch.call(window, url, options)
    }

    const method = options.method || 'GET'
    const body = options.body ? JSON.parse(options.body) : {}
    const token = options.headers?.Authorization?.replace('Bearer ', '')

    // 登录接口
    if (url.includes('/auth/login') && method === 'POST') {
      return mockLogin(body.email, body.password)
        .then((data) =>
          Promise.resolve(
            new Response(JSON.stringify(data), {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            })
          )
        )
        .catch((error) =>
          Promise.resolve(
            new Response(JSON.stringify(error), {
              status: error.status || 400,
              headers: { 'Content-Type': 'application/json' },
            })
          )
        )
    }

    // 注册接口
    if (url.includes('/auth/register') && method === 'POST') {
      return mockRegister(body.email, body.nickname, body.password)
        .then((data) =>
          Promise.resolve(
            new Response(JSON.stringify(data), {
              status: 201,
              headers: { 'Content-Type': 'application/json' },
            })
          )
        )
        .catch((error) =>
          Promise.resolve(
            new Response(JSON.stringify(error), {
              status: error.status || 400,
              headers: { 'Content-Type': 'application/json' },
            })
          )
        )
    }

    // 获取当前用户
    if (url.includes('/users/me') && method === 'GET') {
      return mockGetMe(token)
        .then((data) =>
          Promise.resolve(
            new Response(JSON.stringify(data), {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            })
          )
        )
        .catch((error) =>
          Promise.resolve(
            new Response(JSON.stringify(error), {
              status: error.status || 400,
              headers: { 'Content-Type': 'application/json' },
            })
          )
        )
    }

    // 获取积分记录
    if (url.includes('/points/logs') && method === 'GET') {
      const type = new URL(url).searchParams.get('type')
      return mockPointsLogs(token, type)
        .then((data) =>
          Promise.resolve(
            new Response(JSON.stringify(data), {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            })
          )
        )
        .catch((error) =>
          Promise.resolve(
            new Response(JSON.stringify(error), {
              status: error.status || 400,
              headers: { 'Content-Type': 'application/json' },
            })
          )
        )
    }

    // 获取问卷列表
    if (url.includes('/surveys') && method === 'GET' && !url.includes('/surveys/')) {
      return mockSurveys(token)
        .then((data) =>
          Promise.resolve(
            new Response(JSON.stringify(data), {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            })
          )
        )
        .catch((error) =>
          Promise.resolve(
            new Response(JSON.stringify(error), {
              status: error.status || 400,
              headers: { 'Content-Type': 'application/json' },
            })
          )
        )
    }

    // 获取单个问卷
    if (url.includes('/surveys/') && method === 'GET') {
      const surveyId = url.split('/surveys/')[1]
      return mockGetSurvey(token, surveyId)
        .then((data) =>
          Promise.resolve(
            new Response(JSON.stringify(data), {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            })
          )
        )
        .catch((error) =>
          Promise.resolve(
            new Response(JSON.stringify(error), {
              status: error.status || 400,
              headers: { 'Content-Type': 'application/json' },
            })
          )
        )
    }

    // 未处理的请求，返回 404
    return Promise.resolve(
      new Response(JSON.stringify({ error: '接口不存在' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      })
    )
  }

  console.log('✅ Mock API 已启用 - 所有 /api/v1 请求将被本地模拟')
}
