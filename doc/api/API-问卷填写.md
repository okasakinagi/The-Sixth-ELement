# 问卷填写 API

本文档描述问卷详情获取、答卷提交与奖励入账接口。当前主流程是“提交即发奖”，不是提交后审核发奖。

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：答卷提交需要 Bearer Token；填写页详情可匿名打开
- 时间格式：ISO 8601

## 1. 获取问卷详情

### 获取填写页数据

`GET /surveys/{survey_id}/fill`

说明：

- 该接口返回题目列表，用于渲染填写页。
- 当前实现允许匿名访问；如果请求里带有已登录用户，会记录点击行为。

响应示例：

```json
{
  "id": "34",
  "title": "城市通勤满意度问卷",
  "subtitle": "了解通勤体验与痛点",
  "questions": [
    {
      "id": "q_1",
      "type": "single",
      "title": "您常用的通勤方式是？",
      "options": ["地铁", "公交", "自驾", "骑行"],
      "required": true,
      "order": 1
    }
  ]
}
```

## 2. 提交答卷

### 提交答卷

`POST /surveys/{survey_id}/fills`

请求体：

```json
{
  "duration_seconds": 180,
  "answers": [
    {
      "question_id": "q_1",
      "value": "地铁"
    }
  ]
}
```

响应示例：

```json
{
  "id": "f_abc123",
  "status": "submitted",
  "points_awarded": 5,
  "points_expected": 5,
  "points_receiver_id": "u_1",
  "points_receiver_nickname": "队长昵称",
  "points_flow": "team_owner",
  "points_flow_message": "你已加入队伍，积分已自动入账到队长 队长昵称"
}
```

说明：

- `duration_seconds` 不能少于 10 秒。
- 同一用户对同一问卷只能提交一次。
- 不能填写自己发布的问卷。
- 如果提交者已加入有效队伍且不是队长，奖励会记到队长账户。
- 提交成功后，`activity_points` 仍会增加。

## 3. 当前校验规则

- 问卷必须处于 `published`。
- 问卷必须已经有已发布的内容。
- 必答题不能为空。
- 单选/多选答案必须匹配题目选项。

## 常见错误码

- `401` 未登录或 Token 过期
- `404` 问卷不存在
- `405` 方法不允许
- `422` 问卷不可填写、自己问卷、已提交过、时长过短或答案非法
