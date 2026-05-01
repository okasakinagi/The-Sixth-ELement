from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0017_alter_auditlog_operator"),
    ]

    operations = [
        migrations.AddField(
            model_name="dailyrecommendation",
            name="clicked_ids",
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name="dailyrecommendation",
            name="deleted_ids",
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name="dailyrecommendation",
            name="refresh_count",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="dailyrecommendation",
            name="refreshed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
