# 问卷数据分析 API（SurveyAnalyticsView）

本文档描述“数据分析”页面所需接口，包含概览指标与题目统计。

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token
- 时间格式：ISO 8601

---

## 页面：概览数据

### 获取问卷分析概览

`GET /surveys/{survey_id}/analytics/summary`

响应体：

```json
{
  "survey_id": "S-1204",
  "completion_rate": 1.0,
  "average_duration_seconds": 192,
  "satisfaction_score": 4.6,
  "responses_count": 300,
  "target": 300,
  "updated_at": "2026-01-12T10:20:00Z"
}
```

字段说明：

- `completion_rate`：0-1
- `average_duration_seconds`：平均作答用时
- `satisfaction_score`：问卷满意度（1-5）

### 字段校验 / 枚举表（建议）

| 字段 | 类型 | 约束 | 枚举/说明 |
| --- | --- | --- | --- |
| `survey_id` | string | <= 20 | 问卷编号 |
| `completion_rate` | number | 0-1 | 完成率 |
| `average_duration_seconds` | number | >= 0 | 平均作答时长 |
| `satisfaction_score` | number | 1-5 | 满意度评分 |
| `responses_count` | number | >= 0 | 已收集份数 |
| `target` | number | >= 1 | 目标份数 |

---

## 页面：题目统计（可扩展）

### 获取题目统计列表

`GET /surveys/{survey_id}/analytics/questions`

响应体：

```json
{
  "items": [
    {
      "question_id": "q_1",
      "title": "您一周大约在员工餐厅就餐几次？",
      "type": "single",
      "options": [
        { "label": "1-2 次", "count": 80, "ratio": 0.27 },
        { "label": "3-4 次", "count": 140, "ratio": 0.47 },
        { "label": "5 次以上", "count": 80, "ratio": 0.27 }
      ]
    }
  ]
}
```

---

## 导出相关（可选）

### 导出问卷数据

`POST /surveys/{survey_id}/analytics/export`

请求体：

```json
{
  "format": "csv"
}
```

响应体：

```json
{
  "download_url": "https://example.com/export/S-1204.csv"
}
```

---

## 错误码（本页面常见）

- `401` 未登录或 Token 过期
- `404` 问卷不存在
- `500` 服务器内部错误
