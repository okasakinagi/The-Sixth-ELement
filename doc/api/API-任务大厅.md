# 任务大厅 API

本文档描述任务大厅、每日推荐、等级任务和任务奖励接口。当前实现不再强调旧的分层叙述，重点是实际可用路由。

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token，除访客任务外其余接口都需要登录

## 1. 任务大厅

### 获取大厅概览

`GET /task-hall/overview`

响应包含：

- `user`：当前用户的 `id`、`nickname`、`points`
- `summary`：任务统计概览
- `filters`：筛选项
- `notices`：公告列表

### 获取首页模块

`GET /task-hall/home-modules`

说明：

- 登录用户返回个性化模块。
- 访客返回降级内容。
- 当前模块主要是 `feed` 和 `trending`。

### 获取任务列表

`GET /task-hall/tasks`

查询参数：

- `keyword`
- `type`
- `difficulty`
- `min_reward`
- `max_minutes`
- `status`
- `sort`
- `page`
- `page_size`

### 换一批

`POST /task-hall/batch/refresh`

请求体：

```json
{
  "exclude_task_ids": ["s_1", "s_2"],
  "batch_size": 15
}
```

### 访客任务

`GET /task-hall/guest-tasks?size=15`

说明：

- 无需认证。
- `size` 限制在 1 到 30。

### 每日推荐

`GET /task-hall/daily-recommendations`

说明：

- 返回当前用户当天的 5 个推荐问卷。
- 结果按天缓存。

### 领取每日推荐奖励

`POST /task-hall/daily-recommendations/{survey_id}/claim-bonus`

说明：

- `survey_id` 兼容 `123` 和 `s_123` 两种格式。
- 成功后会额外发放 `activity_points +2`、`points +1`。

## 2. 等级与任务

### 获取等级信息

`GET /user/level`

### 获取日任务

`GET /tasks/daily`

### 获取周任务

`GET /tasks/weekly`

### 领取任务奖励

`POST /tasks/{task_code}/claim`

任务编码示例：

- `daily_login`
- `daily_fill_1`
- `daily_fill_3`
- `weekly_fill_10`
- `weekly_publish_1`

## 3. 当前关键业务口径

1. 任务大厅主列表和首页模块都基于当前用户的推荐结果或降级随机结果。
2. 每日推荐完成后可领取额外奖励。
3. 等级系统把 `activity_points` 作为经验值来源。
4. 登录、完成问卷、发布问卷都会推动任务进度。

## 常见错误码

- `401` 未登录或 Token 过期
- `404` 资源不存在
- `409` 状态冲突
- `422` 参数校验失败
