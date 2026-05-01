from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0015_taskcompletion"),
    ]

    operations = [
        migrations.AddField(
            model_name="appuser",
            name="level",
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name="appuser",
            name="title",
            field=models.CharField(default="新手探索者", max_length=32),
        ),
    ]
