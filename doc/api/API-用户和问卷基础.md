# 用户与问卷基础 API

本文档描述用户基础接口和问卷基础接口的详细说明。

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token
- 时间格式：ISO 8601

---

## 用户接口

### 获取当前用户信息

**请求：**

```
GET /users/me
Authorization: Bearer <access_token>
```

**响应体：**

```json
{
  "id": "u_550e8400e29b41d4a716446655440000",
  "nickname": "Alice",
  "credit_score": 85,
  "points": 150,
  "activity_points": 200,
  "has_honor": true
}
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 用户唯一ID（前缀 `u_`） |
| nickname | string | 昵称 |
| credit_score | number | 信用分（0-100，>=85 为荣誉用户） |
| points | number | 可用积分余额 |
| activity_points | number | 活跃度积分（非交易用） |
| has_honor | boolean | 是否荣誉用户 |

**可能的错误码：**

- `401` 未登录或 Token 过期

---

### 更新用户信息

**请求：**

```
PATCH /users/me
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "nickname": "Alice2024",
  "school": "X大学",
  "tags": ["心理学", "产品", "设计"]
}
```

**参数说明（所有参数可选）：**

| 参数 | 类型 | 约束 | 说明 |
|------|------|------|------|
| nickname | string | <=64 | 昵称 |
| school | string | <=128 | 所在学校 |
| tags | string[] | 可选，每项<=30 | 兴趣标签（最多 10 个） |

**响应体：**

返回更新后的完整用户信息（同 `GET /users/me` 格式）。

**请求示例（更新标签）：**

如果前端传递的 tags 是数组，后端会自动转换为逗号分隔的字符串存储。

```json
{
  "tags": ["前端开发", "AI", "创意写作"]
}
```

后端存储为：`"前端开发,AI,创意写作"`

**可能的错误码：**

- `401` 未登录或 Token 过期
- `405` 方法不允许（非 GET 或 PATCH）
- `422` 参数校验失败

---

## 问卷接口

### 获取问卷列表（任务大厅）

**请求：**

```
GET /surveys?status=active&min_points=10&max_minutes=30&page=1&page_size=20
```

**查询参数：**

| 参数 | 类型 | 约束 | 说明 |
|------|------|------|------|
| status | string | 可选 | 筛选状态：`active`（进行中）、`closed`（已关闭） |
| min_points | number | 可选 | 最低奖励积分 |
| max_minutes | number | 可选 | 最长耗时（分钟） |
| page | number | 可选，默认 1 | 页码 |
| page_size | number | 可选，默认 20 | 每页数量，最多 100 |

**响应体：**

```json
{
  "items": [
    {
      "id": "s_abc123...",
      "title": "城市通勤满意度问卷",
      "reward_points": 50,
      "estimated_minutes": 10,
      "deadline": "2026-02-15"
    },
    {
      "id": "s_def456...",
      "title": "办公环境调查",
      "reward_points": 30,
      "estimated_minutes": 8,
      "deadline": "2026-02-10"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 125
}
```

**字段说明：**

| 字段 | 说明 |
|------|------|
| id | 问卷ID（前缀 `s_`） |
| title | 问卷标题 |
| reward_points | 奖励积分 |
| estimated_minutes | 预计耗时（分钟） |
| deadline | 截止日期（可选） |

**可能的错误码：**

- `422` 参数错误（如 page 非数字）

---

### 获取问卷详情

**请求：**

```
GET /surveys/{survey_id}
```

**响应体：**

```json
{
  "id": "s_abc123...",
  "title": "城市通勤满意度问卷",
  "description": "本问卷旨在了解城市居民的通勤体验",
  "link": "https://example.com/survey/123",
  "reward_points": 50,
  "estimated_minutes": 10,
  "deadline": "2026-02-15",
  "status": "active",
  "created_at": "2026-01-10T12:00:00Z",
  "owner_id": "u_owner123"
}
```

**字段说明：**

| 字段 | 说明 |
|------|------|
| description | 问卷说明/副标题 |
| link | 第三方问卷链接（如 Google Form、问卷星等） |
| status | 问卷状态：`active`（进行中）、`closed`（已关闭） |
| created_at | 创建时间 |
| owner_id | 问卷发布者ID |

**可能的错误码：**

- `404` 问卷不存在

---

### 创建并发布问卷

**请求：**

```
POST /surveys
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "员工餐厅满意度调查",
  "description": "了解员工对食堂的满意度",
  "link": "https://example.com/survey/123",
  "reward_points": 100,
  "deadline": "2026-02-28",
  "estimated_minutes": 15
}
```

**参数说明：**

| 参数 | 类型 | 约束 | 说明 |
|------|------|------|------|
| title | string | 必填，<=200 | 问卷标题 |
| description | string | 可选，<=500 | 问卷说明 |
| link | string | 必填，<=500 | 第三方问卷链接 |
| reward_points | number | 必填，>=0 | 奖励积分（需要充足的积分余额） |
| deadline | string | 可选，ISO 8601 | 截止日期 |
| estimated_minutes | number | 可选 | 预计耗时（分钟） |

**响应体：**

```json
{
  "id": "s_abc123...",
  "status": "active"
}
```

**积分消耗：**

发布问卷时，系统会立即从用户账户扣除 `reward_points` 作为奖励预算。

**可能的错误码：**

- `401` 未登录或 Token 过期
- `405` 方法不允许（非 POST）
- `422` 参数校验失败（缺少必填参数）
- `422` 积分不足：`not enough points to publish survey`

---

### 关闭问卷

**请求：**

```
POST /surveys/{survey_id}/close
Authorization: Bearer <access_token>
```

**响应体：**

```json
{
  "id": "s_abc123...",
  "status": "closed"
}
```

**说明：**

- 只有问卷发布者可以关闭问卷
- 关闭后不再接受新的填答

**可能的错误码：**

- `401` 未登录或 Token 过期
- `404` 问卷不存在
- `403` 权限不足：`not survey owner`

---

## 前端接入指南

### 任务大厅列表

```javascript
// 获取进行中的问卷列表
const response = await fetch('/api/v1/surveys?status=active&page=1&page_size=20', {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  }
});
const data = await response.json();
// data.items 为问卷列表
// data.total 为总数
```

### 打开问卷详情

```javascript
// 点击问卷卡片时获取详情
const response = await fetch(`/api/v1/surveys/${surveyId}`, {
  headers: { 'Authorization': `Bearer ${accessToken}` }
});
const survey = await response.json();
// 重定向到 survey.link 或弹出 iframe
window.open(survey.link, '_blank');
```

### 发布问卷

```javascript
// 用户点击"发布"时
const response = await fetch('/api/v1/surveys', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: formData.title,
    description: formData.description,
    link: formData.link,
    reward_points: parseInt(formData.reward_points),
    estimated_minutes: parseInt(formData.estimated_minutes)
  })
});
const data = await response.json();
if (data.error) {
  alert(data.error); // 显示错误信息
} else {
  alert('问卷发布成功！');
}
```

