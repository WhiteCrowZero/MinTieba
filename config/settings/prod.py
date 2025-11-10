# config/settings/prod.py
from .base import *
import os

DEBUG = False
# ALLOWED_HOSTS = ["mintieba.com", "api.mintieba.com"]
# 展示用
ALLOWED_HOSTS = ["*"]

# # 强制 HTTPS
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
#
# # 安全头部（可按需扩展）
# SECURE_HSTS_SECONDS = 31536000  # 一年
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# 生产数据库：MySQL，通过环境变量注入
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("MYSQL_DATABASE", "mintieba"),
        "USER": os.getenv("MYSQL_USER", "mintieba"),
        "PASSWORD": os.getenv("MYSQL_PASSWORD", ""),
        "HOST": os.getenv("MYSQL_HOST", "mysql"),
        "PORT": int(os.getenv("MYSQL_PORT", 3306)),
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}

# 静态文件收集路径
STATIC_ROOT = BASE_DIR / "staticfiles"

# # CORS：只放前端域名
# CORS_ALLOW_ALL_ORIGINS = False
# CORS_ALLOWED_ORIGINS = [
#     "https://mintieba.com",
#     "https://www.mintieba.com",
# ]

# JWT 生命周期按生产场景配置（这里继续用 base 默认 30min，可按业务调整）
SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = timedelta(minutes=30)

# 日志：生产环境控制台只打 WARNING+
LOGGING["handlers"]["console"]["level"] = "WARNING"

# API 文档：生产只对后台可见
SPECTACULAR_SETTINGS.update(
    {
        "SERVE_INCLUDE_SCHEMA": True,
        # 此处为了方便展示，不设置API权限
        # "SERVE_PUBLIC": False,
        # "SERVE_PERMISSIONS": [
        #     "rest_framework.permissions.IsAdminUser",
        # ],
    }
)
