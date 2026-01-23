# 积分与报告 API

本文档描述用户积分流水查询和举报相关接口。

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token
- 时间格式：ISO 8601

---

## 积分流水 API

### 获取积分流水记录

**请求：**

```
GET /points/logs?type=&page=1&page_size=20
Authorization: Bearer <access_token>
```

**查询参数：**

| 参数 | 类型 | 约束 | 说明 |
|------|------|------|------|
| type | string | 可选 | 筛选类型：`earn`（收入）、`spend`（支出），不填则返回全部 |
| page | number | 可选，默认 1 | 页码 |
| page_size | number | 可选，默认 20 | 每页数量 |

**响应体：**

```json
{
  "items": [
    {
      "id": "p_abc123...",
      "delta": 50,
      "reason": "完成问卷",
      "created_at": "2026-01-21T10:30:00Z",
      "related_id": "s_survey123",
      "related_type": "survey_fill"
    },
    {
      "id": "p_def456...",
      "delta": -100,
      "reason": "发布问卷消耗",
      "created_at": "2026-01-20T15:22:00Z",
      "related_id": "s_survey456",
      "related_type": "survey_publish"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 45,
  "user": {
    "id": "u_abc123...",
    "points": 150,
    "credit_score": 85,
    "activity_points": 200,
    "has_honor": true
  }
}
```

**字段说明：**

| 字段 | 说明 |
|------|------|
| id | 流水记录唯一ID |
| delta | 积分变化量（正数=收入，负数=支出） |
| reason | 变化原因 |
| created_at | 发生时间 |
| related_id | 关联资源ID（如 survey_id 或 fill_id） |
| related_type | 关联资源类型：`survey_fill`（完成问卷）、`survey_publish`（发布问卷） |
| has_honor | 是否具有荣誉身份（credit_score >= 85） |

**列表示例：**

| 原因 | delta | related_type | 说明 |
|------|-------|--------------|------|
| 完成问卷 | +50 | survey_fill | 用户填答问卷，被问卷主审核通过 |
| 发布问卷消耗 | -100 | survey_publish | 用户发布问卷，扣除预设的积分预算 |

**可能的错误码：**

- `401` 未登录或 Token 过期
- `422` 参数错误（如 page 非数字）

---

## 举报 API

### 创建举报

**请求：**

```
POST /reports
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "target_type": "survey",
  "target_id": "s_survey123",
  "reason": "问卷内容违反平台规范"
}
```

**参数说明：**

| 参数 | 类型 | 约束 | 说明 |
|------|------|------|------|
| target_type | string | 必填 | 举报目标类型：`survey`（问卷）、`user`（用户） |
| target_id | string | 必填，<=64 | 被举报对象ID |
| reason | string | 必填，<=200 | 举报原因 |

**响应体：**

```json
{
  "id": "r_abc123...",
  "status": "pending"
}
```

**字段说明：**

| 字段 | 说明 |
|------|------|
| id | 举报记录唯一ID（前缀 `r_`） |
| status | 举报状态：`pending`（待审核）、`reviewed`（已处理） |

**举报原因示例：**

- 问卷类：`问卷内容不当`、`虚假问卷`、`重复问卷`、`涉及隐私`等
- 用户类：`骚扰其他用户`、`刷单行为`、`虚假信息`等

**可能的错误码：**

- `401` 未登录或 Token 过期
- `405` 方法不允许（非 POST）
- `422` 参数校验失败：`target_type, target_id, reason required`
- `422` target_type 非法（需为 `survey` 或 `user`）

---

## 积分经济说明

### 积分获得方式

| 方式 | 积分 | 触发条件 |
|------|------|---------|
| 注册新账户 | +20 | 注册成功 |
| 完成问卷 | 由发布者设定 | 问卷被审核通过 |

### 积分消耗方式

| 方式 | 积分 | 说明 |
|------|------|------|
| 发布问卷 | 由用户设定 | 作为问卷奖励发布时扣除 |

### 信用分系统

- **初始值**：80 分
- **计算方式**：完成问卷时不调整（暂未实现自动扣分机制）
- **荣誉身份**：credit_score >= 85 时获得 `has_honor=true`

### 活跃度积分（不可交易）

- **获得**：完成问卷被审核通过时 +points_awarded
- **用途**：标识用户贡献度，用于排序和推荐

---

## 前端接入指南

### 积分展示

用户点击"积分流水"时调用 `GET /points/logs`：

```javascript
const response = await fetch('/api/v1/points/logs?page=1&page_size=20', {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  }
});
const data = await response.json();
// 显示 data.user 的积分信息
// 显示 data.items 的流水列表
```

### 举报提交

用户点击"举报"按钮时调用 `POST /reports`：

```javascript
const response = await fetch('/api/v1/reports', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    target_type: 'survey',
    target_id: surveyId,
    reason: userInput
  })
});
const data = await response.json();
if (data.id) {
  alert('举报成功，感谢你的反馈！');
}
```

