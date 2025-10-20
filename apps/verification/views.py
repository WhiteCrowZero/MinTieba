import uuid
import base64
from django.conf import settings
from captcha.image import ImageCaptcha
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.generics import GenericAPIView, get_object_or_404

# from services.permissions import IsSelf, IsActiveAccount
# from verify.serializers import (
#     EmailVerifySerializer,
#     EmailSendVerifySerializer,
#     EmailSendActivateSerializer,
# )

from apps.common.auth import make_random_code, CaptchaValidateMixin
from apps.common.utils.cache_utils import CacheService

User = get_user_model()


class CaptchaRateThrottle(AnonRateThrottle):
    rate = "5/min"  # 每个IP每分钟最多访问5次


class EmailSendRateThrottle(UserRateThrottle):
    rate = "1/min"  # 每个用户每分钟最多访问1次


class ImageCaptchaView(GenericAPIView):
    """图片验证码"""

    permission_classes = [AllowAny]
    throttle_classes = [CaptchaRateThrottle]

    def get(self, request):
        """生成图片验证码并返回给前端"""
        # 生成随机验证码
        code = make_random_code()

        # 生成验证码图片
        image = ImageCaptcha(width=280, height=90)
        img_bytes = image.generate(code).read()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")

        # 将验证码保存到 Redis
        captcha_id = str(uuid.uuid4()).replace("-", "")
        key = f"captcha:{captcha_id}"
        code = code.lower()
        CacheService.set_value(
            key,
            code,
            cache=CaptchaValidateMixin.CAPTCHA_CACHE_NAME,
            exp=int(settings.CAPTCHA_EXPIRE_SECONDS),
        )

        # 组织响应数据
        data = {
            "captcha_id": captcha_id,
            "captcha_image": f"data:image/png;base64,{img_base64}",
        }
        return Response(data, status=status.HTTP_200_OK)


# class EmailActivateView(GenericAPIView):
#     permission_classes = [AllowAny]
#
#     def get(self, request):
#         verify_code = request.query_params.get("verify_code")
#         if not verify_code:
#             return Response({"error": "缺少激活码"}, status=status.HTTP_400_BAD_REQUEST)
#
#         email = email_service.check_activate_code(verify_code)
#         if not email:
#             return Response(
#                 {"error": "邮箱激活失败或激活码过期"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#
#         user = get_object_or_404(User, email=email)
#         if user.is_active_account:
#             return Response({"message": "邮箱已激活"}, status=status.HTTP_200_OK)
#
#         user.is_active_account = True
#         user.save()
#
#         return Response({"message": "邮箱激活成功"}, status=status.HTTP_200_OK)
#
#
# class EmailActivateSendView(GenericAPIView):
#     permission_classes = [IsAuthenticated, IsSelf]
#     throttle_classes = [EmailSendRateThrottle]
#     serializer_class = EmailSendActivateSerializer
#
#     def post(self, request):
#         email = request.data.get("email")
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#
#         email_service.send_activate(email)
#         return Response({"message": "邮箱激活链接发送成功"}, status=status.HTTP_200_OK)
#
#
# class EmailSendVerifyView(GenericAPIView):
#     serializer_class = EmailSendVerifySerializer
#     throttle_classes = [EmailSendRateThrottle]
#     permission_classes = [IsAuthenticated, IsSelf, IsActiveAccount]
#
#     def post(self, request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#
#         new_email = serializer.validated_data.get("new_email")
#         email_service.send_verify(new_email)
#
#         return Response({"message": "邮箱验证码发送成功"}, status=status.HTTP_200_OK)
#
#
# class EmailVerifyView(GenericAPIView):
#     serializer_class = EmailVerifySerializer
#     permission_classes = [IsAuthenticated, IsSelf, IsActiveAccount]
#
#     def post(self, request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#
#         verify_code = serializer.validated_data.get("verify_code")
#         email = serializer.validated_data.get("email")
#         new_email = serializer.validated_data.get("new_email")
#
#         is_valid = email_service.check_verify_code(new_email, verify_code)
#         if not is_valid:
#             return Response(
#                 {"error": "邮箱激活失败或激活码过期"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#
#         user = get_object_or_404(User, email=email)
#         user.email = new_email
#         user.save()
#
#         return Response({"message": "邮箱修改成功"}, status=status.HTTP_200_OK)
