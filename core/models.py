from django.db import models


class AppUser(models.Model):
    nickname = models.CharField(max_length=64)
    email = models.EmailField(unique=True)
    credit_score = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    activity_points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    title = models.CharField(max_length=32, default="新手探索者")
    status = models.CharField(max_length=32, default="normal")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_active_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nickname


class AuthCredential(models.Model):
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE)
    password_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AuthToken(models.Model):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=128, unique=True, db_index=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class PasswordResetCode(models.Model):
    """邮件验证码（服务于注册验证和密码重置两种场景）"""

    PURPOSE_REGISTER = "register"
    PURPOSE_RESET = "reset"
    PURPOSE_CHOICES = [
        ("register", "注册验证"),
        ("reset", "密码重置"),
    ]

    email = models.EmailField(db_index=True)
    # 存储 SHA-256(code)，不明文保存原始6位数字；default='' 仅用于迁移过渡
    code_hash = models.CharField(max_length=64, default="")
    purpose = models.CharField(
        max_length=20, choices=PURPOSE_CHOICES, default=PURPOSE_RESET
    )
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    # 错误尝试次数，超过阈值（5次）自动失效
    attempt_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["email", "purpose", "is_used", "expires_at"],
                name="email_code_lookup_idx",
            ),
        ]


class Role(models.Model):
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name


class UserRole(models.Model):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "role"], name="unique_user_role")
        ]


class Survey(models.Model):
    owner = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    estimated_minutes = models.IntegerField(blank=True, null=True)
    difficulty = models.IntegerField(default=3)
    reward_points = models.IntegerField(default=0)
    publish_cost_points = models.IntegerField(default=0)
    deadline = models.DateTimeField(blank=True, null=True)
    target = models.IntegerField(default=1)
    completed = models.IntegerField(default=0)
    status = models.CharField(max_length=32, default="draft")
    ai_generated = models.BooleanField(default=False)
    active_questionnaire = models.ForeignKey(
        "Questionnaire",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="active_for_surveys",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        indexes = [
            models.Index(
                fields=["status", "deadline"], name="survey_status_deadline_idx"
            ),
        ]


class Questionnaire(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    version = models.IntegerField(default=1)
    status = models.CharField(max_length=32, default="draft")
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Question(models.Model):
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    order_no = models.IntegerField(default=1)
    type = models.CharField(max_length=32)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    is_required = models.BooleanField(default=True)
    config_json = models.JSONField(blank=True, null=True)
    logic_json = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["questionnaire", "order_no"],
                name="unique_questionnaire_order",
            )
        ]


class QuestionOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order_no = models.IntegerField(default=1)
    label = models.CharField(max_length=200)
    value = models.CharField(max_length=200)
    is_other = models.BooleanField(default=False)
    extra_config_json = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["question", "order_no"],
                name="unique_question_option_order",
            )
        ]


class Response(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    status = models.CharField(max_length=32, default="in_progress")
    started_at = models.DateTimeField(blank=True, null=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    duration_seconds = models.IntegerField(blank=True, null=True)
    risk_flag = models.BooleanField(default=False)
    evidence_url = models.CharField(max_length=500, blank=True, null=True)
    device_fingerprint = models.CharField(max_length=200, blank=True, null=True)
    ip_hash = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "survey"],
                name="unique_response_user_survey",
            )
        ]
        indexes = [
            models.Index(
                fields=["survey", "status"], name="response_survey_status_idx"
            ),
            models.Index(
                fields=["user", "created_at"], name="response_user_created_idx"
            ),
        ]


class Answer(models.Model):
    response = models.ForeignKey(Response, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    value_text = models.TextField(blank=True, null=True)
    value_json = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["response", "question"], name="unique_answer_response_question"
            )
        ]


class PointsLog(models.Model):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    points_type = models.CharField(max_length=32)
    delta = models.IntegerField()
    reason = models.CharField(max_length=200)
    ref_type = models.CharField(max_length=32, blank=True, null=True)
    ref_id = models.BigIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["user", "created_at"], name="pointslog_user_created_idx"
            ),
        ]


