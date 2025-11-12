# config/settings/dev.py
from .base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]

# 开发环境允许任意来源跨域
CORS_ALLOW_ALL_ORIGINS = True

# 开发数据库：sqlite 单文件，简单稳定
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# 开发环境 JWT 可以给长一点，省得频繁登录
SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = timedelta(days=30)

# DRF 渲染器：开发环境可以加上浏览器调试界面
REST_FRAMEWORK.update(
    {
        "DEFAULT_RENDERER_CLASSES": (
            "apps.common.response_renders.UnifiedJSONRenderer",
            "rest_framework.renderers.BrowsableAPIRenderer",
        )
    }
)

# 邮件直接打到控制台，不连真实 SMTP
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# API 文档：开发环境完全开放
SPECTACULAR_SETTINGS.update(
    {
        "SERVE_INCLUDE_SCHEMA": True,
        "SERVE_PUBLIC": True,
    }
)

# 开发绘制 UML 图
INSTALLED_APPS += ["django_extensions"]
