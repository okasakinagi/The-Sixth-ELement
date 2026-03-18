# API 总览

本文件按当前代码实现汇总后端接口。详细入参/出参请看各专题文档。

## 实际路由结构

- 统一前缀：`/api/v1`
- 多应用挂载：`core`、`survey_management`、`task_hall`、`personal_homepage`
- 子前缀挂载：
   - `points_record` 挂载在 `/api/v1/points/`
   - `user_profile_extractor` 挂载在 `/api/v1/profile/`

## 已实现接口（按领域）

### 认证与账号

- `POST /auth/send-register-code`
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/send-reset-code`
- `POST /auth/reset-password`
- `GET /users/me`
- `PATCH /users/me`

### 问卷管理与制作

- `GET /surveys`
- `POST /surveys`
- `GET /surveys/summary`
- `POST /surveys/drafts`
- `GET /surveys/drafts/{draft_id}`
- `PATCH /surveys/drafts/{draft_id}`
- `POST /surveys/drafts/{draft_id}/ai-generate`
- `DELETE /surveys/drafts/{draft_id}/questions/{question_id}`
- `GET /surveys/{survey_id}`
- `DELETE /surveys/{survey_id}`
- `POST /surveys/{survey_id}/publish`
- `POST /surveys/{survey_id}/pause`
- `POST /surveys/{survey_id}/resume`
- `POST /surveys/{survey_id}/cancel`
- `POST /surveys/{survey_id}/evaluate`
- `POST /surveys/{survey_id}/close`（兼容入口）

### 问卷填写与记录

- `GET /surveys/{survey_id}/fill`
- `POST /surveys/{survey_id}/fills`
- `GET /fills/me`
- `POST /fills/{fill_id}/review`（兼容入口，非主流程）

### 任务大厅

- `GET /task-hall/overview`
- `GET /task-hall/tasks`
- `POST /task-hall/batch/refresh`
- `GET /task-hall/guest-tasks`

### 数据分析

- `GET /surveys/{survey_id}/analytics/summary`
- `GET /surveys/{survey_id}/analytics/questions`
- `GET /surveys/{survey_id}/analytics/export`

### 积分与举报

- `GET /points/logs`（当前由 `core` 提供）
- `GET /points/summary`
- `GET /points/logs`（`points_record` 路面，注意同名路径并存）
- `POST /points/update`
- `POST /reports`

### 画像与内部能力

- `GET /users/me/profile`
- `PATCH /users/me/profile`
- `PUT /users/me/profile`
- `GET /users/me/profile/matches`
- `GET /profile/summary`
- `POST /internal/similarity/compute`
- `POST /internal/vector/encode`
- `POST /internal/vector/generate-string`
- `POST /internal/vector/generate`
- `POST /internal/similarity/dismiss`
- `POST /internal/similarity/abandon`
- `POST /internal/similarity/abandon/{fill_id}`

---

## 关键业务口径（与代码一致）

1. 发布主流程使用 `POST /surveys/{survey_id}/publish`，入参必须包含 `reward_points`、`budget_points`、`target`，并满足 `budget_points >= reward_points * target`。
2. 填写主流程为“提交即发奖”：`POST /surveys/{survey_id}/fills` 成功后立即发放积分并写入积分流水。
3. `POST /fills/{fill_id}/review` 仍存在，但属于兼容逻辑，不是当前前端主流程依赖点。
4. 积分接口存在双入口语义：`/points/logs` 在代码中有 legacy 与 points_record 两套实现，需要按前端实际消费结构选用。

---

## 通用约定

- **Base URL**：`/api/v1`
- **认证**：`Authorization: Bearer <access_token>`
- **时间格式**：ISO 8601（UTC，示例：`2026-03-18T10:30:00Z`）

错误响应统一形态：

```json
{
   "error": "错误信息"
}
```

常见状态码：

- `200` 成功
- `401` 未认证或 Token 过期
- `403` 权限不足
- `404` 资源不存在
- `405` 方法不允许
- `409` 状态冲突
- `422` 参数校验失败
- `500` 服务器内部错误

---

## 本次修订说明

- 将“待实现”描述改为“已实现路由实况”。
- 修正主流程：由“审核后发奖”改为“提交即发奖”。
- 修正任务大厅与画像接口状态。
- 补充多应用挂载结构，避免将项目误判为单应用 API。
