# 问卷制作 API

本文档描述草稿创建、草稿编辑和 AI 生成题目接口。当前实现以问卷草稿为核心，不再使用旧的分散式“页面说明”写法。

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token
- 时间格式：ISO 8601

## 1. 草稿创建

### 创建草稿

`POST /surveys/drafts`

请求体：

```json
{
  "title": "员工餐厅就餐满意度调查",
  "subtitle": "本问卷用于了解员工对餐厅服务的满意度。"
}
```

响应：

```json
{
  "id": "s_34",
  "title": "员工餐厅就餐满意度调查",
  "status": "draft"
}
```

说明：

- 草稿创建后默认处于 `draft`。
- `subtitle` 会写入问卷说明。

## 2. 草稿编辑

### 获取草稿详情

`GET /surveys/drafts/{draft_id}`

响应包含：

- `id`
- `title`
- `subtitle`
- `status`
- `questions`
- `updated_at`

### 更新草稿

`PATCH /surveys/drafts/{draft_id}`

请求体支持：

```json
{
  "title": "新的标题",
  "subtitle": "新的说明",
  "questions": [
    {
      "id": "q_1",
      "type": "single",
      "title": "您一周大约在员工餐厅就餐几次？",
      "options": ["1-2 次", "3-4 次", "5 次以上"],
      "required": true,
      "is_ai": false,
      "order": 1
    }
  ]
}
```

说明：

- 只传 `title` 或 `subtitle` 时，只更新对应字段。
- 只传 `questions` 时，后端会重建该草稿的题目列表。

### 删除题目

`DELETE /surveys/drafts/{draft_id}/questions/{question_id}`

## 3. AI 生成题目

### AI 生成草稿题目

`POST /surveys/drafts/{draft_id}/ai-generate`

请求体：

```json
{
  "prompt": "请生成一份员工满意度调查问卷",
  "question_count": 10
}
```

响应：

```json
{
  "draft_id": "s_34",
  "questions": [
    {
      "id": "q_1",
      "type": "single",
      "title": "...",
      "options": ["..."],
      "required": true,
      "is_ai": true,
      "order": 1
    }
  ]
}
```

## 4. 字段说明

- `type` 当前支持 `single`、`multi`、`text`、`multi-text`。
- `required` 表示是否必答。
- `order` 表示题目顺序。
- `is_ai` 用于标识是否来自 AI 生成。

## 常见错误码

- `401` 未登录或 Token 过期
- `404` 草稿不存在
- `405` 方法不允许
- `422` 参数校验失败
