from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0018_dailyrecommendation_tracking_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="RecommendationClaim",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "claimed_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "completed_at",
                    models.DateTimeField(blank=True, null=True),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("claimed", "已点击"),
                            ("completed", "已完成"),
                            ("abandoned", "超时未完成"),
                        ],
                        default="claimed",
                        max_length=20,
                    ),
                ),
                (
                    "recommendation",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="core.dailyrecommendation",
                    ),
                ),
                (
                    "survey",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recommendation_claims",
                        to="core.survey",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="core.appuser",
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        condition=models.Q(("claimed_at__isnull", False)),
                        fields=["user", "survey", "claimed_at"],
                        name="unique_user_survey_claim",
                    )
                ],
                "indexes": [
                    models.Index(
                        fields=["user", "status"], name="rc_user_status_idx"
                    ),
                    models.Index(fields=["status"], name="rc_status_idx"),
                    models.Index(fields=["claimed_at"], name="rc_claimed_at_idx"),
                ],
            },
        ),
    ]
