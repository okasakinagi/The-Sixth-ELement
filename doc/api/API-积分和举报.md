# 积分与举报 API

本文档描述积分汇总、积分流水、积分趋势、积分调整与举报接口。

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token

## 1. 积分接口

当前项目保留两套积分入口：

1. `core` 的 legacy 口径，主要用于兼容旧页面。
2. `points_record` 的新口径，提供汇总、流水、趋势和更新。

### 积分汇总

`GET /points/summary`

响应示例：

```json
{
  "user": {
    "id": "u_1",
    "nickname": "Alice",
    "points": 150,
    "activity_points": 200
  },
  "summary": {
    "total_points": 150,
    "total_activity_points": 200,
    "recent_earned": 80,
    "recent_spent": 20
  }
}
```

### 积分流水

`GET /points/logs`

查询参数：

- `type`
- `start_date`
- `end_date`
- `keyword`
- `sort`
- `page`
- `page_size`

说明：

- `points_record` 版本返回 `type`、`delta`、`balance`、`reason`、`ref_type`、`ref_id`。
- legacy 版本会补充 `related_id`、`related_type` 的最佳努力推断字段。

### 积分趋势

`GET /points/trend?granularity=day&days=30`

参数：

- `granularity`：`day` / `week` / `month`
- `days`：默认 30，最大 365

### 更新积分

`POST /points/update`

请求体：

```json
{
  "delta": 10,
  "reason": "活动奖励",
  "ref_type": "admin_adjust",
  "ref_id": "evt_01"
}
```

说明：

- `delta` 为正时会同时增加 `activity_points`。
- 这是管理用途接口，不是前端主流程。

## 2. 举报接口

### 创建举报

`POST /reports`

请求体：

```json
{
  "target_type": "survey",
  "target_id": "34",
  "reason": "问卷内容违反平台规范"
}
```

说明：

- `target_type` 只能是 `survey` 或 `user`。
- `target_id` 会被解析为整数 ID。

## 3. 当前业务口径

- 发布问卷会写入负向积分流水。
- 填写问卷会写入正向积分流水，并立即发放。
- 如果填写者属于有效队伍且不是队长，奖励会转到队长账户。

## 常见错误码

- `401` 未登录或 Token 过期
- `404` 资源不存在
- `405` 方法不允许
- `422` 参数校验失败
