# Generated manually 2026-04-08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0013_teammember_role_teammember_tm_team_role_idx"),
    ]

    operations = [
        migrations.CreateModel(
            name="DailyRecommendation",
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
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="core.appuser",
                    ),
                ),
                ("date", models.DateField(db_index=True)),
                ("survey_ids", models.JSONField(default=list)),
                ("claimed_ids", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddConstraint(
            model_name="dailyrecommendation",
            constraint=models.UniqueConstraint(
                fields=["user", "date"], name="unique_user_daily_rec"
            ),
        ),
        migrations.AddIndex(
            model_name="dailyrecommendation",
            index=models.Index(
                fields=["user", "date"], name="daily_rec_user_date_idx"
            ),
        ),
    ]
