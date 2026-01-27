# 任务大厅 API（TaskHallView）

本文档描述“任务大厅”页面所需接口，并按照后端分层设计规范给出落地建议。

## 一、分层设计说明（先懂“每层干嘛”，再懂“为什么要分”）

> 这是后端开发的通用架构思想，**在 Java Spring Boot 中尤为明确**，在 **Python Django/Flask** 中也有对应实现，只是命名与封装略有不同，核心逻辑一致。

### 1. 分层核心职责

| 分层 | 核心职责 | 通俗理解（以任务大厅为例） |
| --- | --- | --- |
| Controller（控制器层） | 1) 接收 HTTP 请求 2) 参数校验（必填/格式） 3) 调用 Service 4) 统一封装响应 | 「前台接待员」：只负责接待用户、转交请求、返回结果。例如：接收“任务大厅列表”的请求，校验分页/筛选参数，然后调用服务层获取数据。 |
| Service（服务层） | 1) 实现业务逻辑 2) 组织多数据源 3) 业务规则校验 | 「核心业务处理员」：负责“任务大厅的推荐/筛选/排序/可见性规则”。例如：根据用户画像生成推荐理由、计算匹配度等。 |
| DAO（数据访问接口层） | 1) 定义数据访问方法 2) 不关心具体数据库 | 「数据访问规范制定者」：定义“查询可参与问卷”“统计任务进度”等接口。 |
| Mapper（映射层） | 1) 实现 DAO 2) SQL/ORM 查询 3) 封装结果集 | 「数据访问执行者」：把数据库查询结果转换成任务卡片所需的数据结构。 |

**Django/Flask 对应关系（轻量落地）**

- Controller：Django/DRF 的 `APIView`/`ViewSet` 或 Flask 的 `Blueprint` + `Route`
- Service：`services/` 目录中的业务类（如 `TaskHallService`）
- DAO + Mapper：Django `Model` + `Manager`（或 SQLAlchemy `Model` + `Repository`）

### 2. 为什么要分层（核心价值）

1) **职责单一**：避免所有逻辑混在 views 里，易于定位与维护。
2) **解耦复用**：同一业务逻辑可被多个接口复用（如任务推荐/匹配算法）。
3) **便于测试**：可独立测试 Service，无需启动整个 Web 服务。
4) **团队协作**：多人并行开发，冲突减少。
5) **易扩展**：规则变更只影响对应层，降低迭代成本。

---

## 二、约定

- Base URL：`/api/v1`
- Content-Type：`application/json`
- 认证方式：Bearer Token
- 时间格式：ISO 8601

---

## 三、数据模型（任务卡片）

任务大厅的“任务”本质上是可参与的问卷，以下为前端卡片所需的统一数据结构。

### TaskCard（任务卡片）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 任务ID（可复用问卷ID，前缀 `s_`） |
| title | string | 任务标题（问卷标题） |
| subtitle | string | 任务副标题/简介 |
| sender | string | 发布者昵称或组织名 |
| type | string | 类型（如：校园调研/教学反馈，来源 Tag.type=survey_type） |
| estimated | number | 预计耗时（分钟） |
| difficulty | number | 难度 1-5 |
| reward | number | 奖励积分 |
| filled | number | 已完成份数（来源：Response 提交统计） |
| total | number | 目标份数（来源：Survey.target） |
| deadline | string/null | 截止时间 |
| status | string | `active`/`closed`/`full` |
| match_level | string | `high`/`medium`/`low`（推荐匹配度） |
| match_reason | string | 推荐理由（可选） |

---

## 四、接口设计

### 1) 获取任务大厅概览

`GET /task-hall/overview`

用于页面顶部信息（用户积分、统计、筛选项、公告）。

**响应体示例：**

```json
{
  "user": {
    "id": "u_123",
    "nickname": "张三",
    "points": 1240
  },
  "summary": {
    "available_tasks": 328,
    "new_tasks_today": 26,
    "high_match_tasks": 14
  },
  "filters": {
    "types": ["校园调研", "教学反馈", "活动报名", "投票"],
    "difficulties": [1, 2, 3, 4, 5]
  },
  "notices": [
    {
      "id": "n_01",
      "title": "新版本已上线",
      "content": "问卷制作支持 AI 生成题目。",
      "created_at": "2026-01-21T12:00:00Z"
    }
  ]
}
```

