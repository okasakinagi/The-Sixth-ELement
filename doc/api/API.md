## API 总览

本文件为早期总览草案，当前以 [API-总览.md](API-总览.md) 和 [readme.md](readme.md) 为准。下面仅保留历史索引，避免旧链接失效。

- 个人主页/编辑资料：doc/api/API-个人界面.md
- 任务大厅：doc/api/API-任务大厅.md
- 问卷管理：doc/api/API-问卷管理.md
- 问卷制作 + AI 编辑器：doc/api/API-问卷制作.md
- 问卷填写：doc/api/API-问卷填写.md
- 问卷数据分析：doc/api/API-数据分析.md

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

- 2026-04-01：标记为历史草案，建议优先阅读 API-总览.md
