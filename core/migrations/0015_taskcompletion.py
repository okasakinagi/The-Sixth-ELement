# Generated manually 2026-04-08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0014_dailyrecommendation"),
    ]

    operations = [
        migrations.CreateModel(
            name="TaskCompletion",
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
                ("task_code", models.CharField(max_length=64)),
                ("period_key", models.CharField(db_index=True, max_length=16)),
                ("progress", models.IntegerField(default=0)),
                ("completed", models.BooleanField(default=False)),
                ("claimed", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddConstraint(
            model_name="taskcompletion",
            constraint=models.UniqueConstraint(
                fields=["user", "task_code", "period_key"],
                name="unique_user_task_period",
            ),
        ),
        migrations.AddIndex(
            model_name="taskcompletion",
            index=models.Index(
                fields=["user", "period_key"],
                name="taskcompletion_user_period_idx",
            ),
        ),
    ]
