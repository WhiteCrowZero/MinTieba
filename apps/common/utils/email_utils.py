import uuid
from django.conf import settings
from django.urls import reverse
from urllib.parse import urlencode

from apps.common.auth import make_random_code
from apps.common.tasks import send_email
from apps.common.utils.cache_utils import CacheService


class EmailService:
    EMAIL_CACHE_NAME = "email"

    @staticmethod
    def send_activate_code(email):
        """发送一次性激活链接"""
        # 生成激活链接
        verify_code = uuid.uuid4().hex
        verify_code.replace("-", "")
        base_url = settings.EMAIL_ACTIVATE_RETURN_URL
        path = reverse("activate-email-verify")
        query = urlencode({"verify_code": verify_code})
        verify_url = f"{base_url}{path}?{query}"

        # 保存验证码到缓存
        key = f"email:activate:{verify_code}"
        CacheService.set_value(
            key,
            email,
            cache=EmailService.EMAIL_CACHE_NAME,
            exp=int(settings.EMAIL_EXPIRE_SECONDS),
        )

        # 异步发送激活链接
        send_email.delay(email, verify_code=verify_url, mode="activate")
        return True

    @staticmethod
    def check_activate_code(verify_code):
        """校验激活链接"""
        key = f"email:activate:{verify_code}"
        email = CacheService.get_value(key, EmailService.EMAIL_CACHE_NAME)
        # 一次性，校验一次后，无论对错，立即删除
        CacheService.del_value(key, cache=EmailService.EMAIL_CACHE_NAME)

        # 如果存在就说明之前调用过激活接口，返回email
        if not email:
            return None
        return email

    @staticmethod
    def send_verify(email):
        """发送邮箱验证码"""
        # 生成验证码
        verify_code = make_random_code(length=6)
        key = f"email:verify:{email}"
        CacheService.set_value(
            key,
            verify_code,
            cache=EmailService.EMAIL_CACHE_NAME,
            exp=int(settings.EMAIL_EXPIRE_SECONDS),
        )

        # 发送邮件
        send_email.delay(email, verify_code, mode="verify")
        return True

    @staticmethod
    def check_verify_code(email, verify_code):
        """校验邮箱验证码"""
        key = f"email:verify:{email}"
        right_code = CacheService.get_value(key, EmailService.EMAIL_CACHE_NAME)
        # 一次性，校验一次后，无论对错，立即删除
        CacheService.del_value(key, cache=EmailService.EMAIL_CACHE_NAME)

        # 校验验证码
        if verify_code != right_code:
            return False
        return True
