# 问卷管理 API（SurveyManagementView）

本文档描述“问卷管理”页面所需接口，包括列表、状态切换、删除与发布确认。

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token
- 时间格式：ISO 8601

---

## 数据模型（建议）

```json
{
  "id": "S-1204",
  "title": "城市通勤满意度问卷",
  "status": "draft",
  "completed": 0,
  "target": 120,
  "updated_at": "2026-01-12",
  "subtitle": "了解通勤体验与痛点",
  "created_at": "2026-01-10T12:00:00Z"
}
```

- `status`：`draft` / `live` / `paused` / `ended`
- `subtitle`：对应问卷说明（来自编辑器“问卷说明”）

### 字段校验 / 枚举表（建议）

| 字段 | 类型 | 约束 | 枚举/说明 |
| --- | --- | --- | --- |
| `id` | string | <= 20 | 问卷编号 |
| `title` | string | <= 60 | 问卷主标题 |
| `subtitle` | string | <= 120 | 问卷说明 |
| `status` | string | 必填 | `draft` / `live` / `paused` / `ended` |
| `completed` | number | >= 0 | 已完成份数 |
| `target` | number | >= 1 | 目标份数 |
| `updated_at` | string | ISO 8601 | 最后更新时间 |

---

## 页面：问卷列表

前端交互说明（当前实现）：

- 列表操作按钮按状态区分：
  - `draft` 显示“编辑问卷”，进入可编辑模式；
  - `live/paused/ended` 显示“查看问卷”，进入查看并可编辑；保存时另存为新草稿，不覆盖原问卷。

### 获取问卷列表

`GET /surveys`

Query 参数：

- `status`（可选）：筛选状态，支持 `draft` / `live` / `paused` / `ended`
- `keyword`（可选）：按标题模糊搜索

响应体：

```json
{
  "items": [
    {
      "id": "S-1204",
      "title": "城市通勤满意度问卷",
      "status": "draft",
      "completed": 0,
      "target": 120,
      "updated_at": "2026-01-12",
      "subtitle": "了解通勤体验与痛点"
    }
  ]
}
```

### 获取问卷统计摘要

`GET /surveys/summary`

响应体：

```json
{
  "draft_count": 2,
  "live_count": 3,
  "ended_count": 1
}
```

---

## 页面：问卷操作

### 删除问卷

`DELETE /surveys/{survey_id}`

响应体：

```json
{
  "success": true
}
```

### 暂停投放

`POST /surveys/{survey_id}/pause`

响应体：

```json
{
  "id": "S-1205",
  "status": "paused"
}
```

### 恢复投放

`POST /surveys/{survey_id}/resume`

响应体：

```json
{
  "id": "S-1205",
  "status": "live"
}
```

### 发布问卷（积分结算前确认）

`POST /surveys/{survey_id}/publish`

请求体（示例）：

```json
{
  "reward_points": 5,
  "budget_points": 600,
  "target": 120
}
```

参数说明（当前实现）：

- `reward_points`：必填，每份问卷奖励积分（后端不再自动推测）
- `budget_points`：必填，总预算，需满足 `budget_points >= reward_points * target`
- `target`：必填，目标份数，且必须大于 0
- 发布前约束：草稿问卷必须至少包含 1 道题，否则返回 `422`

响应体：

```json
{
  "id": "S-1204",
  "status": "live",
  "published_at": "2026-01-12T10:00:00Z"
}
```

---

## 错误码（本页面常见）

- `401` 未登录或 Token 过期
- `404` 问卷不存在
- `409` 状态冲突（如已结束不可暂停）
- `422` 参数校验失败（常见场景）：
  - 草稿问卷为空（无题目）
  - 预算不足以覆盖 `reward_points * target`
  - 用户积分不足
  - `reward_points / budget_points / target` 类型或范围不合法

说明：前端发布弹窗会将发布错误提示统一显示为中文提示语（便于用户理解）。