**可能的错误码：**
- `401` 未登录或 Token 过期
- `500` 服务器内部错误

---

### 2) 获取任务列表（任务大厅主列表）

`GET /task-hall/tasks`

支持关键词检索、筛选、排序与分页。

**查询参数：**

| 参数 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| keyword | string | 可选 | 关键词搜索（标题/副标题/发布者） |
| type | string | 可选 | 类型筛选 |
| difficulty | number | 可选 | 难度 1-5 |
| min_reward | number | 可选 | 最低奖励积分 |
| max_minutes | number | 可选 | 最大耗时 |
| status | string | 可选 | `active`/`closed`/`full` |
| sort | string | 可选 | `recommend`/`reward_desc`/`newest`/`ending` |
| page | number | 默认 1 | 页码 |
| page_size | number | 默认 20，最大 50 | 每页数量 |

**响应体示例：**

```json
{
  "items": [
    {
      "id": "s_t01",
      "title": "校园生活满意度调查",
      "subtitle": "宿舍、食堂、安保整体反馈",
      "sender": "李同学",
      "type": "校园调研",
      "estimated": 6,
      "difficulty": 2,
      "reward": 3,
      "filled": 54,
      "total": 200,
      "deadline": "2026-02-15T00:00:00Z",
      "status": "active",
      "match_level": "high",
      "match_reason": "与你的兴趣标签匹配"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 328
}
```

**可能的错误码：**
- `401` 未登录或 Token 过期
- `422` 参数校验失败

---

### 3) 换一批 / 删除补位（批量刷新）

`POST /task-hall/batch/refresh`

用于“换一批”或“删除后补位”的场景：
- 换一批：传当前可见任务 ID，返回全新批次
- 删除补位：传当前可见任务 ID + 需要补位数量

**请求体：**

```json
{
  "exclude_task_ids": ["s_t01", "s_t02", "s_t03"],
  "batch_size": 15
}
```

**响应体：**

```json
{
  "items": [
    {
      "id": "s_t20",
      "title": "实习就业意向",
      "subtitle": "求职方向、城市与行业偏好",
      "sender": "就业中心",
      "type": "就业调研",
      "estimated": 7,
      "difficulty": 3,
      "reward": 4,
      "filled": 45,
      "total": 120,
      "deadline": "2026-02-18T00:00:00Z",
      "status": "active",
      "match_level": "medium",
      "match_reason": "与你的专业匹配"
    }
  ]
}
```

**可能的错误码：**
- `401` 未登录或 Token 过期
- `422` 参数校验失败

---

## 五、分层落地建议（任务大厅）

### Controller（views.py）
- 只做参数校验与权限校验
- 调用 `TaskHallService.get_overview()` / `list_tasks()` / `refresh_batch()`
- 统一响应结构

### Service（services/task_hall_service.py）
- 实现推荐逻辑（基于用户画像、行为、热门度）
- 组装任务卡片数据（合并 Survey + 用户信息 + 统计数据）
- 处理排序、过滤、分页

### DAO/Mapper（models.py + managers.py）
- `SurveyManager.list_available_tasks(filters)`
- `SurveyManager.get_task_stats(survey_ids)`
- `NoticeManager.latest_notices(limit)`

> Django 中可通过 `Model` + `Manager` 来实现 DAO/Mapper，避免手写 SQL，同时保持分层思路。

---

## 六、字段校验 / 枚举表（建议）

| 字段 | 类型 | 约束 | 枚举/说明 |
| --- | --- | --- | --- |
| user.nickname | string | <= 20 | 昵称展示 |
| user.points | number | >= 0 | 积分余额 |
| task.type | string | <= 20 | 任务类型 |
| task.difficulty | number | 1-5 | 难度等级 |
| task.match_level | string | 必填 | `high` / `medium` / `low` |
| task.status | string | 必填 | `active` / `closed` / `full` |
| notices[].title | string | <= 30 | 通知标题 |
| notices[].content | string | <= 120 | 通知内容 |

---

## 七、错误码（本页面常见）

- `401` 未登录或 Token 过期
- `422` 参数校验失败
- `500` 服务器内部错误
