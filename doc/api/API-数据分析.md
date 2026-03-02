# 问卷数据分析 API（SurveyAnalyticsView）

本文档描述“数据分析”页面所需接口，包含概览指标与题目统计。

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token
- 时间格式：ISO 8601

## 权限规则

- 仅问卷发布者（`survey.owner == 当前用户`）可访问以下接口
- 管理员（`Role.name == "admin"`）可访问所有问卷的分析数据
- 填写者访问上述接口返回 `403`

---

## 页面：概览数据

### 获取问卷分析概览

`GET /surveys/{survey_id}/analytics/summary`

**完成率计算说明：**  
`completion_rate = 已填写份数（responses_count）/ 目标份数（target）`  
（即问卷已收到的答卷数与发布者设定目标份数之比；若 `target` 为 `null` 则返回 `null`）

响应体：

```json
{
  "survey_id": "42",
  "title": "校园生活满意度调查 2026",
  "published_at": "2026-02-01T08:00:00Z",
  "responses_count": 47,
  "target": 50,
  "completion_rate": 0.94,
  "average_duration_seconds": 183
}
```

字段说明：

- `published_at`：取 `Survey.updated_at`（问卷发布时 status 变更触发 auto_now 更新，用作发布时间近似值）
- `completion_rate`：0-1，保留 2 位小数；若 `target` 为 `null` 则返回 `null`
- `average_duration_seconds`：所有 submitted Response 的 `duration_seconds` 均值，若无数据则返回 `null`
- `target`：来自 `Survey.target`，若未设置则返回 `null`

### 字段校验 / 枚举表

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `survey_id` | string | 必填 | 问卷 ID |
| `title` | string | - | 问卷标题 |
| `published_at` | string | ISO 8601 | 取 `Survey.updated_at` |
| `responses_count` | number | >= 0 | 已提交份数 |
| `target` | number\|null | >= 1 | 目标份数，未设置为 null |
| `completion_rate` | number | 0-1 | 完成率 |
| `average_duration_seconds` | number\|null | >= 0 | 平均作答时长，无数据为 null |

**缓存策略：** 后端对 summary 响应按 `survey_id` 缓存；问卷状态为 `closed` 时缓存永不过期，问卷仍在 `published` 时缓存 60 秒。

---

## 页面：题目统计

### 获取题目统计列表

`GET /surveys/{survey_id}/analytics/questions`

支持的题型：`single`（单选）、`multi`（多选）、`text`（填空）、`multi-text`（多项填空）

**查询参数（仅对 text / multi-text 类型生效）：**

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `text_page` | int | 1 | 文本答案分页页码 |
| `text_page_size` | int | 20 | 文本答案每页条数，最大 50 |

响应体：

```json
{
  "items": [
    {
      "question_id": "q_1",
      "order_no": 1,
      "title": "您的年级是？",
      "type": "single",
      "options": [
        { "label": "大一", "count": 18, "ratio": 0.38 },
        { "label": "大二", "count": 15, "ratio": 0.32 },
        { "label": "大三", "count": 9,  "ratio": 0.19 },
        { "label": "大四及以上", "count": 5, "ratio": 0.11 }
      ],
      "texts": null,
      "texts_total": null
    },
    {
      "question_id": "q_2",
      "order_no": 2,
      "title": "您常用的学习方式有哪些？（多选）",
      "type": "multi",
      "options": [
        { "label": "线上课程", "count": 31, "ratio": 0.66 },
        { "label": "图书馆自习", "count": 27, "ratio": 0.57 },
        { "label": "小组讨论", "count": 19, "ratio": 0.40 },
        { "label": "刷题/练习册", "count": 22, "ratio": 0.47 }
      ],
      "texts": null,
      "texts_total": null
    },
    {
      "question_id": "q_3",
      "order_no": 3,
      "title": "您对校园生活最大的不满意之处",
      "type": "text",
      "options": null,
      "texts": [
        { "response_id": "r_101", "anonymous_id": "小*明", "value": "食堂排队太长了", "submitted_at": "2026-02-10T12:34:00Z" },
        { "response_id": "r_102", "anonymous_id": "张*", "value": "宿舍网络不稳定", "submitted_at": "2026-02-10T14:20:00Z" }
      ],
      "texts_total": 47
    },
    {
      "question_id": "q_4",
      "order_no": 4,
      "title": "请分别填写您最喜欢和最不喜欢的课程",
      "type": "multi-text",
      "options": null,
      "texts": [
        { "response_id": "r_101", "anonymous_id": "小*明", "value": ["高等数学", "体育课"], "submitted_at": "2026-02-10T12:34:00Z" },
        { "response_id": "r_102", "anonymous_id": "张*", "value": ["软件工程", "英语听力"], "submitted_at": "2026-02-10T14:20:00Z" }
      ],
      "texts_total": 47
    }
  ]
}
```

**字段说明：**

- `options`：仅 `single`/`multi` 类型有值，其余为 `null`
- `options[].ratio`：
  - `single`：`count / 总填写人数`，保留 2 位小数
  - `multi`：`选择该选项的人数 / 总填写人数`，保留 2 位小数（一人可多选，总和可超过 1）
  - 即使某选项无人选择，也必须包含在列表中，`count` 为 `0`，`ratio` 为 `0.0`
- `texts`：仅 `text`/`multi-text` 类型有值，已按 `submitted_at` 倒序排列，支持分页
- `texts[].anonymous_id`：对用户 `nickname` 做遮盖处理，保留首尾各 1 个字符，中间替换为 `*`（如 `copilot → c*****t`，长度 <= 2 时仅保留第一个字符加 `*`）
- `texts[].value`：`text` 类型为字符串，`multi-text` 类型为字符串数组
- `texts_total`：文本答案总条数，用于前端分页计算

---

## 数据导出

### 导出问卷原始回答

`GET /surveys/{survey_id}/analytics/export?format=csv`

直接返回文件流，响应头：

```
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="survey_{survey_id}_export.csv"
```

导出内容列：

| 列名 | 说明 |
| --- | --- |
| `response_id` | 答卷 ID |
| `anonymous_id` | 匿名用户标识（nickname 中间字符遮盖） |
| `submitted_at` | 提交时间（ISO 8601） |
| `duration_seconds` | 作答时长（秒） |
| `q_{id}_title` | 题目标题（每题一列） |
| `q_{id}_answer` | 该题答案；多选/多项填空以英文逗号拼接 |

**format 参数：**

| 值 | 说明 |
| --- | --- |
| `csv` | UTF-8 with BOM，兼容 Excel 中文显示 |
| `xlsx` | Excel 格式（需后端安装 `openpyxl`，暂未实现） |

---

## 错误码

| 状态码 | 含义 |
| --- | --- |
| `401` | 未登录或 Token 过期 |
| `403` | 无权限（非发布者或管理员） |
| `404` | 问卷不存在 |
| `500` | 服务器内部错误 |
