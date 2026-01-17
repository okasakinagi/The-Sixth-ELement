# 问卷制作 API（SurveyEntryView / SurveyAiPromptView / SurveyBuilderView）

本文档描述“问卷制作 + AI 编辑器”三段式流程的接口，包括标题设定、AI 生成、编辑与自动保存。

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token
- 时间格式：ISO 8601

---

## 数据模型（建议）

### SurveyDraft

```json
{
  "id": "draft_001",
  "title": "员工餐厅就餐满意度调查",
  "subtitle": "本问卷用于了解员工对餐厅服务的满意度。",
  "prompt": "请生成一份调查问卷...",
  "status": "draft",
  "questions": [
    {
      "id": "q_1",
      "type": "single",
      "title": "您一周大约在员工餐厅就餐几次？",
      "options": ["1-2 次", "3-4 次", "5 次以上"],
      "required": true,
      "is_ai": true,
      "order": 1
    }
  ],
  "updated_at": "2026-01-12T10:20:00Z"
}
```

- `subtitle`：编辑器的“问卷说明”，需同步到任务大厅副标题
- `type`：`single` / `multi` / `text` / `multi-text`
- `is_ai`：AI 生成题目初始为 `true`，用户编辑后可置为 `false`
- `order`：题目排序（可由后端自动维护）

### 字段校验 / 枚举表（建议）

| 字段 | 类型 | 约束 | 枚举/说明 |
| --- | --- | --- | --- |
| `title` | string | <= 60 | 问卷主标题 |
| `subtitle` | string | <= 120 | 问卷说明 |
| `prompt` | string | <= 800 | AI 输入内容 |
| `status` | string | 必填 | `draft` / `live` / `paused` / `ended` |
| `questions[].id` | string | <= 32 | 题目唯一 ID |
| `questions[].type` | string | 必填 | `single` / `multi` / `text` / `multi-text` |
| `questions[].title` | string | <= 200 | 题干 |
| `questions[].options` | string[] | 可选 | 选项题必填，单项 <= 50 |
| `questions[].required` | boolean | 必填 | 是否必填 |
| `questions[].is_ai` | boolean | 必填 | 是否为 AI 生成 |
| `questions[].order` | number | >= 1 | 顺序 |

---

## 页面：标题设定（Entry）

### 创建草稿（写入标题）

`POST /surveys/drafts`

请求体：

```json
{
  "title": "员工餐厅就餐满意度调查"
}
```

响应体：

```json
{
  "id": "draft_001",
  "title": "员工餐厅就餐满意度调查",
  "status": "draft"
}
```

---

## 页面：AI Prompt

### 提交 Prompt 生成题目

`POST /surveys/drafts/{draft_id}/ai-generate`

请求体：

```json
{
  "prompt": "请生成一份调查问卷...",
  "question_count": 15
}
```

响应体：

```json
{
  "draft_id": "draft_001",
  "questions": [
    {
      "id": "q_1",
      "type": "single",
      "title": "您一周大约在员工餐厅就餐几次？",
      "options": ["1-2 次", "3-4 次", "5 次以上"],
      "required": true,
      "is_ai": true,
      "order": 1
    }
  ]
}
```

> 若 AI 接口不可用，可返回预置模板以便演示。

---

## 页面：编辑器主界面

### 获取草稿详情

`GET /surveys/drafts/{draft_id}`

响应体：`SurveyDraft`

### 自动保存草稿（2 分钟一次）

`PATCH /surveys/drafts/{draft_id}`

请求体（示例）：

```json
{
  "title": "员工餐厅就餐满意度调查",
  "subtitle": "本问卷用于了解员工对餐厅服务的满意度。",
  "questions": [
    {
      "id": "q_1",
      "title": "您一周大约在员工餐厅就餐几次？",
      "options": ["1-2 次", "3-4 次", "5 次以上"],
      "required": true,
      "is_ai": false,
      "order": 1
    }
  ]
}
```

响应体：

```json
{
  "id": "draft_001",
  "updated_at": "2026-01-12T10:22:00Z"
}
```

### 保存草稿为问卷

`POST /surveys`

请求体：

```json
{
  "draft_id": "draft_001"
}
```

响应体：

```json
{
  "id": "S-1204",
  "status": "draft"
}
```

### 删除题目（可选细化接口）

`DELETE /surveys/drafts/{draft_id}/questions/{question_id}`

响应体：

```json
{
  "success": true
}
```

---

## 错误码（本页面常见）

- `401` 未登录或 Token 过期
- `404` 草稿不存在
- `422` 参数校验失败
