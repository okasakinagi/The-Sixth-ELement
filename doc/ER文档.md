# 数据库 ERD 说明文档（站内问卷填写版）

## 1. 总览

本系统面向“问卷互填平台”，核心闭环为：

1. 发布者创建 **SURVEY（任务）**
2. 在站内配置 **QUESTIONNAIRE（问卷版本）→ QUESTION（题目）→ OPTION（选项）**
3. 填写者开始答题生成 **RESPONSE（答卷）**，逐题写入 **ANSWER（答案）**
4. 提交后进入（可选）风控/审核，最终发放积分（**POINTS_LOG**）并通知（**NOTIFICATION**）
5. 异常行为由用户发起 **REPORT（举报）**，管理员处理留痕于 **AUDIT_LOG**

---

## 2. 实体与字段说明

### 2.1 USER（用户表）

**用途**：存储平台用户基础信息、积分快照与状态。

**关键字段**

* `id`：主键
* `email / nickname`：用户标识信息
* `points`：积分快照（用于快速展示）
* `credit_score`：信用分（用于风控、资格筛选）
* `status`：用户状态（normal/banned/limited 等）
* `created_at / updated_at`

**主要关系**

* 1:N 发布问卷 → `SURVEY.owner_id`
* 1:N 提交答卷 → `RESPONSE.user_id`
* 1:N 积分流水 → `POINTS_LOG.user_id`
* 1:N 举报发起人 → `REPORT.reporter_id`
* 1:N 通知 → `NOTIFICATION.user_id`
* N:M 角色 → `USER_ROLE`
* N:M 用户画像标签 → `USER_TAG`

---

### 2.2 ROLE / USER_ROLE（角色与用户角色）

**用途**：权限系统（多对多）。

**ROLE 字段**

* `id, name, description`

**USER_ROLE 字段**

* `user_id`（FK → USER）
* `role_id`（FK → ROLE）
* `created_at`

**典型权限用例**

* 审核举报、下架问卷、封禁用户、人工调整积分等后台操作。

---

### 2.3 SURVEY（任务/问卷发布单）

**用途**：任务大厅展示与交易规则载体（奖励、截止、状态等）。

**关键字段**

* `owner_id`：发布者（FK → USER）
* `title / description`
* `estimated_minutes`：预计耗时
* `reward_points`：填写通过后奖励
* `publish_cost_points`：发布成本（扣分）
* `deadline`：截止时间
* `status`：draft/published/closed/expired/rejected…
* `active_questionnaire_id`：当前生效问卷版本（FK → QUESTIONNAIRE，可选但推荐）
* `created_at / updated_at`

**主要关系**

* 1:N 版本 → QUESTIONNAIRE（`QUESTIONNAIRE.survey_id`）
* 1:N 答卷 → RESPONSE（`RESPONSE.survey_id`）
* N:M 任务标签 → SURVEY_TAG

---

### 2.4 QUESTIONNAIRE（问卷版本）

**用途**：承载问卷结构的版本化管理，保证“历史答卷永远对应当时版本”。

**关键字段**

* `survey_id`：所属任务（FK → SURVEY）
* `version`：版本号（1,2,3…）
* `status`：draft/published/archived
* `title`
* `created_at / updated_at`

**主要关系**

* 1:N 题目 → QUESTION（`QUESTION.questionnaire_id`）
* 1:N 答卷引用版本 → RESPONSE（`RESPONSE.questionnaire_id`）
* SURVEY.active_questionnaire_id 指向当前发布版本

---

### 2.5 QUESTION（题目）

**用途**：每一道题的题干、题型、排序、必填、逻辑与校验。

**关键字段**

* `questionnaire_id`：所属版本（FK）
* `order_no`：题目序号（决定展示顺序）
* `type`：题型（single/multi/text/number/scale/matrix/date…）
* `title / description`
* `is_required`
* `config_json`：题型配置（如量表范围、矩阵行列、输入限制）
* `logic_json`：跳题/显示条件（可选）
* `created_at / updated_at`

**主要关系**

* 1:N 选项 → QUESTION_OPTION（单选/多选等）
* 1:N 被作答 → ANSWER（`ANSWER.question_id`）

---

### 2.6 QUESTION_OPTION（题目选项）

**用途**：存题目选项（单选/多选/下拉/矩阵列等）。

**关键字段**

* `question_id`（FK → QUESTION）
* `order_no`
* `label`：展示文本
* `value`：存储值（建议稳定，不随文案变化）
* `is_other`：是否“其他”选项
* `extra_config_json`：分值/是否需要补充输入等
* `created_at`

---

### 2.7 RESPONSE（答卷/一次提交）

**用途**：用户对某份问卷的一次填写记录，是答案的容器与结算对象。

**关键字段**

* `survey_id`（FK → SURVEY）
* `questionnaire_id`（FK → QUESTIONNAIRE，固定当时版本）
* `user_id`（FK → USER）
* `status`：in_progress/submitted/approved/rejected
* `started_at / submitted_at`
* `duration_seconds`：填写耗时
* `risk_flag`：风控标记（可选）
* `evidence_url / device_fingerprint / ip_hash`：风控/证据字段（可选）
* `created_at / updated_at`

**主要关系**

* 1:N 逐题答案 → ANSWER（`ANSWER.response_id`）

**业务联动**

* 提交后（submitted）→ 可进入审核 → approved 后触发积分与通知。

---

### 2.8 ANSWER（答案）

**用途**：存每道题的答案，支持简单/复杂题型统一落库。

**关键字段**

