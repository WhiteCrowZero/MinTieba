import random
import string

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common.utils.cache_utils import CacheService

# from services.oauth import OauthWeiboVerify

User = get_user_model()


def generate_tokens_for_user(user):
    """使用 simple-jwt 生成 access/refresh token"""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


#
# def make_random_password(length=8):
#     """生成随机密码"""
#     chars = string.ascii_letters + string.digits + string.punctuation
#     return ''.join(random.choices(chars, k=length))
#
#
def make_random_code(length=5):
    """生成含有字母数字的随机验证码"""
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


class CaptchaValidateMixin:
    """验证码校验 Mixin 工具类"""

    CAPTCHA_CACHE_NAME = "captcha"
    captcha_id_field = "captcha_id"
    captcha_code_field = "captcha_code"

    def check_captcha(self, captcha_id, captcha_code):
        """验证码校验方法"""
        key = f"captcha:{captcha_id}"
        right_code = CacheService.get_value(key, cache=self.CAPTCHA_CACHE_NAME)
        CacheService.del_value(key, cache=self.CAPTCHA_CACHE_NAME)
        if (
            not captcha_code
            or not right_code
            or captcha_code.lower() != right_code.lower()
        ):
            return False
        return True

    def validate_captcha(self, attrs):
        captcha_id = attrs.get(self.captcha_id_field)
        captcha_code = attrs.get(self.captcha_code_field)
        if not self.check_captcha(captcha_id, captcha_code):
            raise serializers.ValidationError({self.captcha_code_field: "验证码错误"})
        return attrs


class EmailOrUsernameBackend(ModelBackend):
    """
    自定义验证后端，支持用户名或邮箱登录
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get("email")
        try:
            if "@" in username:
                user = User.objects.get(email=username)
            else:
                user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        if user.check_password(password):
            return user
        return None


#
# # 系列第三方验证接口
# oauth_weibo_verify = OauthWeiboVerify()
#
#
# def oauth_authentication(type, code):
#     try:
#         if type == 'weibo':
#             openid = oauth_weibo_verify.authentication(code)
#             return openid
#         elif type == 'google':
#             pass
#         elif type == 'facebook':
#             pass
#         elif type == 'wechat':
#             pass
#         elif type == 'qq':
#             pass
#         else:
#             return None
#     except Exception as e:
#         return None
#
#     # # 测试业务逻辑用
# return f'{type}-{code}-test'
