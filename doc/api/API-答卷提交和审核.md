# 答卷提交与审核 API

本文档描述答卷提交、我的填写记录和兼容审核接口。当前主流程是提交后立即发奖，审核接口仅用于兼容旧流程。

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token

## 1. 答卷提交

### 提交答卷

`POST /surveys/{survey_id}/fills`

说明：

- 这是主流程。
- 提交成功后会立即写入积分流水并发奖。

## 2. 填写记录

### 获取我的填写记录

`GET /fills/me`

查询参数：

- `status`
- `page`
- `page_size`

响应条目只包含：

- `id`
- `survey_id`
- `status`
- `created_at`

## 3. 审核接口（兼容）

### 审核答卷

`POST /fills/{fill_id}/review`

请求体：

```json
{
  "status": "approved"
}
```

说明：

- 仅问卷所有者可审核。
- 只有 `submitted` 状态的记录可以审核。
- `approved` 时会给填写者发放问卷 `reward_points`，并增加相同数值的 `activity_points`。
- `rejected` 时不发奖。
- 该接口不是当前主流程依赖点。

## 常见错误码

- `401` 未登录或 Token 过期
- `403` 权限不足
- `404` 填写记录不存在
- `405` 方法不允许
- `422` 参数错误或记录已审核
