from .base import *

DEBUG = False
ALLOWED_HOSTS = ['mintieba.com', 'api.mintieba.com']

# 强制 HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# # 日志输出到文件
# LOGGING['handlers']['file']['filename'] = '/var/log/django/django.log'
