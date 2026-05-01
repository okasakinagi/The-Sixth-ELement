# API 总览

本文按当前代码实现汇总后端路由。详细参数请查看各专题文档。

## 路由结构

- 统一前缀：`/api/v1`
- `core`：认证、账号、兼容问卷、举报、内部相似度接口
- `survey_management`：草稿、发布、暂停、恢复、取消、分析
- `task_hall`：任务大厅、每日推荐、等级任务
- `points_record`：积分汇总、流水、趋势、更新
- `personal_homepage`：个人画像
- `user_profile_extractor`：画像摘要
- `team_messaging`：队伍与消息
- `admin_backend`：管理后台

## 已实现接口

### 认证与账号

- `POST /auth/send-register-code`
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/send-reset-code`
- `POST /auth/reset-password`
- `GET /users/me`
- `PATCH /users/me`
- `GET /users/search`

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
- `GET /surveys/{survey_id}/evaluate`

### 问卷填写与记录

- `GET /surveys/{survey_id}/fill`
- `POST /surveys/{survey_id}/fills`
- `GET /fills/me`
- `POST /fills/{fill_id}/review`

### 任务大厅与等级

- `GET /task-hall/overview`
- `GET /task-hall/home-modules`
- `GET /task-hall/tasks`
- `POST /task-hall/batch/refresh`
- `GET /task-hall/guest-tasks`
- `GET /task-hall/daily-recommendations`
- `POST /task-hall/daily-recommendations/{survey_id}/claim-bonus`
- `GET /user/level`
- `GET /tasks/daily`
- `GET /tasks/weekly`
- `POST /tasks/{task_code}/claim`

### 积分与举报

- `GET /points/summary`
- `GET /points/logs`
- `GET /points/trend`
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

### 队伍与消息

- `POST /teams`
- `GET /teams/mine`
- `GET /teams/{team_id}`
- `GET /teams/{team_id}/members`
- `PATCH /teams/{team_id}/update`
- `DELETE /teams/{team_id}/delete`
- `DELETE /teams/{team_id}/members/{user_id}/remove`
- `PATCH /teams/{team_id}/members/{user_id}/role`
- `POST /teams/{team_id}/invite`
- `GET /invitations`
- `PATCH /invitations/{invitation_id}/accept`
- `PATCH /invitations/{invitation_id}/reject`
- `GET /teams/{team_id}/invite/{invitee_id}/cooldown`
- `GET /messages`
- `GET /messages/unread-count`
- `PATCH /messages/{message_id}/read`
- `DELETE /messages/{message_id}/delete`
- `POST /messages/points-gift`
- `GET /messages/points-gift/limit`

### 管理后台

- `POST /admin/login`
- `GET /admin/dashboard/stats`
- `GET /admin/dashboard/trend`
- `GET /admin/dashboard/export`
- `GET /admin/users`
- `GET /admin/users/{user_id}`
- `PATCH /admin/users/{user_id}/info`
- `DELETE /admin/users/{user_id}/delete`
- `PATCH /admin/users/{user_id}/status`
- `PATCH /admin/users/{user_id}/promote-admin`
- `PATCH /admin/users/batch/status`
- `PATCH /admin/users/batch/points`
- `GET /admin/users/export`
- `GET /admin/surveys`
- `GET /admin/surveys/pending`
- `POST /admin/surveys/create`
- `GET /admin/surveys/{survey_id}`
- `PATCH /admin/surveys/{survey_id}/update`
- `DELETE /admin/surveys/{survey_id}/delete`
- `POST /admin/surveys/{survey_id}/close`
- `POST /admin/surveys/{survey_id}/approve`
- `POST /admin/surveys/{survey_id}/reject`
- `GET /admin/surveys/export`
- `GET /admin/analytics/recommend`
- `GET /admin/analytics/recommend/events`
- `GET /admin/analytics/ai`
- `GET /admin/risk`
- `GET /admin/announcements`
- `POST /admin/announcements/create`
- `GET /admin/operation_logs`
- `GET /admin/notifications`
- `PATCH /admin/notifications/{message_id}/read`
- `PATCH /admin/notifications/mark-all-read`

## 关键业务口径

1. 发布问卷必须同时提供 `reward_points`、`budget_points`、`target`。
2. `POST /surveys/{survey_id}/fills` 是主流程，提交后立即发奖。
3. `POST /fills/{fill_id}/review` 只是兼容入口，不是主流程依赖。
4. `GET /points/logs` 有 legacy 与 `points_record` 两套实现，文档里要区分消费场景。
5. 任务大厅、等级任务、画像摘要和后台模块都已独立挂载，不是单体视图。

## 常见状态码

- `200` 成功
- `401` 未认证或 Token 过期
- `403` 权限不足
- `404` 资源不存在
- `405` 方法不允许
- `409` 状态冲突
- `422` 参数校验失败
- `500` 服务器内部错误
