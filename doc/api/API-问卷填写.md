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
  "survey_id": "s_abc123",
  "answers": [
    {
      "question_id": "q_1",
      "value": "3-4 次"
    },
    {
      "question_id": "q_2",
      "value": ["家常菜", "轻食沙拉"]
    },
    {
      "question_id": "q_3",
      "value": "菜品丰富，环境整洁"
    },
    {
      "question_id": "q_4",
      "value": ["张三", "13800138000", "zhangsan@example.com"]
    }
  ],
  "duration_seconds": 180
}
```

---

## 字段校验 / 枚举表（建议）

| 字段 | 类型 | 约束 | 枚举/说明 |
| --- | --- | --- | --- |
| `questions[].id` | string | <= 32 | 题目唯一ID |
| `questions[].type` | string | 必填 | `single` / `multi` / `text` / `multi-text` |
| `questions[].title` | string | <= 200 | 题干文本 |
| `questions[].options` | string[] | 选项题必填 | 选项数组，单项 <= 50 |
| `questions[].required` | boolean | 必填 | 是否必填 |
| `questions[].order` | number | >= 1 | 题目顺序 |
| `answers[].question_id` | string | 必填 | 题目ID |
| `answers[].value` | string/array | 必填 | 答案内容，格式见下方说明 |
| `duration_seconds` | number | >= 0 | 填答耗时（秒），用于防作弊 |

**`value` 字段格式规则：**

- `single`（单选题）：字符串，必须是 `options` 中的一项，如 `"选项1"`
- `multi`（多选题）：字符串数组，每项必须在 `options` 中，如 `["选项1", "选项3"]`
- `text`（填空题）：字符串，自由文本，如 `"用户填写的完整回答"`
- `multi-text`（多项填空）：字符串数组，长度应与 `options` 一致，如 `["张三", "13800138000", "zhangsan@example.com"]`

---

## 页面：问卷填写

### 获取问卷详情（用于填写）

**当前实现（临时）：**

`GET /surveys/{survey_id}`

**推荐实现（新接口）：**

`GET /surveys/{survey_id}/fill`

响应体：`SurveyFill`（必须包含 `questions` 字段）

**注意**：前端依赖 `questions` 数组来渲染题目，后端必须返回此字段。

---

### 提交答卷

`POST /surveys/{survey_id}/fills`

请求体：`SurveyResponse`

响应体：

```json
{
  "id": "f_xyz789",
  "status": "pending",
  "points_awarded": 0
}
```

**字段说明：**
- `id`：填写记录ID
- `status`：`pending`（待审核）/ `approved`（已通过）/ `rejected`（已拒绝）
- `points_awarded`：当前已发放积分（审核前为 0）

**后端校验规则：**
1. 所有 `required: true` 的题目必须有答案
2. 单选/多选题的 `value` 必须在 `options` 范围内
3. 同一用户对同一问卷只能提交一次（唯一性约束）
4. `duration_seconds` 不能小于合理阈值（如 10 秒，防作弊）
5. 不能填写自己发布的问卷

---

## 前端本地缓存机制

**LocalStorage 键名：** `survey-fill-{survey_id}`

**存储内容示例：**
```json
{
  "q_1": "3-4 次",
  "q_2": ["家常菜", "轻食沙拉"],
  "q_3": "菜品丰富"
}
```

**实现逻辑：**
- 加载时：从 LocalStorage 恢复已填答案
- 填写时：每次选择/输入立即保存，每 30 秒自动保存
- 提交后：清除 LocalStorage 缓存
- 异常恢复：刷新页面后自动恢复进度

---

## 错误码（本页面常见）

- `401` 未登录或 Token 过期
- `404` 问卷不存在
- `422` 问卷已关闭/不可填写（`survey not active`）
- `422` 填写自己的问卷（`cannot fill your own survey`）
- `422` 已提交过该问卷（`already filled`）
- `422` 必填题未填（`question {id} is required`）
- `422` 选项不合法（`invalid option for question {id}`）
- `422` 填写时间过短（`fill duration too short`）
