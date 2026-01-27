# API 文档

本目录包含《第六元素》问卷交换平台的完整 API 文档。

## 📚 文档索引

### ✅ 已实现的接口（可直接使用）

1. **[API-总览.md](API-总览.md)** - API 整体说明、业务流程、资源定义
   - 包含全部接口速查表和常见问题解答

2. **[API-认证.md](API-认证.md)** - 用户认证（2 个接口）
   - POST /auth/register - 用户注册
   - POST /auth/login - 用户登录

3. **[API-用户和问卷基础.md](API-用户和问卷基础.md)** - 用户与问卷基础（6 个接口）
   - GET /users/me - 获取当前用户信息
   - PATCH /users/me - 更新用户信息
   - GET /surveys - 获取问卷列表
   - GET /surveys/{id} - 获取问卷详情
   - POST /surveys - 创建并发布问卷
   - POST /surveys/{id}/close - 关闭问卷

4. **[API-答卷提交和审核.md](API-答卷提交和审核.md)** - 答卷操作（3 个接口）
   - POST /surveys/{id}/fills - 提交答卷
   - GET /fills/me - 获取我的填写记录
   - POST /fills/{id}/review - 审核答卷

5. **[API-积分和举报.md](API-积分和举报.md)** - 积分与举报（2 个接口）
   - GET /points/logs - 获取积分流水
   - POST /reports - 创建举报

**已实现总数：13 个接口**

---

### 🚧 规划中的接口（后续需要实现）

1. **[API-个人界面.md](API-个人界面.md)** - 个人主页/编辑资料（2 个接口）
   - GET /users/me/profile - 获取用户画像
   - PATCH /users/me/profile - 更新用户画像

2. **[API-任务大厅.md](API-任务大厅.md)** - 任务大厅（3 个接口）
   - GET /task-hall/overview - 获取任务大厅概览
   - GET /task-hall/tasks - 获取任务列表
   - POST /task-hall/batch/refresh - 换一批/补位

3. **[API-问卷管理.md](API-问卷管理.md)** - 问卷列表管理（4 个接口）
   - GET /surveys/summary - 获取问卷统计
   - DELETE /surveys/{id} - 删除问卷
   - POST /surveys/{id}/pause - 暂停问卷
   - POST /surveys/{id}/resume - 恢复问卷

4. **[API-问卷制作.md](API-问卷制作.md)** - 问卷草稿与 AI（5 个接口）
   - POST /surveys/drafts - 创建草稿
   - GET /surveys/drafts/{id} - 获取草稿
   - PATCH /surveys/drafts/{id} - 保存草稿
   - POST /surveys/drafts/{id}/ai-generate - AI 生成题目
   - DELETE /surveys/drafts/{id}/questions/{q_id} - 删除题目

5. **[API-问卷填写.md](API-问卷填写.md)** - 问卷填写界面（1 个接口）
   - GET /surveys/{id}/fill - 获取填写界面问卷

6. **[API-数据分析.md](API-数据分析.md)** - 问卷数据分析（3 个接口）
   - GET /surveys/{id}/analytics/summary - 获取分析概览
   - GET /surveys/{id}/analytics/questions - 获取题目统计
   - POST /surveys/{id}/analytics/export - 导出数据

**规划总数：18 个接口**

---

## 🔑 基础约定

- **Base URL**：`/api/v1`
- **Content-Type**：`application/json`
- **认证方式**：Bearer Token
  - 在请求头添加：`Authorization: Bearer <access_token>`
- **时间格式**：ISO 8601 with Z timezone（例如 `2026-01-21T10:30:00Z`）

## 🚀 快速开始

### 1. 注册/登录

```bash
# 注册
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pwd","nickname":"Alice"}'

# 登录
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pwd"}'
```

获得 `access_token` 后，在后续请求中添加：
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### 2. 浏览与填答问卷

```bash
# 获取问卷列表
curl -X GET "http://127.0.0.1:8000/api/v1/surveys?page=1" \
  -H "Authorization: Bearer TOKEN"

# 提交答卷
curl -X POST http://127.0.0.1:8000/api/v1/surveys/s_xxx/fills \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"duration_seconds":180}'
```

### 3. 发布问卷

```bash
# 发布问卷
curl -X POST http://127.0.0.1:8000/api/v1/surveys \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"问卷标题",
    "link":"https://forms.gle/xxx",
    "reward_points":50,
    "estimated_minutes":10
  }'
```

### 4. 审核答卷

```bash
# 批准答卷
curl -X POST http://127.0.0.1:8000/api/v1/fills/f_xxx/review \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"approved"}'
```

---

## 📋 HTTP 状态码

| 状态码 | 含义 |
|--------|------|
| 200 | 成功 |
| 401 | 未认证或 Token 过期 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 405 | 方法不允许 |
| 422 | 参数校验失败 |
| 500 | 服务器内部错误 |

## 📖 详细说明

- 所有接口的参数、响应、错误码详见各个专题文档
- 前端集成指南见 [API-总览.md](API-总览.md) 的"常见业务流程"和"前端接入指南"部分
- 常见问题见各专题文档末尾的"常见问题"部分

---

**最后更新**：2026-01-21  
**版本**：v1.0 完整文档
