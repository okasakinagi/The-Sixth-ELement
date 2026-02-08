from django.db import models


class AppUser(models.Model):
    nickname = models.CharField(max_length=64)
    email = models.EmailField(unique=True)
    credit_score = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    activity_points = models.IntegerField(default=0)
    status = models.CharField(max_length=32, default="normal")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
    """密码重置验证码"""

    email = models.EmailField(db_index=True)
    code = models.CharField(max_length=6)  # 6位数字验证码
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["email", "is_used", "expires_at"], name="reset_code_lookup_idx"
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
    operator = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    type = models.CharField(max_length=32)
    title = models.CharField(max_length=200)
    content = models.TextField()
    status = models.CharField(max_length=32, default="unread")
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(blank=True, null=True)


class Tag(models.Model):
    TYPE_SURVEY = "survey_type"
    TYPE_INTEREST = "interest"
    TYPE_SCHOOL = "school"
    TYPE_CHOICES = (
        (TYPE_SURVEY, "Survey Type"),
        (TYPE_INTEREST, "Interest"),
        (TYPE_SCHOOL, "School"),
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
