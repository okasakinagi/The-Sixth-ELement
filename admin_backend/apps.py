from django.apps import AppConfig


class AdminBackendConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin_backend"
    verbose_name = "管理员后台"