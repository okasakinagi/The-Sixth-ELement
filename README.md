# 第六元素 · SurveyFiller

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
| **答卷审核** | 兼容审核入口仍保留，但主流程是提交后立即发放积分 |
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
| 答卷审核 | `POST /fills/{id}/review`  `GET /fills/me` | 兼容审核入口，查看我的填写 |
| 积分 | `GET /points/logs`  `GET /points/summary` | 流水明细与积分概览 |
| 举报 | `POST /reports` | 举报问卷或用户 |
| 内部推荐 | `POST /internal/vector/generate`  `POST /internal/similarity/compute` | 向量生成与相似度计算（内部调用） |

完整文档见 [doc/api/API-总览.md](doc/api/API-总览.md)。

---

## 数据模型

核心表结构（详见 [doc/数据模型字典.md](doc/数据模型字典.md)）：

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

项目提供完整的容器化部署方案，核心由 4 个服务组成：

```
db        MySQL 8.0（数据持久化）
web       Django + Gunicorn（端口 8000）
frontend  Nginx + Vue 静态文件（端口 80，反代 /api 到 web）
redis     Redis 7（缓存与推荐相关能力）
```

### 服务器上的环境变量

项目没有单独提供 `deploy/.env.example`，线上部署时需要在服务器上手动创建 `deploy/.env`。这个文件会同时被 Docker Compose 和部署脚本读取。

```env
DJANGO_SECRET_KEY=replace-with-a-long-random-string
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=your-domain.com,127.0.0.1,localhost
DJANGO_DB_NAME=sixth_element
DJANGO_DB_USER=sixth_element
DJANGO_DB_PASSWORD=replace-with-db-password
DJANGO_DB_HOST=db
DJANGO_DB_PORT=3306
DB_ROOT_PASSWORD=replace-with-root-password
DB_NAME=sixth_element
DB_USER=sixth_element
DB_PASSWORD=replace-with-db-password
REDIS_URL=redis://redis:6379/0
RECOMMENDATION_MODE=personalized
EMAIL_HOST=smtp.exmail.qq.com
EMAIL_PORT=465
EMAIL_USE_SSL=true
EMAIL_USE_TLS=false
EMAIL_PRIMARY_USER=your-email@example.com
EMAIL_PRIMARY_PASSWORD=your-email-password-or-app-password
EMAIL_INTERNAL_USER=your-email@example.com
EMAIL_INTERNAL_PASSWORD=your-email-password-or-app-password
EMAIL_INTERNAL_NAME=第六元素部署节点
EMAIL_DEPLOY_NOTIFY_TO=ops@example.com

# AI 功能：环境变量优先，deploy/ai_config.json 作为兜底
GENERATION_API_KEY=your-siliconflow-api-key
GENERATION_BASE_URL=https://api.siliconflow.cn/v1/chat/completions
GENERATION_MODEL=Qwen/Qwen2.5-7B-Instruct
DIFFICULTIES_API_KEY=your-siliconflow-api-key
DIFFICULTIES_BASE_URL=https://api.siliconflow.cn/v1/chat/completions
DIFFICULTIES_MODEL=Pro/deepseek-ai/DeepSeek-V3.2
EMBEDDING_API_KEY=your-siliconflow-api-key
EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1/embeddings
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-4B
```

说明：

- `DJANGO_DB_*` 是 Django 运行时读取的数据库配置。
- `DB_*` 是部署脚本和 MySQL 容器初始化时读取的数据库配置。
- `EMAIL_*` 用于验证码邮件和部署通知邮件。
- `REDIS_URL` 用于缓存和推荐相关功能。
- `RECOMMENDATION_MODE` 默认建议保持 `personalized`。

AI 功能可以直接写在 `deploy/.env` 里，也可以写在 `deploy/ai_config.json` 里。代码读取顺序是：先看环境变量，没配全再回退到 `deploy/ai_config.json`。部署时更推荐把这几组 AI 变量写进 `deploy/.env`，`deploy/ai_config.json` 作为兜底和示例配置即可。参考 [deploy/ai_config.example.json](deploy/ai_config.example.json)。

### 部署命令

```bash
cd deploy

# 启动或更新容器
docker compose -f docker-compose.yml up -d --build

# 初始化数据库迁移
docker compose -f docker-compose.yml exec web python Main.py migrate

# 如需收集静态文件
docker compose -f docker-compose.yml exec web python Main.py collectstatic --noinput
```

### 自动更新部署

`deploy/update_deploy.sh` 是正式的自动/手动部署脚本，执行顺序大致如下：

1. 检查 `deploy/.env` 是否存在。
2. 备份当前 `deploy/.env` 和数据库。
3. 拉取远端 `main` 分支最新代码。
4. 构建 `backend:latest` 和 `frontend:latest` 镜像。
5. 启动或替换容器。
6. 执行迁移和静态文件收集。
7. 成功后记录最新 commit，失败时发送邮件并暂停自动部署。

> 说明：脚本里现在的 `PROJECT_DIR`、`STATE_DIR`、日志路径等是按当前服务器路径写死的参考值。实际部署时如果你的项目路径不同，需要先改脚本顶部的路径常量再使用；如果你已经把脚本改成了相对路径版本，那就按你的实际环境直接执行即可。

服务器上手动触发部署时，可以直接执行：

```bash
bash deploy/update_deploy.sh
```

### 自动巡检与恢复

- `deploy/auto_watch.sh`：轮询远端 `main` 分支，如果发现新 commit 就调用 `update_deploy.sh`。
- `deploy/unpause_auto.sh`：运维排障工具，可导出容器日志、查看部署日志、或在人工修复后解除暂停状态。
- `deploy/ops-cheatsheet.sh`：部署维护速查脚本，适合人工排障时参考常用命令。

Linux 上建议用 `cron` 触发自动巡检，例如每分钟执行一次：

```cron
* * * * * /bin/bash /home/six_element/home/six_element_app/The-Sixth-ELement/deploy/auto_watch.sh >> /home/six_element/deploy_state/cron.log 2>&1
```

如果你的仓库路径或状态目录不同，把上面的绝对路径改成你服务器上的实际路径即可。`auto_watch.sh` 本身没有绑定到某台机器，只要更新脚本里的 `PROJECT_DIR`、`STATE_DIR` 等路径常量，就可以在别的 Linux 服务器上复用。

部署日志位置：

- `~/deploy_state/update_deploy.log`
- `~/deploy_state/auto_watch.log`
- `~/deploy_state/cron.log`（如果定时任务有重定向）

AI 功能同样支持写入 `deploy/.env`，当前代码会优先读取环境变量；如果环境变量缺失，再读取 `deploy/ai_config.json`。

---

## 典型用户流程

1. 注册账号（获赠 20 初始积分）
2. 在**任务大厅**浏览推荐问卷并填写
3. 填写完成后立即获得积分，队伍场景下可自动记到队长账户
4. 积分充足后，在**问卷制作**中创建并发布自己的问卷（支持 AI 辅助生成）
5. 在**问卷管理**中查看列表、状态和数据分析，审核接口仅作兼容保留

---

## 贡献方式

欢迎提交 Issue 或 Pull Request。请在 PR 描述中说明改动场景与预期效果。

## 版权

本项目遵循 [LICENSE](LICENSE) 中的协议。

