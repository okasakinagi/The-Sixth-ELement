# 问卷数据分析 API

本文档描述问卷分析、题目统计和导出接口。

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token
- 时间格式：ISO 8601

## 权限规则

- 仅问卷发布者可访问自己的分析数据。
- 管理员可以访问所有问卷分析数据。

## 1. 概览数据

### 获取分析概览

`GET /surveys/{survey_id}/analytics/summary`

响应示例：

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

说明：

- `completion_rate = responses_count / target`。
- 如果 `target` 为空，则 `completion_rate` 也为空。
- `published_at` 来自发布时的更新时间快照。

## 2. 题目统计

### 获取题目统计列表

`GET /surveys/{survey_id}/analytics/questions`

查询参数：

- `text_page`
- `text_page_size`

说明：

- `single` 和 `multi` 类型返回选项统计。
- `text` 和 `multi-text` 类型返回文本答案分页。

## 3. 数据导出

### 导出问卷数据

`GET /surveys/{survey_id}/analytics/export?format=csv|xlsx`

说明：

- `format=csv` 返回 CSV 文件。
- `format=xlsx` 返回 Excel 文件。
- 当前实现两种格式都支持。

## 常见错误码

- `401` 未登录或 Token 过期
- `403` 无权限
- `404` 问卷不存在
- `405` 方法不允许
- `422` 参数校验失败
