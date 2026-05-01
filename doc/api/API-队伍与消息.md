# 队伍与消息 API

本文档描述队伍管理、邀请、消息中心和积分赠送接口。当前模块挂载在 `/api/v1` 下，全部使用 Bearer Token 鉴权。

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token

## 1. 队伍管理

### 创建队伍

`POST /teams`

### 获取我的队伍

`GET /teams/mine`

### 获取队伍详情

`GET /teams/{team_id}`

### 获取队伍成员

`GET /teams/{team_id}/members`

### 更新队伍

`PATCH /teams/{team_id}/update`

### 解散队伍

`DELETE /teams/{team_id}/delete`

### 移除成员

`DELETE /teams/{team_id}/members/{user_id}/remove`

### 设置成员角色

`PATCH /teams/{team_id}/members/{user_id}/role`

## 2. 队伍邀请

### 发送邀请

`POST /teams/{team_id}/invite`

请求体：

```json
{
  "invitee_id": 2
}
```

### 获取邀请列表

`GET /invitations`

### 接受邀请

`PATCH /invitations/{invitation_id}/accept`

### 拒绝邀请

`PATCH /invitations/{invitation_id}/reject`

### 检查邀请冷却

`GET /teams/{team_id}/invite/{invitee_id}/cooldown`

## 3. 消息中心

### 获取消息列表

`GET /messages`

查询参数：

- `page`
- `page_size`
- `type`
- `status`

### 获取未读数

`GET /messages/unread-count`

### 标记已读

`PATCH /messages/{message_id}/read`

### 删除消息

`DELETE /messages/{message_id}/delete`

## 4. 积分赠送

### 赠送积分

`POST /messages/points-gift`

请求体：

```json
{
  "receiver_id": 2,
  "points_amount": 10,
  "message": "辛苦了"
}
```

### 获取赠送额度

`GET /messages/points-gift/limit`

## 当前业务口径

- 队伍侧采用单队伍模式，`/teams/mine` 是个人当前队伍入口。
- 邀请接口带冷却检查。
- 积分赠送有日限额控制。

## 常见错误码

- `401` 未登录或 Token 过期
- `403` 权限不足
- `404` 资源不存在
- `409` 冷却或状态冲突
- `422` 参数校验失败
