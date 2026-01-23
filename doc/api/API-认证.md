# 认证 API（Register & Login）

本文档描述用户注册和登录相关接口。

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 时间格式：ISO 8601

---

## 数据模型

### 注册/登录响应

```json
{
  "access_token": "GXl8_tZ...（24位）",
  "expires_in": 3600,
  "user": {
    "id": "u_abc123...",
    "nickname": "Alice"
  }
}
```

### 用户信息响应

```json
{
  "id": "u_abc123...",
  "nickname": "Alice",
  "credit_score": 80,
  "points": 120,
  "activity_points": 56,
  "has_honor": false
}
```

---

## 注册接口

### 用户注册

**请求：**

```
POST /auth/register
Content-Type: application/json

{
  "email": "alice@example.com",
  "password": "securePassword123",
  "nickname": "Alice"
}
```

**参数说明：**

| 参数 | 类型 | 约束 | 说明 |
|------|------|------|------|
| email | string | 必填，<=128 | 邮箱地址，唯一 |
| password | string | 必填，<=128 | 密码（明文存储，需自行加密） |
| nickname | string | 必填，<=64 | 昵称 |

**响应体：**

```json
{
  "access_token": "GXl8_tZ9AQ7kR...",
  "expires_in": 3600,
  "user": {
    "id": "u_550e8400e29b41d4a716446655440000",
    "nickname": "Alice"
  }
}
```

**响应说明：**

- `access_token`：用于后续请求的 Bearer Token
- `expires_in`：token 有效期（秒），当前固定 3600 秒
- `user.id`：系统生成的用户唯一ID（前缀 `u_`）

**错误响应：**

```json
{
  "error": "email already registered"
}
```

**可能的错误码：**

- `405` 方法不允许（非 POST）
- `422` 参数校验失败：`email, password, nickname required`
- `422` 邮箱已注册：`email already registered`

---

## 登录接口

### 用户登录

**请求：**

```
POST /auth/login
Content-Type: application/json

{
  "email": "alice@example.com",
  "password": "securePassword123"
}
```

**参数说明：**

| 参数 | 类型 | 约束 | 说明 |
|------|------|------|------|
| email | string | 必填，<=128 | 邮箱地址 |
| password | string | 必填，<=128 | 密码 |

**响应体：**

```json
{
  "access_token": "GXl8_tZ9AQ7kR...",
  "expires_in": 3600,
  "user": {
    "id": "u_550e8400e29b41d4a716446655440000",
    "nickname": "Alice"
  }
}
```

**响应说明：**

- 登录成功会生成新的 `access_token`，覆盖之前的 token
- 每次登录都重新生成 token

**错误响应：**

```json
{
  "error": "invalid credentials"
}
```

**可能的错误码：**

- `405` 方法不允许（非 POST）
- `422` 参数校验失败：`email and password required`
- `401` 凭证错误：`invalid credentials`

---

## 前端接入指南

### 保存 Token

登录/注册后，前端应将 `access_token` 保存到 `localStorage`：

```javascript
localStorage.setItem('accessToken', response.access_token);
localStorage.setItem('user', JSON.stringify(response.user));
```

### 使用 Token

后续请求时，将 token 添加到请求头：

```javascript
fetch('/api/v1/users/me', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
    'Content-Type': 'application/json'
  }
})
```

### Token 过期处理

如果收到 `401` 错误，应提示用户重新登录：

```javascript
if (response.status === 401) {
  localStorage.removeItem('accessToken');
  localStorage.removeItem('user');
  // 跳转到登录页
  window.location.href = '/auth';
}
```

---

## 初始值说明

新注册用户的初始状态：

| 字段 | 初始值 | 说明 |
|------|--------|------|
| credit_score | 80 | 信用分（范围 0-100） |
| points | 20 | 积分（可用于发布问卷） |
| activity_points | 0 | 活跃度积分（记录贡献） |
| school | 空 | 学校（后期补充） |
| tags | 空 | 标签（后期补充） |

