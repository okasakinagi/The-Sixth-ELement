# 答卷提交与审核 API

本文档描述用户填答问卷、获取填写记录和审核答卷的接口。

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token
- 时间格式：ISO 8601

---

## 数据模型

### 填写记录（FillRecord）

```json
{
  "id": "f_abc123...",
  "survey_id": "s_survey123",
  "status": "pending",
  "created_at": "2026-01-21T10:30:00Z"
}
```

**字段说明：**

| 字段 | 说明 |
|------|------|
| id | 填写记录ID（前缀 `f_`） |
| survey_id | 所属问卷ID |
| status | 审核状态：`pending`（待审核）、`approved`（已通过）、`rejected`（已拒绝） |
| created_at | 提交时间 |

---

## 答卷提交

### 提交答卷

**请求：**

```
POST /surveys/{survey_id}/fills
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "duration_seconds": 180
}
```

**参数说明：**

| 参数 | 类型 | 约束 | 说明 |
|------|------|------|------|
| duration_seconds | number | 可选 | 填答耗时（秒），用于防作弊验证 |

**响应体：**

```json
{
  "id": "f_abc123...",
  "status": "pending",
  "points_awarded": 0
}
```

**字段说明：**

| 字段 | 说明 |
|------|------|
| id | 填写记录ID |
| status | 当前状态（提交时为 `pending`） |
| points_awarded | 已发放积分（待审核时为 0） |

**验证规则：**

- 填答时间不能过短（需 > 10 秒）
- 一个用户对同一问卷只能提交一次
- 不能填写自己发布的问卷
- 问卷必须处于 `active` 状态

**可能的错误码：**

- `401` 未登录或 Token 过期
- `404` 问卷不存在：`survey not found`
- `405` 方法不允许（非 POST）
- `422` 问卷已关闭：`survey not active`
- `422` 不能填写自己的问卷：`cannot fill your own survey`
- `422` 已填过该问卷：`already filled`
- `422` 填答时间过短：`fill duration too short`

---

## 填写记录查询

### 获取我的填写记录

**请求：**

```
GET /fills/me?status=&page=1&page_size=20
Authorization: Bearer <access_token>
```

**查询参数：**

| 参数 | 类型 | 约束 | 说明 |
|------|------|------|------|
| status | string | 可选 | 筛选状态：`pending`、`approved`、`rejected`，不填则返回全部 |
| page | number | 可选，默认 1 | 页码 |
| page_size | number | 可选，默认 20 | 每页数量 |

**响应体：**

```json
{
  "items": [
    {
      "id": "f_abc123...",
      "survey_id": "s_survey123",
      "status": "approved",
      "created_at": "2026-01-20T15:30:00Z"
    },
    {
      "id": "f_def456...",
      "survey_id": "s_survey456",
      "status": "pending",
      "created_at": "2026-01-21T10:00:00Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 5
}
```

**可能的错误码：**

- `401` 未登录或 Token 过期

---

## 答卷审核

### 审核答卷

**请求：**

```
POST /fills/{fill_id}/review
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "status": "approved"
}
```

**参数说明：**

| 参数 | 类型 | 约束 | 说明 |
|------|------|------|------|
| status | string | 必填 | 审核结果：`approved`（通过）、`rejected`（拒绝） |

**响应体：**

```json
{
  "id": "f_abc123...",
  "status": "approved",
  "points_awarded": 50
}
```

**字段说明：**

| 字段 | 说明 |
|------|------|
| id | 填写记录ID |
| status | 审核结果 |
| points_awarded | 发放的积分 |

**审核逻辑：**

- **通过（approved）**：
  - 用户获得问卷设定的 `reward_points`
  - 用户的 `activity_points` 增加相同数值
  - 生成对应的积分流水记录（reason: "完成问卷"）
  
- **拒绝（rejected）**：
  - `points_awarded` 为 0
  - 不产生任何积分变化
  - 用户可重新填答该问卷

**权限限制：**

- 只有问卷发布者可以审核答卷
- 同一答卷只能审核一次（status 必须为 `pending`）

**可能的错误码：**

- `401` 未登录或 Token 过期
- `404` 填写记录不存在：`fill record not found`
- `405` 方法不允许（非 POST）
- `403` 权限不足：`not survey owner`
- `422` 参数错误：`status must be approved or rejected`
- `422` 已审核过：`record already reviewed`

---

## 前端接入指南

### 提交答卷

用户在第三方问卷平台（Google Form 等）完成填答后，点击"提交"按钮时：

```javascript
// 记录填答耗时
const startTime = Date.now();

// ... 用户填答问卷 ...

const endTime = Date.now();
const duration = Math.floor((endTime - startTime) / 1000); // 转换为秒

// 提交答卷
const response = await fetch(`/api/v1/surveys/${surveyId}/fills`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    duration_seconds: duration
  })
});

const data = await response.json();
if (data.error) {
  alert(data.error); // 显示错误信息
} else {
  alert('答卷已提交，等待审核！');
  // 跳转回任务大厅
  navigate('/tasks');
}
```

### 查看填写记录

```javascript
// 打开"我的填答"页面时
const response = await fetch('/api/v1/fills/me?page=1&page_size=20', {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  }
});

const data = await response.json();
// data.items 为填写记录列表
// 显示每条记录的状态和时间
```

### 审核答卷（问卷发布者）

在"问卷管理"页面的"待审核"标签中：

```javascript
// 获取待审核的答卷列表
const response = await fetch(`/api/v1/fills/me?status=pending`, {
  headers: { 'Authorization': `Bearer ${accessToken}` }
});

// 点击"批准"或"拒绝"时
const reviewResponse = await fetch(`/api/v1/fills/${fillId}/review`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    status: 'approved' // 或 'rejected'
  })
});

const result = await reviewResponse.json();
if (result.error) {
  alert(result.error);
} else {
  alert(`答卷已${result.status === 'approved' ? '批准' : '拒绝'}，${result.points_awarded} 积分已发放`);
  // 刷新列表
}
```

---

## 状态流转图

```
提交答卷
   |
   v
pending (待审核)
   |
   +---> approved (已通过) --> 发放积分 --> 完成
   |
   +---> rejected (已拒绝) --> 无积分 --> 完成
```

---

## 常见问题

### 1. 用户提交后能否修改填答？

否，一次提交后不能修改。如被拒绝，用户可以重新提交。

### 2. 审核后能否反悔？

不能。审核结果不可修改，需要另外设计"申诉"流程。

### 3. 填答时间过短会怎样？

提交请求时会返回 `422` 错误，填答记录不会被创建。

### 4. 同一用户能否多次填答同一问卷？

不能。系统会检查唯一性约束，第二次提交会返回 `already filled` 错误。