class Report(models.Model):
    reporter = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    target_type = models.CharField(max_length=32)
    target_id = models.BigIntegerField()
    reason = models.CharField(max_length=200)
    detail = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=32, default="open")
    handled_by = models.ForeignKey(
        AppUser,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="handled_reports",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    handled_at = models.DateTimeField(blank=True, null=True)


class AuditLog(models.Model):
    target_type = models.CharField(max_length=32)
    target_id = models.BigIntegerField()
    action = models.CharField(max_length=64)
    operator = models.ForeignKey(AppUser, on_delete=models.CASCADE, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Message(models.Model):
    """站内信（原Notification扩展）"""

    # 原有字段 - 保留不动
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)  # 接收者
    type = models.CharField(max_length=32)  # 历史兼容字段
    title = models.CharField(max_length=200)
    content = models.TextField()
    status = models.CharField(max_length=32, default="unread", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    read_at = models.DateTimeField(blank=True, null=True)

    # 新增字段 - 支持组队邀请和积分赠送
    sender = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name="sent_messages",
        blank=True,
        null=True,
    )  # 发送者（系统消息时为null）

    message_type = models.CharField(
        max_length=32,
        default="system",
        choices=[
            ("system", "系统消息"),
            ("team_invite", "队伍邀请"),
            ("points_gift", "积分赠送"),
        ],
    )  # 消息具体类型

    ref_type = models.CharField(
        max_length=32, blank=True, db_index=True
    )  # 'team', 'user' 等
    ref_id = models.BigIntegerField(blank=True, null=True, db_index=True)  # 关联对象ID

    points_amount = models.IntegerField(default=0)  # 赠送的积分数
    is_accepted = models.BooleanField(default=False)  # 邀请或赠送是否被接受

    class Meta:
        indexes = [
            models.Index(
                fields=["user", "status", "-created_at"],
                name="msg_user_status_created_idx",
            ),
            models.Index(fields=["user", "-created_at"], name="msg_user_created_idx"),
            models.Index(fields=["ref_type", "ref_id"], name="msg_ref_type_id_idx"),
        ]


class Team(models.Model):
    """用户组队信息"""

    owner = models.ForeignKey(
        AppUser, on_delete=models.CASCADE, related_name="owned_teams"
    )
    title = models.CharField(max_length=200, blank=True)  # 队伍名（可选）
    description = models.TextField(blank=True)  # 队伍描述
    max_members = models.IntegerField(default=5)  # 最大成员数
    status = models.CharField(
        max_length=32,
        default="active",
        choices=[
            ("active", "活跃"),
            ("closed", "已关闭"),
        ],
    )

    # 审计字段
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner", "status"], name="team_owner_status_idx"),
            models.Index(
                fields=["status", "-created_at"], name="team_status_created_idx"
            ),
        ]

    def __str__(self):
        return f"Team({self.id}) - {self.owner.nickname}"


class TeamMember(models.Model):
    """队伍成员关联"""

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(
        AppUser, on_delete=models.CASCADE, related_name="team_memberships"
    )

    role = models.CharField(
        max_length=32,
        default="member",
        choices=[
            ("member", "普通成员"),
            ("admin", "管理员"),
        ],
    )

    status = models.CharField(
        max_length=32,
        default="joined",
        choices=[
            ("invited", "邀请中"),
            ("joined", "已加入"),
            ("left", "已离开"),
            ("kicked", "被移除"),
        ],
    )

    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["team", "user"], name="unique_team_member"),
        ]
        indexes = [
            models.Index(fields=["team", "status"], name="tm_team_status_idx"),
            models.Index(fields=["user", "status"], name="tm_user_status_idx"),
            models.Index(fields=["team", "role"], name="tm_team_role_idx"),
        ]

    def __str__(self):
        return (
            f"{self.user.nickname}({self.get_role_display()}) in Team({self.team.id})"
        )


