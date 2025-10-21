import logging
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError, NotFound

from rest_framework.generics import (
    GenericAPIView,
    RetrieveAPIView,
    UpdateAPIView,
    RetrieveUpdateAPIView,
)
from rest_framework.views import APIView
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)

from .models import UserProfile, GenderChoices, UserAccount
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    LogoutSerializer,
    ResetPasswordSerializer,
    UserProfileSerializer,
)

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from django.db import transaction
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.common.permissions import IsSelf, CanViewUserProfile
from apps.common.auth import generate_tokens_for_user
from apps.common.utils.email_utils import EmailService

User = get_user_model()
logger = logging.getLogger("feat")


class RegisterView(GenericAPIView):
    """用户注册视图（普通注册，只支持邮箱+用户名）"""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # 发送邮件激活链接
        EmailService.send_activate_code(user.id, user.email)
        # 签发 token（包含 Access 和 Refresh）
        access_token, refresh_token = generate_tokens_for_user(user)
        logger.info(f"{user.id}:{user.username}普通注册成功")
        return Response(
            {
                "user_id": user.id,
                "username": user.username,
                "access": access_token,
                "refresh": refresh_token,
            }
        )


class LoginView(GenericAPIView):
    """普通登录视图（邮箱/用户名登录）"""

    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data.get("user")
        access_token, refresh_token = generate_tokens_for_user(user)
        logger.info(f"{user.id}:{user.username}普通登录成功")
        return Response(
            {
                "user_id": user.id,
                "username": user.username,
                "access": access_token,
                "refresh": refresh_token,
            }
        )


