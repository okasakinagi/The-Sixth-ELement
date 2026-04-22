# 个人界面 API

本文档描述账号基础信息、用户画像和画像匹配接口。当前实现把基础账号信息、个人画像和画像摘要分成了三个独立入口。

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：`Authorization: Bearer <access_token>`
- 时间格式：ISO 8601

## 1. 基础账号信息

### 获取当前用户

`GET /users/me`

响应示例：

```json
{
  "id": "1",
  "nickname": "Alice",
  "credit_score": 80,
  "points": 120,
  "activity_points": 56,
  "has_honor": false
}
```

说明：

- 这里只返回账号层字段。
- `has_honor` 按 `credit_score >= 85` 计算。

### 更新当前用户

`PATCH /users/me`

请求体：

```json
{
  "nickname": "Alice2026",
  "school": "X大学",
  "tags": ["心理学", "产品", "设计"]
}
```

说明：

- `nickname` 直接更新昵称。
- `school` 和 `tags` 由后端映射为标签系统字段。

### 通过邮箱搜索用户

`GET /users/search?email=alice@example.com`

说明：

- 仅支持精确邮箱搜索。
- 不能搜索自己。

响应示例：

```json
{
  "id": "2",
  "nickname": "Bob",
  "email": "bob@example.com",
  "points": 88
}
```

## 2. 用户画像

### 获取当前用户画像

`GET /users/me/profile`

响应示例：

```json
{
  "user_id": 1,
  "gender": "female",
  "age": 20,
  "grade": "大二",
  "college": "计算机学院",
  "major": "计算机科学与技术",
  "mbti": "INTJ",
  "interests": ["人工智能", "德语"],
  "organizations": ["学生会"],
  "consumption_preferences": ["数码", "奶茶"],
  "career_intention": ["大厂"],
  "skills": ["Python"],
  "current_status": "备战期末",
  "profile_completion": 67,
  "updated_at": "2026-01-01T12:00:00Z"
}
```

### 部分更新画像

`PATCH /users/me/profile`

说明：

- 只更新传入字段，未传字段保持不变。
- 支持 `careerIntention`、`consumptionPreferences`、`currentStatus` 等 camelCase 兼容字段。

### 完整替换画像

`PUT /users/me/profile`

说明：

- 先清空同类标签，再按请求体重建。
- 适合“整页保存”场景。

## 3. 画像匹配

### 获取匹配画像列表

`GET /users/me/profile/matches`

可选查询参数：

- `college`
- `major`
- `mbti`
- `min_completion`

响应：

```json
{
  "matches": [
    {
      "user_id": 2,
      "gender": "male",
      "college": "计算机学院",
      "major": "软件工程",
      "profile_completion": 82
    }
  ]
}
```

## 4. 画像摘要

### 获取画像摘要

`GET /profile/summary`

响应示例：

```json
{
  "profile_summary": "用户兴趣：人工智能\n最近活跃：7天内",
  "user": {
    "id": 1,
    "nickname": "Alice",
    "email": "alice@example.com"
  }
}
```

说明：

- 这是字符串摘要接口，不是结构化画像接口。
- 更适合推荐、调试或日志展示。

## 常见错误码

- `401` 未登录或 Token 过期
- `404` 用户不存在
- `405` 方法不允许
- `422` 参数校验失败
