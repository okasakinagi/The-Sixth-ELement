# 个人界面 API（UserProfileView / EditProfileView）

本文档按 RESTful 设计逻辑，描述“个人主页（展示）”与“编辑资料（填写/更新画像）”两个界面所需的接口。

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token
  - Header：`Authorization: Bearer <access_token>`
- 时间格式：ISO 8601

## 资源设计

### 1) 当前用户（账号基础信息）
- 资源：`/users/me`
- 语义：账号层面的昵称、学校、标签、积分等（不包含详细画像字段）

### 2) 当前用户画像（个人主页/匹配画像）
- 资源：`/users/me/profile`
- 语义：用于匹配推荐的详细画像字段（性别/学院/专业/兴趣/技能等）

> 说明：为避免 `GET /users/me` 越来越臃肿，这里将“画像”拆为独立子资源。

---

## 数据模型（建议）

### User（基础）

```json
{
  "id": "u_123",
  "nickname": "Alice",
  "school": "某大学",
  "tags": ["心理学", "产品"],
  "credit_score": 80,
  "points": 120,
  "activity_points": 56
}
```

### UserProfile（画像）

```json
{
  "user_id": "u_123",
  "gender": "secret",
  "age": 20,
  "grade": "大二",
  "college": "计算机科学学院",
  "major": "计算机科学与技术",

  "mbti": "INTJ",
  "interests": "人工智能、德语初级",
  "organizations": "校学生会、摄影社",

  "consumption_preferences": ["数码", "奶茶"],
  "career_intention": ["考公", "大厂"],
  "skills": ["Python", "视频剪辑"],

  "current_status": "正在备战期末",

  "profile_completion": 67,
  "updated_at": "2024-01-01T12:00:00Z"
}
```

- `gender`：建议枚举：`male` / `female` / `other` / `secret`
- `mbti`：建议枚举 16 种（`INTJ`...`ESFP`），也可允许为空
- `profile_completion`：可由后端计算（0-100），也可由前端计算（若后端不提供）

### 字段长度与约束（建议，非强制）

- `college`：<= 50
- `major`：<= 50
- `interests`：<= 200
- `organizations`：<= 200
- `current_status`：<= 100
- `consumption_preferences` / `career_intention` / `skills`：数组长度建议 <= 20，每个元素 <= 20

---

## 页面：个人主页（展示） UserProfileView

### 获取当前用户基础信息

`GET /users/me`

响应体：

```json
{
  "id": "u_123",
  "nickname": "Alice",
  "credit_score": 80,
  "points": 120,
  "activity_points": 56
}
```

### 获取当前用户画像（用于展示与匹配）

`GET /users/me/profile`

响应体：

```json
{
  "user_id": "u_123",
  "gender": "secret",
  "age": 20,
  "grade": "大二",
  "college": "计算机科学学院",
  "major": "计算机科学与技术",
  "mbti": "INTJ",
  "interests": "人工智能、德语初级",
  "organizations": "校学生会、摄影社",
  "consumption_preferences": ["数码", "奶茶"],
  "career_intention": ["考公", "大厂"],
  "skills": ["Python", "视频剪辑"],
  "current_status": "正在备战期末",
  "profile_completion": 67,
  "updated_at": "2024-01-01T12:00:00Z"
}
```

> 前端建议：页面初始化时并发调用 `GET /users/me` 与 `GET /users/me/profile`，减少首屏等待。

---

## 页面：编辑资料 EditProfileView

### 更新当前用户画像（非强制填写）

`PATCH /users/me/profile`

说明：
- “非强制”策略：所有字段均可选；缺省字段不应被强制要求。
- `PATCH` 语义：仅更新传入字段；未传入字段保持不变。

请求体（示例）：

```json
{
  "gender": "female",
  "age": 19,
  "grade": "大一",
  "college": "物理学院",
  "major": "应用物理学",
  "mbti": "INFP",
  "interests": "人工智能、德语初级",
  "organizations": "校学生会、摄影社",
  "consumption_preferences": ["数码", "户外"],
  "career_intention": ["学术"],
  "skills": ["Python", "英语口译"],
  "current_status": "正在备战期末"
}
```

响应体：更新后的画像（字段同 `GET /users/me/profile`）。

###（可选）覆盖式更新画像

`PUT /users/me/profile`

说明：
- 若后端更偏好“整对象提交”，可提供 `PUT`。
- `PUT` 语义：客户端提交完整画像对象，后端用提交内容覆盖（未填字段将被置空/默认）。

---

## 匹配相关说明（与个人界面强相关）

- 学院/专业改为填空后，后端在匹配算法中应支持关键词模糊匹配
  - 示例：用户填写“计算机”，可匹配到“计算机科学与技术”相关标签/问卷

---

## 错误码（本页面常见）

- `401` 未登录或 Token 过期
- `422` 参数校验失败（如 `age` 非数字、数组元素过长等）

错误响应示例：

```json
{
  "error": {
    "code": "validation_error",
    "message": "参数校验失败",
    "details": {
      "age": ["must be between 0 and 120"],
      "major": ["max length is 50"]
    }
  }
}
```