class LogoutView(GenericAPIView):
    """通用登出视图"""

    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated, IsSelf]

    def post(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # 转换成 Token 对象，并将 refresh_token 拉入黑名单（access短期过期后自动失效）
            refresh_token = serializer.validated_data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as e:
            logger.error(
                f"{request.user.id}:{request.user.username}token已过期或已登出，原因：{str(e)}"
            )
            return Response(
                {"detail": "token已过期或已登出"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(
                f"{request.user.id}:{request.user.username}登出失败，原因：{str(e)}"
            )
            return Response({"detail": "登出失败"}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"{request.user.id}:{request.user.username}登出成功")
        return Response({"detail": "登出成功"}, status=status.HTTP_200_OK)


class DestroyUserView(APIView):
    """通用注销账户视图"""

    permission_classes = [IsAuthenticated, IsSelf]

    @staticmethod
    def anonymize_user_account(user):
        """匿名化用户"""
        user.username = f"user_{user.id}"
        user.email = f"{user.id}@deleted.com"
        user.avatar_url = settings.DEFAULT_AVATAR_URL
        user.bio = "该用户已注销"
        user.mobile = ""
        # user.role = Role.objects.get(name="已删除用户")
        user.role = None
        user.gender = GenderChoices.OTHER
        user.is_active = False
        user.is_active_account = False
        user.is_deleted = True
        user.deleted_at = timezone.now()
        user.save()

    @staticmethod
    def anonymize_user_profile(user):
        """匿名化用户扩展信息"""
        if hasattr(user, "profile"):
            profile: UserProfile = user.profile
            profile.is_deleted = True
            profile.deleted_at = timezone.now()
            profile.birthday = None
            profile.location = None
            profile.signature = "该用户已注销"
            profile.last_login_ip = None
            profile.save()
        else:
            logger.warning(f"用户 {user.id} 没有 profile")

    def post(self, request):
        user = request.user
        try:
            # refresh token 拉入黑名单
            tokens = OutstandingToken.objects.filter(user=user)
            for t in tokens:
                BlacklistedToken.objects.get_or_create(token=t)
        except Exception as e:
            logger.error(
                f"{user.id}:{user.username}token已过期或已登出，原因：{str(e)}"
            )
            return Response(
                {"detail": "Token 注销失败"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                self.anonymize_user_account(user)
                self.anonymize_user_profile(user)
        except Exception as e:
            logger.error(f"{user.id}:{user.username}注销失败，原因：{str(e)}")
            return Response({"detail": f"注销失败"}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"{user.id}:{user.username}注销成功")
        return Response({"detail": "注销成功"}, status=status.HTTP_200_OK)


class ResetPasswordView(GenericAPIView):
    """重置密码"""

    serializer_class = ResetPasswordSerializer
    permission_classes = [IsAuthenticated, IsSelf]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data["password"]
        user = self.request.user
        try:
            # 重置密码
            user.set_password(password)
            user.save()

            # 注销 refresh token，强制当前登录状态下线（不依赖前端）
            tokens = OutstandingToken.objects.filter(user=user)
            for t in tokens:
                BlacklistedToken.objects.get_or_create(token=t)

            logger.info(f"{user.id}:{user.username}重置密码成功")
            return Response(
                {
                    "user_id": user.id,
                    "username": user.username,
                    "message": "重置密码成功",
                }
            )
        except Exception as e:
            logger.error(f"{user.id}:{user.username}重置密码失败，原因：{str(e)}")
            return Response(
                {
                    "user_id": user.id,
                    "username": user.username,
                    "message": "重置密码失败",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


#
# class OauthLoginView(GenericAPIView):
#     """第三方登录视图（可以选择登录后绑定，未绑定新创建账户）"""
#
#     serializer_class = OauthLoginSerializer
#     permission_classes = [AllowAny]
#
#     def post(self, request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#
#         type = serializer.validated_data["type"]
#         openid = serializer.validated_data["openid"]
#
#         try:
#             # 有相关账号直接登录（登录）
#             user_contact = UserContact.objects.get(type=type, openid=openid)
#             user = user_contact.user
#         except UserContact.DoesNotExist:
#             # 没有相关账号，创建新账号（注册）
#             with transaction.atomic():
#                 # 创建 User
#                 user = User.objects.create_user(
#                     username=f"{type}-{uuid.uuid4()}",
#                     password=auth.make_random_password(),
#                     is_active_account=True,
#                 )
#
#                 # 创建 UserContact
#                 user_contact = UserContact.objects.create(
#                     user=user, type=type, openid=openid, is_bound=True
#                 )
#
#         access_token, refresh_token = auth.generate_tokens_for_user(user)
#         return Response(
#             {
#                 "user_id": user.id,
#                 "username": user.username,
#                 "access": access_token,
#                 "refresh": refresh_token,
#             }
#         )
#
#
# class UserContactView(ListCreateAPIView):
#     """用户绑定的第三方登录方式视图，展示或创建"""
#
#     serializer_class = UserContactSerializer
#     pagination_class = None  # 关闭分页
#
#     def get_queryset(self):
#         return UserContact.objects.filter(user=self.request.user)
#
#
# class UserContactDetailView(RetrieveUpdateDestroyAPIView):
#     """用户绑定的第三方登录方式视图，修改或删除"""
#
#     lookup_field = "type"  # URL中传 type
#
#     def get_object(self):
#         type = self.kwargs["type"]
#         obj, _ = UserContact.objects.get_or_create(user=self.request.user, type=type)
#         return obj
#
#     def get_serializer_class(self):
#         # 更新使用 code 为 write_only 的序列化器
#         if self.request.method in ["PUT", "PATCH"]:
#             return UserContactBindSerializer
#         # 删除使用不需要 code 的序列化器
#         elif self.request.method == "DELETE":
#             return UserContactUnbindSerializer
#         # 其余如 get 可以直接获取对应的绑定联系方式的信息
#         return UserContactSerializer


class UserProfileView(RetrieveAPIView):
    """用户资料展示视图"""

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, CanViewUserProfile]

    def get_object(self):
        pk = self.kwargs.get("pk")
        if pk:
            try:
                user = UserAccount.active_objects.get(pk=pk)
            except UserAccount.DoesNotExist:
                raise NotFound(detail="当前用户不存在或已注销")
            return user.profile
        # 默认返回自己
        return self.request.user.profile

class UserProfileRetrieveUpdateView(RetrieveUpdateAPIView):
    """用户资料修改视图"""

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsSelf]

    def get_object(self):
        return self.request.user.profile


#
# class UserAvatarView(RetrieveUpdateDestroyAPIView):
#     """用户头像查看、修改、删除视图"""
#
#     serializer_class = UserAvatarSerializer
#     permission_classes = [IsAuthenticated, IsSelf, IsActiveAccount]
#     lookup_field = "id"  # 指定查找字段，但其实下面 get_object 会直接用 request.user
#
#     def get_object(self):
#         # 直接返回当前登录用户
#         return self.request.user