class TeamInvitation(models.Model):
    """组队邀请追踪表（管理邀请冷却和重试次数）"""

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="invitations")
    inviter = models.ForeignKey(
        AppUser, on_delete=models.CASCADE, related_name="sent_invitations"
    )
    invitee = models.ForeignKey(
        AppUser, on_delete=models.CASCADE, related_name="received_invitations"
    )

    # 邀请状态
    status = models.CharField(
        max_length=32,
        default="pending",
        choices=[
            ("pending", "待处理"),
            ("accepted", "已接受"),
            ("rejected", "已拒绝"),
            ("expired", "已过期"),
        ],
    )

    # 冷却时间追踪
    attempt_count = models.IntegerField(
        default=1
    )  # 邀请次数（1 or 2不受限，3+需10min冷却）
    last_invited_at = models.DateTimeField(auto_now_add=True)  # 最后一次邀请时间

    # 决议记录
    accepted_at = models.DateTimeField(
        blank=True, null=True
    )  # 接受时间（接受后重置count）
    rejected_at = models.DateTimeField(blank=True, null=True)

    # 审计字段
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # 同一team对一个invitee最多一条pending邀请
        constraints = [
            models.UniqueConstraint(
                fields=["team", "invitee"],
                condition=models.Q(status="pending"),
                name="unique_team_invitee_pending",
            ),
        ]
        indexes = [
            models.Index(fields=["team", "status"], name="tinv_team_status_idx"),
            models.Index(fields=["invitee", "status"], name="tinv_invitee_status_idx"),
            models.Index(
                fields=["inviter", "invitee"], name="tinv_inviter_invitee_idx"
            ),
        ]

    def __str__(self):
        return f"Invite {self.inviter.nickname} -> {self.invitee.nickname} to Team({self.team.id})"


class Tag(models.Model):
    TYPE_SURVEY = "survey_type"
    TYPE_INTEREST = "interest"
    TYPE_SCHOOL = "school"
    TYPE_GENDER = "gender"
    TYPE_AGE = "age"
    TYPE_GRADE = "grade"
    TYPE_COLLEGE = "college"
    TYPE_MAJOR = "major"
    TYPE_MBTI = "mbti"
    TYPE_ORGANIZATION = "organization"
    TYPE_CONSUMPTION = "consumption"
    TYPE_CAREER = "career"
    TYPE_SKILL = "skill"
    TYPE_STATUS = "status"
    TYPE_CHOICES = (
        (TYPE_SURVEY, "Survey Type"),
        (TYPE_INTEREST, "Interest"),
        (TYPE_SCHOOL, "School"),
        (TYPE_GENDER, "Gender"),
        (TYPE_AGE, "Age"),
        (TYPE_GRADE, "Grade"),
        (TYPE_COLLEGE, "College"),
        (TYPE_MAJOR, "Major"),
        (TYPE_MBTI, "MBTI"),
        (TYPE_ORGANIZATION, "Organization"),
        (TYPE_CONSUMPTION, "Consumption"),
        (TYPE_CAREER, "Career"),
        (TYPE_SKILL, "Skill"),
        (TYPE_STATUS, "Status"),
    )
    name = models.CharField(max_length=64)
    type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)


class SurveyTag(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["survey", "tag"], name="unique_survey_tag")
        ]
        indexes = [
            models.Index(fields=["tag"], name="survey_tag_tag_idx"),
        ]


class UserTag(models.Model):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "tag"], name="unique_user_tag")
        ]
        indexes = [
            models.Index(fields=["tag"], name="user_tag_tag_idx"),
        ]


class UserTagWeight(models.Model):
    """记录用户和 tag 的权重，供相似性/推荐使用。

    - 当用户手动编辑（set_user_tags）时，将权重写为 1.0。
    - 当用户提交问卷时（submit_fill），相关 survey 的 tag 对应权重增加（+0.2）。
    - 当用户在任务大厅标记不感兴趣/删除（dismiss）时，权重减少 -0.2。
    - 当用户填写一半放弃（abandon）时，减少为 -0.04（即 -0.2 的五分之一）。
    权重保持在 [0.0, 5.0] 范围内以防失控。
    """

    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    weight = models.FloatField(default=0.0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "tag"], name="unique_user_tag_weight"
            )
        ]
        indexes = [
            models.Index(fields=["tag"], name="user_tagweight_tag_idx"),
            models.Index(fields=["user"], name="user_tagweight_user_idx"),
        ]


