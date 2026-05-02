from django.db import migrations, models


def seed_home_module_configs(apps, schema_editor):
    HomeModuleConfig = apps.get_model("core", "HomeModuleConfig")
    defaults = [
        {
            "module_key": "feed",
            "title": "为你推荐",
            "enabled": True,
            "weight": 100,
            "item_limit": 12,
        },
        {
            "module_key": "trending",
            "title": "热门趋势",
            "enabled": True,
            "weight": 80,
            "item_limit": 8,
        },
    ]
    for item in defaults:
        HomeModuleConfig.objects.update_or_create(
            module_key=item["module_key"],
            defaults=item,
        )


def unseed_home_module_configs(apps, schema_editor):
    HomeModuleConfig = apps.get_model("core", "HomeModuleConfig")
    HomeModuleConfig.objects.filter(module_key__in=["feed", "trending"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0025_appuser_level_title"),
    ]

    operations = [
        migrations.CreateModel(
            name="HomeModuleConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("module_key", models.CharField(max_length=32, unique=True)),
                ("title", models.CharField(max_length=64)),
                ("enabled", models.BooleanField(default=True)),
                ("weight", models.IntegerField(default=100)),
                ("item_limit", models.IntegerField(default=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "indexes": [models.Index(fields=["enabled", "weight"], name="home_module_enabled_weight_idx")],
            },
        ),
        migrations.RunPython(seed_home_module_configs, reverse_code=unseed_home_module_configs),
    ]
