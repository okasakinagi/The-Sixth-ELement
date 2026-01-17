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
  "budget_points": 600,
  "target": 120
}
```

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
- `422` 参数校验失败
