﻿# 第六元素 · SurveyFiller

> 面向校园与社群的问卷互填平台——发布问卷、完成填写、赚取积分，形成公平可持续的互助闭环。

**线上地址：[http://www.surveyfiller.com/](http://www.surveyfiller.com/)**

---

## 项目简介

**第六元素**是一个问卷互填交换平台。用户通过完成他人问卷赚取积分，再用积分发布自己的问卷来吸引回收。平台内置 AI 辅助题目生成、基于向量嵌入的个性化推荐、完整的积分经济体系与数据分析看板，致力于解决"发了没人填"的普遍困境。

---

## 主要功能

| 模块 | 功能描述 |
|------|----------|
| **账户体系** | 注册/登录（Bearer Token）、密码重置（验证码）、用户画像与标签 |
| **问卷制作** | 富文本问卷编辑器，支持单选、多选、填空等题型，跳转逻辑配置，版本管理 |
| **AI 辅助** | 输入 Prompt，由大语言模型（Qwen 2.5）自动生成问卷题目 |
| **任务大厅** | 个性化推荐列表（余弦相似度算法），访客可浏览，登录后可参与 |
| **问卷填写** | 在线作答，提交答案，支持耗时记录与反作弊字段采集 |
| **答卷审核** | 问卷发布方可审核填写记录，审核通过后自动发放积分 |
| **积分体系** | 发布扣分、填写得分，积分流水全量记录，信用分独立管理 |
| **数据分析** | 问卷统计概览、题目维度分析、原始数据导出 |
| **举报系统** | 对问卷或用户发起举报 |
| **个人中心** | 积分明细、问卷管理、历史填写记录、标签画像编辑 |

---

## 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | Vue 3  Vite 7  Vue Router 4 |
| 后端 | Django 6.0  Gunicorn |
| 数据库 | MySQL 8.0 |
| AI 服务 | SiliconFlow API（Qwen2.5-7B 问卷生成  Qwen3-Embedding-4B 向量推荐） |
| 部署 | Docker  Docker Compose  Nginx |

---

## 项目结构

```
The-Sixth-ELement/
 core/                    # 核心 Django 应用（模型、主路由、通用视图）
    models.py            # 全部数据模型（15+ 张表）
    views.py             # 认证、用户、积分等基础 API
    urls.py              # 路由注册
    controllers/         # 相似度计算控制器
    services/            # 相似度业务服务
    migrations/          # 数据库迁移文件
 task_hall/               # 任务大厅（推荐列表）子应用
 survey_management/       # 问卷管理（CRUD、发布、分析）子应用
 surveyfill/              # 问卷填写与审核子应用
 points_record/           # 积分记录子应用
 personal_homepage/       # 个人主页与用户画像子应用
 user_profile_extractor/  # 用户画像 AI 提取子应用
 frontend/sixth_element/  # Vue 3 前端项目
    src/views/           # 16 个页面组件
    src/components/      # 公共组件（导航栏、侧边栏等）
    src/router/          # SPA 路由配置
 module/survey_app/       # Django 配置（settings、wsgi、urls）
 docker/                  # Dockerfile（后端 + 前端）
 deploy/                  # Docker Compose 与部署脚本
 doc/                     # API 文档与数据库设计文档
 Main.py                  # 入口（注入 module/ 路径的 manage.py 封装）
```

---

## API 概览

Base URL：`/api/v1/`

| 分组 | 示例端点 | 说明 |
|------|----------|------|
| 认证 | `POST /auth/register`  `POST /auth/login` | 注册登录，返回 Bearer Token |
| 认证 | `POST /auth/send-reset-code`  `POST /auth/reset-password` | 验证码密码重置 |
| 用户 | `GET /users/me`  `PATCH /users/me` | 当前用户信息与标签更新 |
| 问卷管理 | `GET/POST /surveys`  `POST /surveys/{id}/publish` | 列表、创建、发布/暂停/关闭 |
| 草稿 | `POST /surveys/drafts`  `POST /surveys/drafts/{id}/ai-generate` | 草稿编辑与 AI 生成题目 |
| 数据分析 | `GET /surveys/{id}/analytics/summary`  `GET /surveys/{id}/analytics/export` | 统计与数据导出 |
| 任务大厅 | `GET /task-hall/tasks`  `GET /task-hall/guest-tasks` | 推荐任务列表（含访客模式） |
| 问卷填写 | `GET /surveys/{id}/fill`  `POST /surveys/{id}/fills` | 获取题目，提交答案 |
| 答卷审核 | `POST /fills/{id}/review`  `GET /fills/me` | 审核答卷，查看我的填写 |
| 积分 | `GET /points/logs`  `GET /points/summary` | 流水明细与积分概览 |
| 举报 | `POST /reports` | 举报问卷或用户 |
| 内部推荐 | `POST /internal/vector/generate`  `GET /internal/recommend` | 向量生成与相似度推荐（内部调用） |

完整文档见 [doc/api/](doc/api/)。

---

## 数据模型

核心表结构（详见 [doc/数据库表.md](doc/数据库表.md)）：

- **AppUser**  用户账号（积分、信用分、活跃度）
- **AuthToken**  Bearer 令牌（1 小时有效期）
- **Survey**  问卷任务（draft  published  closed 状态机）
- **Questionnaire / Question / QuestionOption**  问卷内容与版本管理
- **Response / Answer**  答卷与单题答案
- **PointsLog**  积分流水（全量审计）
- **Tag / SurveyTag / UserTag / UserTagWeight**  标签画像体系（14 种标签类型）
- **IDVector / SurveyUserSimilarity**  向量推荐引擎
- **Report**  举报记录
- **Notification / AuditLog**  通知与审计日志

---

## 本地开发

### 前提条件

- Python 3.12+
- Node.js 20+
- MySQL 8.0（数据库名 `sixth_element`，用户 `sixth_element`，密码 `123456`）

### 启动后端

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python Main.py migrate
python Main.py runserver
```

后端运行于 `http://127.0.0.1:8000`，API 前缀 `/api/v1/`。

### 启动前端

```bash
cd frontend/sixth_element
npm install
npm run dev
```

Vite 开发服务器运行于 `http://localhost:5173`，`/api` 请求自动代理到 Django。

---

## Docker 部署

项目提供完整的容器化部署方案（3 个服务）：

```
db        MySQL 8.0（数据持久化）
web       Django + Gunicorn（3 workers，端口 8000）
frontend  Nginx + Vue 静态文件（端口 80，反代 /api 到 web）
```

```bash
cd deploy

# 复制并填写环境变量
cp .env.example .env   # 设置 DJANGO_SECRET_KEY、DB 密码等

# 构建并启动
docker compose up -d --build

# 初始化数据库
docker compose exec web python Main.py migrate
```

AI 功能需在 `deploy/ai_config.json` 中填写 SiliconFlow API Key（参考 `deploy/ai_config.example.json`）。

---

## 典型用户流程

1. 注册账号（获赠 20 初始积分）
2. 在**任务大厅**浏览推荐问卷并填写
3. 填写完成  等待审核  通过后获得积分
4. 积分充足后，在**问卷制作**中创建并发布自己的问卷（支持 AI 辅助生成）
5. 在**问卷管理**中审核他人提交、查看数据分析

---

## 贡献方式

欢迎提交 Issue 或 Pull Request。请在 PR 描述中说明改动场景与预期效果。

## 版权

本项目遵循 [LICENSE](LICENSE) 中的协议。