class IDVector(models.Model):
    """存储与 `user` 或 `survey` 关联的向量数据。

    - `ref_type`: 'user' 或 'survey' 等，标识 ref_id 的类型。
    - `ref_id`: 引用对象 ID（字符串/UUID）。
    - `vector`: 向量内容，使用 JSONField 存储浮点数组（也可改为二进制/外部向量库 ID）。
    - `created_at`: 写入时间，当 ref_type == 'user' 时用于标记用户向量写入时间。
    """

    ref_type = models.CharField(max_length=32)
    ref_id = models.CharField(max_length=128, db_index=True)
    # 存为 float32 bytes，以节省空间并加快整体加载（use array('f') to pack/unpack）
    vector = models.BinaryField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def set_vector(self, vec):
        """把 Python 列表浮点数转为 float32 bytes 并保存到 `vector` 字段。"""
        from array import array

        arr = array("f", vec)
        self.vector = arr.tobytes()

    def get_vector(self):
        """从二进制中恢复为 Python 列表（float）。若无向量返回 None。"""
        from array import array

        if not self.vector:
            return None
        arr = array("f")
        arr.frombytes(self.vector)
        return list(arr)

    def __str__(self):
        return f"{self.ref_type}:{self.ref_id}"

    class Meta:
        indexes = [
            models.Index(fields=["ref_type", "ref_id"], name="idvector_ref_idx"),
            models.Index(
                fields=["ref_type", "created_at"], name="idvector_type_created_idx"
            ),
        ]


class SurveyUserSimilarity(models.Model):
    """保存问卷与用户之间的余弦相似度（cosine）。

    约束：每条记录的 `survey` 必须来自 `Survey`，`user` 来自 `AppUser`，用于保证“问卷-用户”配对。
    """

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    cosine = models.FloatField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["survey", "user"], name="unique_survey_user_similarity"
            )
        ]
        indexes = [
            models.Index(fields=["cosine"], name="survey_user_cosine_idx"),
        ]

class DailyRecommendation(models.Model):
    """每日推荐缓存：每用户每天一条，存储推荐问卷ID列表和已领取奖励ID列表。"""

    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    date = models.DateField(db_index=True)
    survey_ids = models.JSONField(default=list)
    claimed_ids = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "date"], name="unique_user_daily_rec"
            )
        ]
        indexes = [
            models.Index(fields=["user", "date"], name="daily_rec_user_date_idx"),
        ]


class TaskCompletion(models.Model):
    """用户任务完成记录。

    - task_code: 任务标识，如 'daily_fill_1', 'weekly_fill_10', 'daily_login'
    - period_key: 任务周期标识，日任务用 '2026-04-08'，周任务用 '2026-W15'
    - progress: 当前进度（如已填写问卷数）
    - completed: 是否已达成完成条件
    - claimed: 是否已手动领取奖励
    """

    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    task_code = models.CharField(max_length=64)
    period_key = models.CharField(max_length=16, db_index=True)
    progress = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    claimed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "task_code", "period_key"],
                name="unique_user_task_period",
            )
        ]
        indexes = [
            models.Index(
                fields=["user", "period_key"], name="taskcompletion_user_period_idx"
            ),
        ]


class HomeModuleConfig(models.Model):
    """首页模块配置。用于编排 Feed / Trending 等模块顺序与容量。"""

    module_key = models.CharField(max_length=32, unique=True)
    title = models.CharField(max_length=64)
    enabled = models.BooleanField(default=True)
    weight = models.IntegerField(default=100)
    item_limit = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["enabled", "weight"], name="home_module_enabled_weight_idx"),
        ]