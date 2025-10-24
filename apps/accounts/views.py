import base64
import logging
import random
import uuid

from captcha.image import ImageCaptcha
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound

from rest_framework.generics import (
    GenericAPIView,
    RetrieveAPIView,
    RetrieveUpdateAPIView,
    UpdateAPIView,
    ListAPIView,
)
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)

from common.permissions import RBACPermission
from common.utils.cache_utils import CacheService
from common.utils.sms_utils import SMSService
from .models import (
    UserProfile,
    GenderChoices,
    UserAccount,
    Role,
    Permission,
    RolePermissionMap,
)
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    LogoutSerializer,
    ResetPasswordSerializer,
    UserProfileSerializer,
    UserBasicInfoSerializer,
    UserAvatarSerializer,
    UserEmailUpdateSerializer,
    UserEmailSendSerializer,
    UserMobileUpdateSerializer,
    UserMobileVerifySendSerializer,
    UserEmailActivateSerializer,
    RoleListSerializer,
    PermissionListSerializer,
    RoleNestedSerializer,
    RolePermissionSerializer,
)

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from django.db import transaction
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.common.permissions import IsSelf, CanViewUserProfile
from apps.common.auth import (
    generate_tokens_for_user,
    make_random_code,
    CaptchaValidateMixin,
)
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
        EmailService.send_activate_code(user.email)
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


class UserBasicInfoView(RetrieveAPIView):
    """用户基本信息展示视图"""

    serializer_class = UserBasicInfoSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        pk = self.kwargs.get("pk")
        if pk:
            try:
                user = UserAccount.active_objects.get(pk=pk)
            except UserAccount.DoesNotExist:
                raise NotFound(detail="当前用户不存在或已注销")
            return user
        else:
            raise NotFound(detail="当前用户不存在或已注销")


class UserBasicInfoUpdateView(UpdateAPIView):
    """用户基本信息更新视图"""

    serializer_class = UserBasicInfoSerializer
    permission_classes = [IsAuthenticated, IsSelf]

    def get_object(self):
        return self.request.user


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
        else:
            raise NotFound(detail="当前用户不存在或已注销")


class UserProfileRetrieveUpdateView(RetrieveUpdateAPIView):
    """用户资料修改视图"""

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsSelf]

    def get_object(self):
        try:
            profile = UserProfile.objects.get(user=self.request.user)
            return profile
        except Exception as e:
            logger.error(
                f"获取用户扩展资料失败，原因：{str(e)}，用户id：{self.request.user.id}"
            )
            raise NotFound(detail="当前用户不存在或已注销")


class UserAvatarView(UpdateAPIView):
    """用户头像查看、修改视图"""

    serializer_class = UserAvatarSerializer
    permission_classes = [IsAuthenticated, IsSelf]

    def get_object(self):
        return self.request.user


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


class UserEmailUpdateView(UpdateAPIView):
    """用户邮箱修改视图（验证验证码）"""

    serializer_class = UserEmailUpdateSerializer
    permission_classes = [IsAuthenticated, IsSelf]

    def get_object(self):
        return self.request.user


class UserEmailVerifySendView(GenericAPIView):
    """用户邮箱验证码发送视图"""

    serializer_class = UserEmailSendSerializer
    permission_classes = [IsAuthenticated, IsSelf]

    def post(self, request):
        # 校验数据
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 发送验证码
        email = serializer.validated_data["email"]
        EmailService.send_verify(email)
        logger.info(f"用户{request.user.id}发送邮箱验证码成功，邮箱地址：{email}")
        return Response({"detail": "邮箱验证码发送成功"}, status=status.HTTP_200_OK)


class UserActivateSendView(GenericAPIView):
    """用户激活链接发送视图"""

    serializer_class = UserEmailSendSerializer
    permission_classes = [IsAuthenticated, IsSelf]

    def post(self, request):
        # 检查是否已经激活
        if request.user.is_active_account:
            return Response({"activate": "当前用户已经激活"}, status=status.HTTP_200_OK)

        # 校验数据
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 发送验证码
        email = serializer.validated_data["email"]
        EmailService.send_activate_code(email)
        logger.info(f"用户{request.user.id}发送邮箱激活链接成功，邮箱地址：{email}")
        return Response({"activate": "邮箱激活链接发送成功"}, status=status.HTTP_200_OK)


class UserActivateVerifyView(GenericAPIView):
    """用户激活链接验证视图"""

    serializer_class = UserEmailActivateSerializer
    permission_classes = [IsAuthenticated, IsSelf]

    def get(self, request):
        # 校验数据
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # 激活用户
        request.user.is_active_account = True
        request.user.save()
        logger.info(f"用户{request.user.id}激活成功")
        return Response({"activate": "用户激活成功"}, status=status.HTTP_200_OK)


class UserMobileUpdateView(UpdateAPIView):
    """用户手机号修改视图（验证验证码）"""

    serializer_class = UserMobileUpdateSerializer
    permission_classes = [IsAuthenticated, IsSelf]

    def get_object(self):
        return self.request.user


class UserMobileVerifySendView(GenericAPIView):
    """用户手机号验证码发送视图"""

    serializer_class = UserMobileVerifySendSerializer
    permission_classes = [IsAuthenticated, IsSelf]

    def post(self, request):
        # 校验数据
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 发送验证码
        mobile = serializer.validated_data["mobile"]
        random_code = random.randint(100000, 999999)
        SMSService.send_code(mobile, random_code)
        logger.info(f"用户{request.user.id}发送手机验证码成功，手机号：{mobile}")
        return Response({"detail": "手机验证码发送成功"}, status=status.HTTP_200_OK)


class RoleListView(ListAPIView):
    """角色列表视图"""

    queryset = Role.objects.all()
    serializer_class = RoleListSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    permission_code = "rbac.view_roles"


class PermissionListView(ListAPIView):
    """权限列表视图"""

    serializer_class = PermissionListSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    permission_code = "rbac.view_permissions"

    def get_queryset(self):
        # 只获取根节点（parent is null）
        return Permission.objects.filter(parent__isnull=True).prefetch_related(
            "children"
        )


class RolePermissionView(GenericAPIView):
    """角色对应权限查看视图"""

    serializer_class = RolePermissionSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    permission_code = "rbac.manage_role_permissions"

    def get(self, request, role_id):
        """获取角色当前权限"""
        try:
            role = Role.objects.get(pk=role_id)
        except Role.DoesNotExist:
            return Response({"detail": "角色不存在"}, status=status.HTTP_404_NOT_FOUND)

        # 获取该角色数据
        role_data = RoleNestedSerializer(role).data
        # 获取该角色的所有权限映射
        role_permissions = RolePermissionMap.objects.filter(role=role)
        # 序列化权限映射记录
        serializer = self.get_serializer(role_permissions, many=True)

        # 返回包含角色基本信息和权限列表的结构
        return Response(
            {
                "role": role_data,
                "permissions": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
