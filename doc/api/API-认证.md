# 认证 API

本文档描述注册、登录、验证码与密码重置接口。当前实现使用 Bearer Token，注册和登录都会返回 `access_token`。

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 时间格式：ISO 8601

## 返回格式

注册/登录成功的响应：

```json
{
  "access_token": "GXl8_tZ...",
  "expires_in": 3600,
  "user": {
    "id": "1",
    "nickname": "Alice"
  }
}
```

## 接口

### 发送注册验证码

`POST /auth/send-register-code`

请求体：

```json
{
  "email": "alice@example.com"
}
```

成功响应：

```json
{
  "message": "verification code sent",
  "expires_in": 900
}
```

### 用户注册

`POST /auth/register`

请求体：

```json
{
  "email": "alice@example.com",
  "password": "securePassword123",
  "nickname": "Alice",
  "code": "123456"
}
```

规则：

- 邮箱、密码、昵称、验证码都不能为空。
- 密码长度至少 6 位。
- 注册成功后会创建用户，初始 `credit_score=80`、`points=20`、`activity_points=0`。

### 用户登录

`POST /auth/login`

请求体：

```json
{
  "email": "alice@example.com",
  "password": "securePassword123"
}
```

说明：

- 登录成功会刷新 token。
- 注册成功后也会自动下发 token。

### 发送重置验证码

`POST /auth/send-reset-code`

请求体：

```json
{
  "email": "alice@example.com"
}
```

### 重置密码

`POST /auth/reset-password`

请求体：

```json
{
  "email": "alice@example.com",
  "code": "123456",
  "new_password": "newSecurePassword123"
}
```

成功响应：

```json
{
  "message": "password reset successful",
  "user": {
    "id": "1",
    "nickname": "Alice"
  }
}
```

## 常见错误码

- `401` 凭证错误或验证码无效
- `404` 用户不存在
- `405` 方法不允许
- `422` 参数校验失败
- `429` 发送频率过高
- `500` 邮件发送失败
