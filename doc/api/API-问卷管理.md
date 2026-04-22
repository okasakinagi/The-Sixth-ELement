# 问卷管理 API

本文档描述问卷列表、详情、状态切换、发布、取消和删除接口。

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token
- 时间格式：ISO 8601

## 1. 问卷列表

### 获取我的问卷列表

`GET /surveys?status=&keyword=`

说明：

- `status` 支持 `draft`、`live`、`paused`、`ended`。
- `keyword` 按标题模糊搜索。

### 获取统计摘要

`GET /surveys/summary`

响应：

```json
{
  "draft_count": 2,
  "live_count": 3,
  "ended_count": 1
}
```

## 2. 草稿

### 创建草稿

`POST /surveys/drafts`

### 获取草稿详情

`GET /surveys/drafts/{draft_id}`

### 更新草稿

`PATCH /surveys/drafts/{draft_id}`

### AI 生成题目

`POST /surveys/drafts/{draft_id}/ai-generate`

### 删除草稿题目

`DELETE /surveys/drafts/{draft_id}/questions/{question_id}`

## 3. 发布与投放

### 发布问卷

`POST /surveys/{survey_id}/publish`

请求体：

```json
{
  "reward_points": 5,
  "budget_points": 600,
  "target": 120
}
```

规则：

- `reward_points`、`budget_points`、`target` 都必填。
- `budget_points >= reward_points * target`。
- 草稿必须至少有 1 道题。
- 发布成功后，问卷状态为 `live`。

### 暂停投放

`POST /surveys/{survey_id}/pause`

### 恢复投放

`POST /surveys/{survey_id}/resume`

### 取消发布

`POST /surveys/{survey_id}/cancel`

说明：

- 状态会变为 `ended`。
- 会按当前退款规则退还剩余预算。
- 退款不包含推断出的加速预算部分。

## 4. 问卷详情与删除

### 获取问卷详情

`GET /surveys/{survey_id}`

### 删除问卷

`DELETE /surveys/{survey_id}`

说明：

- 如果问卷曾经发布或暂停，删除前会先按同一退款逻辑结算。

## 5. 评估

### 问卷评估

`GET /surveys/{survey_id}/evaluate`

说明：

- 这是兼容接口，用于估算难度和预计时长。

## 常见错误码

- `401` 未登录或 Token 过期
- `404` 问卷不存在
- `409` 状态冲突
- `422` 参数校验失败
