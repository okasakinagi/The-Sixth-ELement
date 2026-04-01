# 用户与问卷基础 API

本文档描述账号基础接口与问卷基础管理接口（以当前代码实现为准）。

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token
- 时间格式：ISO 8601（UTC）

---

## 用户接口

### 获取当前用户信息

`GET /users/me`

响应示例：

```json
{
  "id": "1",
  "nickname": "Alice",
  "credit_score": 80,
  "points": 120,
  "activity_points": 30,
  "has_honor": false
}
```

说明：

- `has_honor` 按 `credit_score >= 85` 计算。
- 当前实现返回基础账号字段，不会在 `GET /users/me` 中直接返回 `school` 或 `tags`。

---

### 更新当前用户信息

`PATCH /users/me`

请求体（可选字段）：

```json
{
  "nickname": "Alice2026",
  "school": "X大学",
  "tags": ["心理学", "产品", "设计"]
}
```

说明：

- `nickname`：直接更新昵称。
- `school`：写入 school 类型标签。
- `tags`：写入 interest 类型标签。

响应：同 `GET /users/me`。

---

## 问卷基础接口

说明：`/surveys` 在当前实现中用于“我的问卷管理”，不是任务大厅入口。任务大厅请使用 `/task-hall/*`。

### 获取我的问卷列表

`GET /surveys?status=&keyword=`

查询参数：

- `status`：可选，`draft` / `live` / `paused` / `ended`
- `keyword`：可选，标题关键字

响应示例：

```json
{
  "items": [
    {
      "id": "s_12",
      "title": "城市通勤满意度问卷",
      "subtitle": "了解通勤体验",
      "status": "draft",
      "completed": 0,
      "target": 0,
      "updated_at": "2026-03-18",
      "created_at": "2026-03-18T08:00:00Z"
    }
  ]
}
```

---

### 创建问卷（兼容入口）

`POST /surveys`

请求体示例：

```json
{
  "title": "员工餐厅满意度调查",
  "description": "了解员工对食堂的满意度",
  "reward_points": 100,
  "estimated_minutes": 15,
  "deadline": "2026-03-30T00:00:00Z"
}
```

说明：

- 当前实现会直接创建为已发布状态并扣除 `reward_points`。
- 建议新流程使用“草稿 + publish”接口（见 `API-问卷管理.md` 与 `API-问卷制作.md`）。

响应示例：

```json
{
  "id": "s_34",
  "status": "active"
}
```

---

### 获取问卷详情

`GET /surveys/{survey_id}`

响应示例：

```json
{
  "id": "s_34",
  "title": "员工餐厅满意度调查",
  "subtitle": "了解员工对食堂的满意度",
  "description": "了解员工对食堂的满意度",
  "link": null,
  "reward_points": 100,
  "estimated_minutes": 15,
  "deadline": "2026-03-30T00:00:00Z",
  "status": "live",
  "created_at": "2026-03-18T08:00:00Z",
  "updated_at": "2026-03-18",
  "owner_id": "u_1",
  "completed": 12,
  "target": 100
}
```

---

### 删除问卷

`DELETE /surveys/{survey_id}`

响应示例：

```json
{
  "success": true,
  "refund": 80
}
```

说明：

- 对已发布/暂停问卷会按当前规则计算可退还积分。

---

### 关闭问卷（兼容入口）

`POST /surveys/{survey_id}/close`

响应示例：

```json
{
  "id": "34",
  "status": "active"
}
```

说明：

- 当前兼容入口会直接创建已发布问卷并扣除 `reward_points`。
- 新的草稿发布流程请使用 `API-问卷管理.md` 中的 `POST /surveys/{survey_id}/publish`。

说明：

- 该接口来自兼容逻辑。
- 主管理流程推荐使用 `pause/resume/cancel`。

---

## 常见错误码

- `401` 未登录或 Token 过期
- `403` 非资源所有者
- `404` 问卷不存在
- `405` 请求方法不允许
- `409` 状态冲突（如非草稿发布）
- `422` 参数校验失败

