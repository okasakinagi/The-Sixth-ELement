# 用户与问卷基础 API

本文档描述账号基础接口和问卷兼容入口。问卷的正式管理流程请优先参考 `API-问卷管理.md`，这里仅保留当前仍然存在的基础入口和兼容入口。

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token
- 时间格式：ISO 8601（UTC）

## 1. 用户接口

### 获取当前用户信息

`GET /users/me`

### 更新当前用户信息

`PATCH /users/me`

### 通过邮箱搜索用户

`GET /users/search?email=alice@example.com`

说明：

- 只能按邮箱精确搜索。
- 不能搜索自己。

## 2. 问卷兼容入口

### 获取问卷列表

`GET /surveys?status=&keyword=`

### 创建问卷（兼容入口）

`POST /surveys`

说明：

- 这是旧入口。
- 当前实现会直接创建并发布问卷，不是草稿流程。

### 获取问卷详情

`GET /surveys/{survey_id}`

### 删除问卷

`DELETE /surveys/{survey_id}`

### 关闭问卷

`POST /surveys/{survey_id}/close`

说明：

- `close` 只会把问卷状态改为 `closed`。
- 正式的投放控制请使用 `pause`、`resume`、`cancel`。

## 3. 当前响应口径

`GET /users/me` 返回：

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

`GET /surveys/{survey_id}` 返回的基础字段包括：

- `id`
- `title`
- `description`
- `reward_points`
- `estimated_minutes`
- `deadline`
- `status`
- `created_at`
- `owner_id`

## 常见错误码

- `401` 未登录或 Token 过期
- `403` 非资源所有者
- `404` 资源不存在
- `405` 方法不允许
- `422` 参数校验失败