* `response_id`（FK → RESPONSE）
* `question_id`（FK → QUESTION）
* `value_text`：文本/数字/日期等简单答案
* `value_json`：多选/矩阵/复杂结构答案
* `created_at / updated_at`

**建议约束**

* `UNIQUE(response_id, question_id)`：同一答卷同一题只允许一条答案（便于 upsert 保存草稿）

---

### 2.9 POINTS_LOG（积分流水）

**用途**：积分账本，所有加减分必须可审计、可追溯。

**关键字段**

* `user_id`（FK → USER）
* `points_type`：积分类型（reward/publish_cost/admin_adjust…）
* `delta`：增减值（正负）
* `reason`：原因说明
* `ref_type / ref_id`：来源对象（如 SURVEY / RESPONSE / REPORT / ADMIN）
* `created_at`

**业务原则**

* `USER.points` 是快照；对账/纠纷以 `POINTS_LOG` 为准。

---

### 2.10 REPORT（举报单）

**用途**：用户上报异常、管理员处理闭环。

**关键字段**

* `reporter_id`（FK → USER）
* `target_type + target_id`：举报对象（SURVEY/RESPONSE/USER…）
* `reason / detail`
* `status`：open/resolved/rejected
* `handled_by`（FK → USER，管理员/审核员）
* `created_at / handled_at`

**业务联动**

* 处理举报时通常会：

  * 修改目标对象 status（下架、驳回答卷、封禁用户等）
  * 写 AUDIT_LOG 留痕
  * 必要时写 POINTS_LOG（扣分/补偿/奖励举报人）

---

### 2.11 AUDIT_LOG（审计日志）

**用途**：管理员操作留痕（可追溯、可回滚、可审计）。

**关键字段**

* `target_type + target_id`：被操作对象
* `action`：操作类型（ban_user/unpublish_survey/approve_response/adjust_points…）
* `operator_id`（FK → USER）
* `note`：备注（原因/证据）
* `created_at`

---

### 2.12 NOTIFICATION（站内通知）

**用途**：把“状态变化结果”推送给用户。

**关键字段**

* `user_id`（FK → USER）
* `type`：通知类型（survey_published/response_approved/report_resolved…）
* `title / content`
* `status`：unread/read（或用 read_at 表示）
* `created_at / read_at`

---

### 2.13 TAG / SURVEY_TAG / USER_TAG（标签体系）

**用途**：筛选与推荐的基础设施。

**TAG 字段**

* `name`：标签名（如 心理学/本科生/AI）
* `type`：标签类别（domain/identity/topic…）
* `created_at`

**SURVEY_TAG**

* `survey_id`（FK → SURVEY）
* `tag_id`（FK → TAG）
* `created_at`

**USER_TAG**

* `user_id`（FK → USER）
* `tag_id`（FK → TAG）
* `created_at`

**业务联动**

* 任务大厅筛选：按 SURVEY_TAG
* 推荐：`USER_TAG ∩ SURVEY_TAG`
* 定向通知：发布新问卷 → 通知匹配用户标签的人群

---

## 3. 关键关系与联动（按业务流程）

### 3.1 发布问卷（创建任务 + 发布版本）

1. 创建 SURVEY（draft）
2. 创建 QUESTIONNAIRE（draft version=1）
3. 创建 QUESTION / OPTION
4. 发布：

   * QUESTIONNAIRE.status=published
   * SURVEY.status=published
   * SURVEY.active_questionnaire_id=该版本
   * 扣发布成本：POINTS_LOG(delta = -publish_cost_points, ref= SURVEY)
   * 通知（可选）：匹配标签用户 NOTIFICATION

---

### 3.2 站内填写（开始 → 保存 → 提交）

1. 用户点击开始：

   * 创建 RESPONSE(status=in_progress, started_at)
2. 答题过程中保存：

   * 对每题 upsert ANSWER（唯一键 response_id+question_id）
3. 用户提交：

   * 校验必填题、答案合法性
   * RESPONSE.status=submitted，记录 submitted_at、duration_seconds

---

### 3.3 审核与积分结算（可选）

* 自动/人工审核：

  * 通过：RESPONSE.status=approved

    * 发积分：POINTS_LOG(delta=+reward_points, ref=RESPONSE)
    * 更新 USER.points
    * 发送 NOTIFICATION
  * 驳回：RESPONSE.status=rejected + 通知

---

### 3.4 举报处理闭环

1. 用户创建 REPORT（target 指向 SURVEY/RESPONSE/USER）
2. 管理员处理：

   * 改目标对象状态（下架/封禁/驳回答卷等）
   * 写 AUDIT_LOG
   * 必要时积分处罚/补偿（POINTS_LOG）
   * 通知相关方（NOTIFICATION）

---

## 4. 推荐的数据库约束与索引（强烈建议）

* `ANSWER`：`UNIQUE(response_id, question_id)`
* `QUESTION`：建议 `UNIQUE(questionnaire_id, order_no)`（保证顺序稳定）
* `QUESTION_OPTION`：建议 `UNIQUE(question_id, order_no)`
* `RESPONSE`：

  * 若业务要求“一人一份任务只能提交一次”：

    * `UNIQUE(user_id, survey_id)`（或仅对 submitted/approved 生效的逻辑唯一）
* 常用索引：

  * `RESPONSE(survey_id, status)`
  * `RESPONSE(user_id, created_at)`
  * `POINTS_LOG(user_id, created_at)`
  * `SURVEY(status, deadline)`
  * `SURVEY_TAG(tag_id)`, `USER_TAG(tag_id)`

---

