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
    reward_points = models.IntegerField(default=0)
    publish_cost_points = models.IntegerField(default=0)
    deadline = models.DateTimeField(blank=True, null=True)
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
            models.Index(fields=["status", "deadline"], name="survey_status_deadline_idx"),
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
            models.Index(fields=["survey", "status"], name="response_survey_status_idx"),
            models.Index(fields=["user", "created_at"], name="response_user_created_idx"),
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
            models.Index(fields=["user", "created_at"], name="pointslog_user_created_idx"),
        ]


class Report(models.Model):
    reporter = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    target_type = models.CharField(max_length=32)
    target_id = models.BigIntegerField()
    reason = models.CharField(max_length=200)
    detail = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=32, default="open")
    handled_by = models.ForeignKey(
        AppUser, on_delete=models.SET_NULL, blank=True, null=True, related_name="handled_reports"
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
    name = models.CharField(max_length=64)
    type = models.CharField(max_length=32)
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
