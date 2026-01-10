# 接口文档（草案）

本接口文档用于问卷互填 App 的服务端 API 规划，默认采用 JSON 进行请求与响应。本文档为草案，可根据实际后端框架与鉴权方式调整。

## 约定
- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token（登录后获取）
- 时间格式：ISO 8601（例如 `2024-01-01T12:00:00Z`）

## 认证
### 登录
`POST /auth/login`

请求体：
```json
{
  "email": "user@example.com",
  "password": "password"
}
```

响应体：
```json
{
  "access_token": "token",
  "expires_in": 3600,
  "user": {
    "id": "u_123",
    "nickname": "Alice"
  }
}
```

### 注册
`POST /auth/register`

请求体：
```json
{
  "email": "user@example.com",
  "password": "password",
  "nickname": "Alice"
}
```

响应体：同登录

## 用户
### 获取当前用户
`GET /users/me`

响应体：
```json
{
  "id": "u_123",
  "nickname": "Alice",
  "credit_score": 80,
  "points": 120,
  "activity_points": 56
}
```

### 更新用户资料
`PATCH /users/me`

请求体：
```json
{
  "nickname": "Alice",
  "school": "某大学",
  "tags": ["心理学", "产品"]
}
```

响应体：更新后的用户信息

## 问卷
### 发布问卷
`POST /surveys`

请求体：
```json
{
  "title": "用户研究问卷",
  "description": "预计 5 分钟",
  "link": "https://example.com/form",
  "reward_points": 5,
  "deadline": "2024-12-31T23:59:59Z",
  "estimated_minutes": 5
}
```

响应体：
```json
{
  "id": "s_123",
  "status": "active"
}
```

### 获取问卷列表
`GET /surveys`

查询参数：
- `status`：`active` / `closed`
- `min_points`：最低奖励积分
- `max_minutes`：最大预计耗时
- `tags`：领域标签（逗号分隔）
- `page` / `page_size`

响应体：
```json
{
  "items": [
    {
      "id": "s_123",
      "title": "用户研究问卷",
      "reward_points": 5,
      "estimated_minutes": 5,
      "deadline": "2024-12-31T23:59:59Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 120
}
```

### 获取问卷详情
`GET /surveys/{id}`

响应体：
```json
{
  "id": "s_123",
  "title": "用户研究问卷",
  "description": "预计 5 分钟",
  "link": "https://example.com/form",
  "reward_points": 5,
  "estimated_minutes": 5,
  "deadline": "2024-12-31T23:59:59Z",
  "status": "active"
}
```

### 关闭问卷
`POST /surveys/{id}/close`

响应体：
```json
{
  "id": "s_123",
  "status": "closed"
}
```

## 填写记录
### 提交填写
`POST /surveys/{id}/fills`

请求体：
```json
{
  "duration_seconds": 260,
  "evidence": "截图或回执链接（可选）"
}
```

响应体：
```json
{
  "id": "f_456",
  "status": "pending",
  "points_awarded": 0
}
```

### 审核填写
`POST /fills/{id}/review`

请求体：
```json
{
  "status": "approved",
  "reason": ""
}
```

响应体：
```json
{
  "id": "f_456",
  "status": "approved",
  "points_awarded": 5
}
```

### 获取我的填写记录
`GET /fills/me`

查询参数：
- `status`：`pending` / `approved` / `rejected`
- `page` / `page_size`

响应体：
```json
{
  "items": [
    {
      "id": "f_456",
      "survey_id": "s_123",
      "status": "approved",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 12
}
```

## 积分
### 获取积分明细
`GET /points/logs`

查询参数：
- `type`：`earn` / `spend`
- `page` / `page_size`

响应体：
```json
{
  "items": [
    {
      "id": "p_789",
      "delta": 5,
      "reason": "完成问卷",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 42
}
```

## 举报
### 提交举报
`POST /reports`

请求体：
```json
{
  "target_type": "survey",
  "target_id": "s_123",
  "reason": "诱导填写"
}
```

响应体：
```json
{
  "id": "r_001",
  "status": "pending"
}
```

## 通用错误码（示例）
- `401` 未认证或 Token 过期
- `403` 权限不足
- `404` 资源不存在
- `422` 参数校验失败
- `429` 触发频率限制
- `500` 服务器内部错误

## 变更记录
- 2024-01-01：初始化版本
