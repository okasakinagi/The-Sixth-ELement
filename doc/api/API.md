## API 总览

本文件为后端 API 的总览文档（草案），用于前后端对齐接口与字段。更细的页面级接口说明请见：

- 个人主页/编辑资料：doc/api/API-个人界面.md

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token
  - Header：`Authorization: Bearer <access_token>`
- 时间格式：ISO 8601（例如 `2024-01-01T12:00:00Z`）

### 通用错误响应（建议）

```json
{
  "error": {
    "code": "validation_error",
    "message": "参数校验失败",
    "details": {
      "field": ["错误原因"]
    }
  }
}
```

### 通用错误码（示例）

- `401` 未认证或 Token 过期
- `403` 权限不足
- `404` 资源不存在
- `422` 参数校验失败
- `429` 触发频率限制
- `500` 服务器内部错误

---

## 变更记录

- 2024-01-01：初始化版本
