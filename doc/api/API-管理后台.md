# 管理后台 API

本文档描述管理后台的登录、看板、用户管理、问卷管理、推荐分析和通知接口。所有接口位于 `/api/v1/admin` 下。

## 约定

- Base URL：`/api/v1/admin`
- Content-Type：`application/json`
- 认证方式：管理员 Bearer Token

## 1. 登录与看板

### 管理员登录

`POST /login`

### 看板统计

`GET /dashboard/stats`

### 看板趋势

`GET /dashboard/trend`

### 看板导出

`GET /dashboard/export`

## 2. 用户管理

- `GET /users`
- `GET /users/{user_id}`
- `PATCH /users/{user_id}/info`
- `DELETE /users/{user_id}/delete`
- `PATCH /users/{user_id}/status`
- `PATCH /users/{user_id}/promote-admin`
- `PATCH /users/batch/status`
- `PATCH /users/batch/points`
- `GET /users/export`

说明：

- `promote-admin` 只用于管理员提权。
- 批量接口用于后台运营操作。

## 3. 问卷管理

- `GET /surveys`
- `GET /surveys/pending`
- `POST /surveys/create`
- `GET /surveys/{survey_id}`
- `PATCH /surveys/{survey_id}/update`
- `DELETE /surveys/{survey_id}/delete`
- `POST /surveys/{survey_id}/close`
- `POST /surveys/{survey_id}/approve`
- `POST /surveys/{survey_id}/reject`
- `GET /surveys/export`

## 4. 分析与风控

- `GET /analytics/recommend`
- `GET /analytics/recommend/events`
- `GET /analytics/ai`
- `GET /risk`
- `GET /operation_logs`

## 5. 公告与通知

- `GET /announcements`
- `POST /announcements/create`
- `GET /notifications`
- `PATCH /notifications/{message_id}/read`
- `PATCH /notifications/mark-all-read`

## 当前业务口径

- 除 `POST /login` 外，其他接口都要求管理员身份。
- 推荐分析和 AI 分析是后台运营接口，不是普通用户页面接口。
- 问卷审批、拒绝和强制关闭属于后台人工干预流程。

## 常见错误码

- `401` 未登录或 Token 过期
- `403` 非管理员
- `404` 资源不存在
- `405` 方法不允许
- `422` 参数校验失败
