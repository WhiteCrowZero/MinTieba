import uuid
from django.conf import settings

from apps.common.auth import make_random_code
from apps.common.tasks import send_email
from apps.common.utils.cache_utils import CacheService


class EmailService:
    EMAIL_CACHE_NAME = "email"
    EMAIL_LIMIT_EXPIRE = 60

    @staticmethod
    def send_activate_code(user_id, email):
        """一次性激活链接，同一用户60秒限制调用一次"""
        # 限制频率的缓存 key
        limit_key = f"email:limit:{user_id}"
        # 如果存在限制标志，说明 60 秒内已发送过
        if CacheService.get_value(limit_key, EmailService.EMAIL_CACHE_NAME):
            raise ValueError("请勿频繁操作，60 秒后再试")

        # 生成激活链接
        verify_code = uuid.uuid4().hex
        verify_code.replace("-", "")
        verify_url = f"{settings.EMAIL_ACTIVATE_RETURN_URL}/verify/email/activate?verify_code={verify_code}"
        # 保存验证码到缓存
        key = f"email:{user_id}:{email}"
        CacheService.set_value(
            key,
            verify_code,
            cache=EmailService.EMAIL_CACHE_NAME,
            exp=int(settings.EMAIL_EXPIRE_SECONDS),
        )

        # 设置限制标识，60 秒过期
        CacheService.set_value(
            limit_key,
            True,
            cache=EmailService.EMAIL_CACHE_NAME,
            exp=int(EmailService.EMAIL_LIMIT_EXPIRE),
        )
        # 异步发送激活链接
        send_email.delay(email, verify_code=verify_url)

        return True

    # def send_verify(self, email):
    #     """邮箱更改验证码，次数频率进行限制"""
    #     # 生成验证码
    #     verify_code = make_random_code(length=6)
    #     key = f"email:{email}"
    #     cache_verify_service.set_verify_code(
    #         key, verify_code, cache=self.EMAIL_CACHE_NAME
    #     )
    #
    #     # 发送邮件
    #     send_email.delay(email, verify_code, mode="verify")
    #
    #     return True
    #
    # def check_verify_code(self, email, verify_code):
    #     key = f"email:{email}"
    #     right_code = cache_verify_service.get_verify_code(key, self.EMAIL_CACHE_NAME)
    #     # 一次性，校验一次后，无论对错，立即删除
    #     cache_verify_service.del_verify_code(key, cache=self.EMAIL_CACHE_NAME)
    #     if verify_code != right_code:
    #         return False
    #     return True
    #
    # def check_activate_code(self, verify_code):
    #     key = f"email:{verify_code}"
    #     email = cache_verify_service.get_verify_code(key, self.EMAIL_CACHE_NAME)
    #     # 一次性，校验一次后，无论对错，立即删除
    #     cache_verify_service.del_verify_code(key, cache=self.EMAIL_CACHE_NAME)
    #     if not email:
    #         return None
    #     return email
