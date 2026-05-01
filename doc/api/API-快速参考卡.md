# API 快速参考卡

这是一份面向开发调试的高频接口速查，内容以当前实现为准。

## 1. 认证

- `POST /auth/send-register-code`
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/send-reset-code`
- `POST /auth/reset-password`

后续业务请求统一携带：

```text
Authorization: Bearer <access_token>
```

## 2. 账号与画像

- `GET /users/me`
- `PATCH /users/me`
- `GET /users/search`
- `GET /users/me/profile`
- `PATCH /users/me/profile`
- `PUT /users/me/profile`
- `GET /users/me/profile/matches`
- `GET /profile/summary`

## 3. 问卷主流程

- `POST /surveys/drafts`
- `GET /surveys/drafts/{draft_id}`
- `PATCH /surveys/drafts/{draft_id}`
- `POST /surveys/drafts/{draft_id}/ai-generate`
- `DELETE /surveys/drafts/{draft_id}/questions/{question_id}`
- `POST /surveys/{survey_id}/publish`
- `POST /surveys/{survey_id}/pause`
- `POST /surveys/{survey_id}/resume`
- `POST /surveys/{survey_id}/cancel`
- `DELETE /surveys/{survey_id}`

发布问卷的核心约束：

```json
{
  "reward_points": 5,
  "budget_points": 600,
  "target": 120
}
```

要求满足：`budget_points >= reward_points * target`。

## 4. 填答与任务大厅

- `GET /task-hall/overview`
- `GET /task-hall/home-modules`
- `GET /task-hall/tasks`
- `POST /task-hall/batch/refresh`
- `GET /task-hall/guest-tasks`
- `GET /task-hall/daily-recommendations`
- `POST /task-hall/daily-recommendations/{survey_id}/claim-bonus`
- `GET /surveys/{survey_id}/fill`
- `POST /surveys/{survey_id}/fills`
- `GET /fills/me`
- `POST /fills/{fill_id}/review`（兼容入口）
- `GET /user/level`
- `GET /tasks/daily`
- `GET /tasks/weekly`
- `POST /tasks/{task_code}/claim`

主流程是“提交即发奖”，不是审核后发奖。

## 5. 积分与举报

- `GET /points/summary`
- `GET /points/logs`
- `GET /points/trend`
- `POST /points/update`
- `POST /reports`

说明：

- `GET /points/logs` 在代码中存在 legacy 与 `points_record` 双入口。
- `POST /points/update` 主要用于管理用途。

## 6. 队伍、消息与后台

- `POST /teams`
- `GET /teams/mine`
- `GET /messages`
- `GET /messages/unread-count`
- `POST /messages/points-gift`
- `GET /admin/dashboard/stats`
- `GET /admin/users`
- `GET /admin/surveys`

## 7. 常用请求参数

### 分页

```json
{
  "page": 1,
  "page_size": 20
}
```

### 任务大厅筛选

```text
GET /task-hall/tasks?status=active&min_reward=10&max_minutes=30&page=1&page_size=20
```

### 积分流水筛选

```text
GET /points/logs?type=earn
```

## 8. 资源 ID 前缀

- 用户：`u_...`
- 问卷：`s_...`
- 填写：`f_...`
- 积分：`p_...`
- 举报：`r_...`

## 9. 关键规则

- 注册成功后返回 Bearer Token。
- 发布问卷会立即扣除预算并写入积分流水。
- 填写成功后立即发放积分并写入积分流水。
- 如果填答者属于队伍且不是队长，奖励会转入队长账户。
- 填写最短时长校验当前为 10 秒。
