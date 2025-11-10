# config/settings/base.py
from datetime import timedelta
from pathlib import Path
import os
import sys
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "apps"))

# =========================
# 环境与密钥（通用）
# =========================

env_path = BASE_DIR / "deploy" / "configs" / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# 生产环境要求通过环境变量注入
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "dev-unsafe-secret-key",  # 仅开发兜底
)

# 默认按生产安全配置，具体环境在 dev/prod 覆盖
DEBUG = False
ALLOWED_HOSTS = []

# =========================
# Django / 第三方 / 项目应用
# =========================

INSTALLED_APPS = [
    "simpleui",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_celery_beat",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    # project
    "accounts",
    "forums",
    "posts",
    "interactions",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# =========================
# 数据库（给一个安全默认，具体环境覆盖）
# =========================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# =========================
# 用户与 i18n
# =========================

AUTH_USER_MODEL = "accounts.UserAccount"

AUTHENTICATION_BACKENDS = [
    "common.auth.EmailOrUsernameBackend",
]

LANGUAGE_CODE = "zh-Hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

# =========================
# 静态资源（静态根目录由 prod 覆盖）
# =========================

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =========================
# DRF / JWT / API 文档
# =========================

REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "apps.common.exceptions.database_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "apps.common.response_renders.UnifiedJSONRenderer",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),  # 默认按生产设置
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "MiniTieba API",
    "DESCRIPTION": "Service API Docs",
    "VERSION": "1.0.0",
}

# =========================
# SimpleUI
# =========================

SIMPLEUI_DEFAULT_THEME = "admin.e-blue-pro.css"

# =========================
# 日志（基础版，级别由 DEBUG 控制）
# =========================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message} (Process:{process:d} Thread:{thread:d})",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "{levelname}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG" if DEBUG else "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "django_file": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(BASE_DIR / "logs/django.log"),
            "formatter": "verbose",
            "when": "midnight",
            "interval": 1,
            "backupCount": 30,
            "encoding": "utf-8",
            "delay": True,
        },
        "access_file": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(BASE_DIR / "logs/access.log"),
            "formatter": "verbose",
            "when": "midnight",
            "interval": 1,
            "backupCount": 30,
            "encoding": "utf-8",
            "delay": True,
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(BASE_DIR / "logs/error.log"),
            "formatter": "verbose",
            "when": "midnight",
            "interval": 1,
            "backupCount": 15,
            "encoding": "utf-8",
            "delay": True,
        },
    },
    "root": {
        "handlers": ["console", "django_file", "error_file"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "django_file", "error_file"],
            "level": "INFO",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["access_file", "error_file"],
            "level": "WARNING",
            "propagate": False,
        },
        "feat": {
            "handlers": ["console", "django_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# =========================
# 缓存 / Redis
# =========================

DEFAULT_EXPIRE_SECONDS = int(os.getenv("DEFAULT_EXPIRE_SECONDS", 300))
CAPTCHA_EXPIRE_SECONDS = int(os.getenv("CAPTCHA_EXPIRE_SECONDS", 300))
EMAIL_EXPIRE_SECONDS = int(os.getenv("EMAIL_EXPIRE_SECONDS", 300))
SMS_CODE_EXPIRE_SECONDS = int(os.getenv("SMS_CODE_EXPIRE_SECONDS", 300))

REDIS_URL = os.getenv("REDIS_BASE_URL", "redis://127.0.0.1:6379")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{REDIS_URL}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
    "captcha": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{REDIS_URL}/2",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
    "email": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{REDIS_URL}/3",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
    "sms": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{REDIS_URL}/4",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
}

# =========================
# 邮件
# =========================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.163.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 25))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = True
EMAIL_ACTIVATE_RETURN_URL = os.getenv(
    "EMAIL_ACTIVATE_RETURN_URL", "http://127.0.0.1:8000"
)

# =========================
# MinIO / OSS
# =========================

# 修正：原来 MINIO_ENDPOINT 读错了环境变量
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "127.0.0.1:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "mini-tieba")
MINIO_USE_SSL = False
DEFAULT_IMAGE_FOLDER_NAME = os.getenv("DEFAULT_IMAGE_FOLDER_NAME", "images")

OSS_MAX_IMAGE_SIZE = 5 * 1024 * 1024
OSS_ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
OSS_MAX_IMAGE_WIDTH = 2000
OSS_DEFAULT_IMAGE_QUALITY = 85

# =========================
# 腾讯短信
# =========================

TENCENTCLOUD_SECRET_ID = os.getenv("TENCENTCLOUD_SECRET_ID", "")
TENCENTCLOUD_SECRET_KEY = os.getenv("TENCENTCLOUD_SECRET_KEY", "")
TENCENT_SMS_APP_ID = os.getenv("TENCENT_SMS_APP_ID", "")
TENCENT_SMS_SIGN = os.getenv("TENCENT_SMS_SIGN", "")
TENCENT_SMS_TEMPLATE_ID = os.getenv("TENCENT_SMS_TEMPLATE_ID", "")

# =========================
# Celery
# =========================

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", f"{REDIS_URL}/15")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Shanghai"
