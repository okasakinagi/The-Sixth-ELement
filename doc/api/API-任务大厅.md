# 任务大厅 API（TaskHallView）

本文档描述“任务大厅”页面展示所需接口。当前前端为静态展示，后端可按需实现以下接口以支持动态内容。

## 约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token
- 时间格式：ISO 8601

---

## 页面数据

### 获取任务大厅概览

`GET /task-hall/overview`

响应体：

```json
{
  "user": {
    "nickname": "张三",
    "points": 1240
  },
  "modules": [
    {
      "key": "survey",
      "title": "问卷管理",
      "description": "管理问卷的全生命周期，从创建到分析。",
      "cta": "打开问卷管理",
      "route": "/surveys",
      "status": "active"
    },
    {
      "key": "market",
      "title": "任务市场",
      "description": "查看推荐任务、积分兑换与投放情况。",
      "cta": "即将上线",
      "route": null,
      "status": "coming"
    },
    {
      "key": "profile",
      "title": "个人中心",
      "description": "账号信息、积分流水、系统设置。",
      "cta": "前往个人信息",
      "route": "/profile",
      "status": "active"
    }
  ],
  "notices": [
    {
      "id": "n_01",
      "title": "新版本已上线",
      "content": "问卷制作支持 AI 生成题目。",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

字段说明：

- `modules[].status`：`active` / `coming` / `disabled`
- `route`：前端跳转路径（无则为 `null`）

### 字段校验 / 枚举表（建议）

| 字段 | 类型 | 约束 | 枚举/说明 |
| --- | --- | --- | --- |
| `user.nickname` | string | <= 20 | 昵称展示 |
| `user.points` | number | >= 0 | 积分余额 |
| `modules[].key` | string | <= 20 | 模块唯一键 |
| `modules[].title` | string | <= 30 | 模块标题 |
| `modules[].description` | string | <= 80 | 模块描述 |
| `modules[].cta` | string | <= 20 | 按钮文案 |
| `modules[].route` | string/null | 可选 | 前端路由 |
| `modules[].status` | string | 必填 | `active` / `coming` / `disabled` |
| `notices[].title` | string | <= 30 | 通知标题 |
| `notices[].content` | string | <= 120 | 通知内容 |

---

## 错误码（本页面常见）

- `401` 未登录或 Token 过期
- `500` 服务器内部错误
