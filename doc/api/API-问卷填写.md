# 问卷填写 API（Survey Fill）

本文档描述“问卷填写”页面所需接口，包含问卷详情获取、提交答卷与保存草稿。

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token（可选开放匿名填写）
- 时间格式：ISO 8601

---

## 数据模型（建议）

### SurveyFill

```json
{
  "id": "S-1204",
  "title": "城市通勤满意度问卷",
  "subtitle": "了解通勤体验与痛点",
  "questions": [
    {
      "id": "q_1",
      "type": "single",
      "title": "您常用的通勤方式是？",
      "options": ["地铁", "公交", "自驾", "骑行"],
      "required": true,
      "order": 1
    }
  ]
}
```

### SurveyResponse

```json
{
  "survey_id": "S-1204",
  "answers": [
    {
      "question_id": "q_1",
      "value": "地铁"
    },
    {
      "question_id": "q_2",
      "value": ["A", "B"]
    },
    {
      "question_id": "q_3",
      "value": "简答文本"
    }
  ],
  "duration_seconds": 180
}
```

---

## 字段校验 / 枚举表（建议）

| 字段 | 类型 | 约束 | 枚举/说明 |
| --- | --- | --- | --- |
| `questions[].type` | string | 必填 | `single` / `multi` / `text` / `multi-text` |
| `questions[].options` | string[] | 选项题必填 | 单项 <= 50 |
| `answers[].value` | string/array | 必填 | `single/text` 为 string，`multi` 为 string[] |
| `duration_seconds` | number | >= 0 | 作答时长 |

---

## 页面：问卷填写

### 获取问卷详情（用于填写）

`GET /surveys/{survey_id}/fill`

响应体：`SurveyFill`

### 保存答卷草稿（可选）

`PATCH /surveys/{survey_id}/responses/draft`

请求体（示例）：

```json
{
  "answers": [
    {
      "question_id": "q_1",
      "value": "地铁"
    }
  ],
  "duration_seconds": 60
}
```

响应体：

```json
{
  "draft_id": "r_draft_001",
  "saved_at": "2026-01-12T10:30:00Z"
}
```

### 提交答卷

`POST /surveys/{survey_id}/responses`

请求体：`SurveyResponse`

响应体：

```json
{
  "id": "r_1204_001",
  "submitted_at": "2026-01-12T10:32:00Z",
  "points_earned": 10
}
```

---

## 错误码（本页面常见）

- `401` 未登录或 Token 过期
- `404` 问卷不存在
- `409` 已提交不可重复提交
- `422` 参数校验失败（必填题未填、选项不合法等）
