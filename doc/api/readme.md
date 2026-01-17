# 接口文档（草案）

本接口文档用于问卷互填 App 的服务端 API 规划，默认采用 JSON 进行请求与响应。本文档为草案，可根据实际后端框架与鉴权方式调整。

## 约定
- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token（登录后获取）
- 时间格式：ISO 8601（例如 `2024-01-01T12:00:00Z`）

## 文档索引

- API 总览：doc/api/API.md
- 个人主页/编辑资料：doc/api/API-个人界面.md
- 任务大厅：doc/api/API-任务大厅.md
- 问卷管理：doc/api/API-问卷管理.md
- 问卷制作 + AI 编辑器：doc/api/API-问卷制作.md
- 问卷填写：doc/api/API-问卷填写.md
- 问卷数据分析：doc/api/API-数据分析.md

## 通用错误码（示例）
- `401` 未认证或 Token 过期
- `403` 权限不足
- `404` 资源不存在
- `422` 参数校验失败
- `429` 触发频率限制
- `500` 服务器内部错误
