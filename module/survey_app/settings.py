import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "corsheaders",
    "core",
    "personal_homepage",
    "survey_management",
    "task_hall",
    "team_messaging",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

# CORS 配置
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = "survey_app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    }
]

WSGI_APPLICATION = "survey_app.wsgi.application"
ASGI_APPLICATION = "survey_app.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DJANGO_DB_NAME", "sixth_element"),
        "USER": os.environ.get("DJANGO_DB_USER", "sixth_element"),
        "PASSWORD": os.environ.get("DJANGO_DB_PASSWORD", "123456"),
        "HOST": os.environ.get("DJANGO_DB_HOST", "localhost"),
        "PORT": os.environ.get("DJANGO_DB_PORT", "3306"),
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# 日志配置 - 在控制台显示详细错误
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}

# 开发环境下显示详细错误
DEBUG_PROPAGATE_EXCEPTIONS = True

# 推荐模式：'personalized' 使用相似度推荐，'random' 使用纯随机候选
# 可通过环境变量 RECOMMENDATION_MODE 修改（修改后需要重启服务以生效）
RECOMMENDATION_MODE = os.environ.get("RECOMMENDATION_MODE", "personalized")

# 邮件配置（腾讯企业邮 SMTP，双账户 fallback）
# 所有敏感信息通过环境变量注入，不在此硬编码
EMAIL_BACKEND = "core.email_backend.FallbackEmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.exmail.qq.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "465"))
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "true").lower() == "true"
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "false").lower() == "true"
# 以下两项由 FallbackEmailBackend 按账户动态设置，此处仅作 Django 默认值
EMAIL_HOST_USER = os.environ.get("EMAIL_PRIMARY_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_PRIMARY_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("EMAIL_PRIMARY_USER", "noreply@example.com")

# 缓存配置
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://redis:6379/0"),
        "TIMEOUT": 3600,  # 1小时
        "OPTIONS": {
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
        },
    }
}
