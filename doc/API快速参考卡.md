# API 快速参考卡

## 🎯 核心三步流程

### 1️⃣ 认证（必须）
```bash
# 注册或登录获取 token
POST /auth/register | POST /auth/login
↓
得到 access_token
↓
# 后续所有请求都需要加上
Authorization: Bearer <access_token>
```

### 2️⃣ 核心操作（按角色）

**A. 发布者：创建草稿并发布**
```bash
POST /surveys/drafts
{
  "title": "问卷标题"
}
↓
PATCH /surveys/drafts/{id}   # 写入题目
↓
POST /surveys/{id}/publish
{
  "reward_points": 5,
  "budget_points": 600,
  "target": 120
}
↓
扣费：user.points -= budget_points
```

**B. 填答问卷**
```bash
GET /task-hall/tasks                # 浏览推荐任务
↓
GET /surveys/{id}/fill              # 获取可填写问卷
↓
POST /surveys/{id}/fills            # 提交答卷
{
  "duration_seconds": 180,
  "answers": [...]
}
↓
提交成功即发放积分 points_awarded
```

**C. 查看记录/统计**
```bash
GET /fills/me                        # 我的填写记录
GET /points/logs                     # 积分流水
GET /surveys/{id}/analytics/summary  # 发布者看统计
```

### 3️⃣ 查看结果
```bash
GET /task-hall/overview
GET /task-hall/tasks
```

---

## 📊 接口速查表

### 认证（5）
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /auth/send-register-code | 发送注册验证码 |
| POST | /auth/register | 注册 |
| POST | /auth/login | 登录 |
| POST | /auth/send-reset-code | 发送重置验证码 |
| POST | /auth/reset-password | 重置密码 |

### 用户（2）
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /users/me | 获取信息 |
| PATCH | /users/me | 更新信息 |

### 问卷管理（核心）
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /surveys | 我的问卷列表 |
| GET | /surveys/summary | 我的问卷统计 |
| GET | /surveys/{id} | 问卷详情 |
| DELETE | /surveys/{id} | 删除问卷 |
| POST | /surveys/{id}/publish | 发布问卷 |
| POST | /surveys/{id}/pause | 暂停 |
| POST | /surveys/{id}/resume | 恢复 |
| POST | /surveys/{id}/cancel | 取消发布并退款 |

### 草稿与填写
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /surveys/drafts | 创建草稿 |
| GET | /surveys/drafts/{id} | 获取草稿 |
| PATCH | /surveys/drafts/{id} | 保存草稿 |
| POST | /surveys/drafts/{id}/ai-generate | AI生成题目 |
| GET | /surveys/{id}/fill | 获取填写问卷 |
| POST | /surveys/{id}/fills | 提交 |
| GET | /fills/me | 我的填答 |

### 任务大厅与其他
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /task-hall/overview | 任务大厅概览 |
| GET | /task-hall/tasks | 任务列表 |
| POST | /task-hall/batch/refresh | 换一批 |
| GET | /task-hall/guest-tasks | 访客任务 |
| GET | /points/logs | 积分流水 |
| GET | /points/summary | 积分汇总 |
| POST | /points/update | 积分更新（管理用途） |
| POST | /reports | 举报 |

---

## 💡 常见错误及解决

| 错误 | 原因 | 解决 |
|------|------|------|
| 401 | Token 过期/不存在 | 重新登录 |
| 403 | 无权操作 | 检查是否为资源所有者 |
| 404 | 资源不存在 | 检查 ID 是否正确 |
| 422 | 参数错误 | 参考文档检查请求体 |

## 🔑 关键参数

### 分页参数（通用）
```json
{
  "page": 1,
  "page_size": 20
}
```

### 任务大厅筛选参数
```
GET /task-hall/tasks?status=active&min_reward=10&max_minutes=30&page=1&page_size=20
```

### 积分筛选参数
```
GET /points/logs?type=earn  // earn 或 spend
```

## 📍 资源 ID 前缀

- 用户：`u_...`
- 问卷：`s_...`
- 填写：`f_...`
- 积分：`p_...`
- 举报：`r_...`

## 🏆 重要规则

### 积分
- 初始：20 分
- 发布问卷：按预算扣费（-budget_points）
- 提交答卷：即时加分（+reward_points）

### 信用分
- 初始：80 分
- 荣誉身份：credit_score >= 85

### 防作弊
- 填答时间最少：10 秒
- 同一用户对同一问卷：只能提交一次
- 不能填自己的问卷

## 📝 请求示例

### 用 Fetch
```javascript
const response = await fetch('/api/v1/surveys/s_1/fills', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    duration_seconds: 180,
    answers: [
      { question_id: 'q_1', value: 'A' }
    ]
  })
});
const data = await response.json();
```

### 用 curl
```bash
curl -X POST http://127.0.0.1:8000/api/v1/surveys/s_1/fills \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"duration_seconds":180,"answers":[{"question_id":"q_1","value":"A"}]}'
```

## 📚 详细文档位置

| 功能 | 文档 |
|------|------|
| 注册/登录细节 | API-认证.md |
| 用户信息 | API-用户和问卷基础.md |
| 问卷发布 | API-问卷管理.md |
| 草稿制作 | API-问卷制作.md |
| 填答与记录 | API-问卷填写.md / API-答卷提交和审核.md |
| 积分明细 | API-积分和举报.md |
| 完整说明 | API-总览.md |

---

## ✅ 检查清单

部署前，确认以下事项：

- [ ] 后端运行在 http://127.0.0.1:8000
- [ ] 前端能访问 /api/v1 端点
- [ ] 已读过相关的详细文档
- [ ] 测试过至少一个端点
- [ ] 前端已添加 Authorization 头
- [ ] 测试过 401 错误处理

---

**打印此卡贴在显示器上！**

