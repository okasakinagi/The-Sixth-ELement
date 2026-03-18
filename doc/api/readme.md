# API 文档

本目录为《第六元素》后端 API 文档索引，已按当前代码实现口径修订。

## 文档索引

1. **[API-总览.md](API-总览.md)**
   - 多应用挂载结构
   - 全量接口分组
   - 主流程口径（提交即发奖）

2. **[API-认证.md](API-认证.md)**
   - 注册验证码、注册、登录
   - 重置验证码、重置密码

3. **[API-用户和问卷基础.md](API-用户和问卷基础.md)**
   - `GET/PATCH /users/me`
   - `GET/POST /surveys`
   - `GET/DELETE /surveys/{id}`
   - `POST /surveys/{id}/close`（兼容）

4. **[API-问卷管理.md](API-问卷管理.md)**
   - 草稿、发布、暂停、恢复、取消、统计

5. **[API-问卷制作.md](API-问卷制作.md)**
   - 草稿创建、读取、保存、AI 生成题目

6. **[API-问卷填写.md](API-问卷填写.md)**
   - `GET /surveys/{id}/fill`
   - `POST /surveys/{id}/fills`

7. **[API-答卷提交和审核.md](API-答卷提交和审核.md)**
   - 填答记录查询
   - 审核接口兼容说明

8. **[API-任务大厅.md](API-任务大厅.md)**
   - `overview / tasks / batch/refresh / guest-tasks`

9. **[API-数据分析.md](API-数据分析.md)**
   - `summary / questions / export`

10. **[API-积分和举报.md](API-积分和举报.md)**
    - 积分接口双入口说明
    - 举报接口说明

11. **[API-个人界面.md](API-个人界面.md)**
    - `GET/PATCH/PUT /users/me/profile`
    - `GET /users/me/profile/matches`

12. **[API-内部.md](API-内部.md)**
    - 向量/相似度内部接口

## 基础约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token
- 时间格式：ISO 8601（UTC）

请求头示例：

```text
Authorization: Bearer <access_token>
```

## 说明

1. 文档中的“主流程”均以当前前端依赖路径为准。
2. 兼容接口（如 `POST /fills/{id}/review`）会保留说明，但会明确其非主流程身份。
3. 如需调整接口契约，需同步更新：控制器/服务代码 + 本目录对应文档。

---

最后更新：2026-03-18
