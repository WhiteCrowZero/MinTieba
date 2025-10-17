import uuid
from django.utils import timezone

from rest_framework.generics import (
    RetrieveUpdateDestroyAPIView,
    RetrieveUpdateAPIView,
    ListCreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    GenericAPIView,
)
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)

from services.code_send import email_service
from social.models import Like
from .models import UserContact
from articles.models import ReadingHistory
from django.contrib.auth import get_user_model
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    OauthLoginSerializer,
    UserInfoSerializer,
    UserContactSerializer,
    ResetPasswordSerializer,
    LogoutSerializer,
    UserContactBindSerializer,
    UserContactUnbindSerializer,
    UserAvatarSerializer,
)
from rest_framework.response import Response
from services import auth
from services.permissions import IsSelf, IsActiveAccount
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated, AllowAny


from common.auth import generate_tokens_for_user

User = get_user_model()


class RegisterView(GenericAPIView):
    """用户注册视图（普通注册，只支持邮箱+用户名）"""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # 发送邮件激活链接
        email_service.send_activate(user.email)
        # 签发 token（包含 Access 和 Refresh）
        access_token, refresh_token = generate_tokens_for_user(user)
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

    def post(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # 转换成 Token 对象，并将 refresh_token 拉入黑名单（access短期过期后自动失效）
            refresh_token = serializer.validated_data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception as e:
            print(e)
            return Response({"detail": "登出失败"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "登出成功"}, status=status.HTTP_200_OK)


class DestroyUserView(GenericAPIView):
    """通用注销账户视图"""

    serializer_class = LogoutSerializer

    @staticmethod
    def anonymize_user(user):
        """匿名化用户"""
        user.username = f"user_{user.id}"
        user.email = ""
        user.avatar = "avatar/default.png"
        user.bio = "该用户已注销"
        user.is_active = False
        user.is_active_account = False
        user.is_deleted = True
        user.deleted_at = timezone.now()
        user.save()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # refresh token 拉入黑名单
            refresh_token = serializer.validated_data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {"detail": "Token 注销失败"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 对敏感数据（如联系方式、阅读历史）进行硬删除，其他（如评论）级联设置为 NULL 软删除
            with transaction.atomic():
                user = request.user
                UserContact.objects.filter(user=user).delete()
                ReadingHistory.objects.filter(user=user).delete()
                Like.objects.filter(
                    user=user
                ).delete()  # 临时性数据，关联较少，直接硬删除
                self.anonymize_user(user)
        except Exception as e:
            return Response(
                {"detail": f"注销失败: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response({"detail": "注销成功"}, status=status.HTTP_200_OK)


class ResetPasswordView(GenericAPIView):
    """重置密码"""

    serializer_class = ResetPasswordSerializer

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

            return Response(
                {
                    "user_id": user.id,
                    "username": user.username,
                    "message": "重置密码成功",
                }
            )
        except Exception as e:
            return Response(
                {
                    "user_id": user.id,
                    "username": user.username,
                    "message": "重置密码失败",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class OauthLoginView(GenericAPIView):
    """第三方登录视图（可以选择登录后绑定，未绑定新创建账户）"""

    serializer_class = OauthLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        type = serializer.validated_data["type"]
        openid = serializer.validated_data["openid"]

        try:
            # 有相关账号直接登录（登录）
            user_contact = UserContact.objects.get(type=type, openid=openid)
            user = user_contact.user
        except UserContact.DoesNotExist:
            # 没有相关账号，创建新账号（注册）
            with transaction.atomic():
                # 创建 User
                user = User.objects.create_user(
                    username=f"{type}-{uuid.uuid4()}",
                    password=auth.make_random_password(),
                    is_active_account=True,
                )

                # 创建 UserContact
                user_contact = UserContact.objects.create(
                    user=user, type=type, openid=openid, is_bound=True
                )

        access_token, refresh_token = auth.generate_tokens_for_user(user)
        return Response(
            {
                "user_id": user.id,
                "username": user.username,
                "access": access_token,
                "refresh": refresh_token,
            }
        )


class UserContactView(ListCreateAPIView):
    """用户绑定的第三方登录方式视图，展示或创建"""

    serializer_class = UserContactSerializer
    pagination_class = None  # 关闭分页

    def get_queryset(self):
        return UserContact.objects.filter(user=self.request.user)


class UserContactDetailView(RetrieveUpdateDestroyAPIView):
    """用户绑定的第三方登录方式视图，修改或删除"""

    lookup_field = "type"  # URL中传 type

    def get_object(self):
        type = self.kwargs["type"]
        obj, _ = UserContact.objects.get_or_create(user=self.request.user, type=type)
        return obj

    def get_serializer_class(self):
        # 更新使用 code 为 write_only 的序列化器
        if self.request.method in ["PUT", "PATCH"]:
            return UserContactBindSerializer
        # 删除使用不需要 code 的序列化器
        elif self.request.method == "DELETE":
            return UserContactUnbindSerializer
        # 其余如 get 可以直接获取对应的绑定联系方式的信息
        return UserContactSerializer


class UserInfoView(RetrieveAPIView):
    """用户基本信息展示视图"""

    serializer_class = UserInfoSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="user_id",
                type=int,
                required=False,
                location="query",
                description="指定用户ID，如果不填则返回当前登录用户信息",
            )
        ],
        operation_id="user_info_retrieve",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        # 通过查询字符串参数，区分是查询自己的用户信息页，还是他人的用户信息页
        user_id = self.request.query_params.get("user_id")
        if user_id:
            return User.objects.get(id=user_id)
        return self.request.user


class UserInfoDetailView(RetrieveUpdateAPIView):
    """用户基本信息修改视图"""

    serializer_class = UserInfoSerializer
    # 必须认证为自己的用户，才能修改自己的详情页
    permission_classes = [IsAuthenticated, IsSelf, IsActiveAccount]
    lookup_field = "id"  # 指定查找字段，但其实下面 get_object 会直接用 request.user

    def get_object(self):
        # 直接返回当前登录用户
        return self.request.user


class UserAvatarView(RetrieveUpdateDestroyAPIView):
    """用户头像查看、修改、删除视图"""

    serializer_class = UserAvatarSerializer
    permission_classes = [IsAuthenticated, IsSelf, IsActiveAccount]
    lookup_field = "id"  # 指定查找字段，但其实下面 get_object 会直接用 request.user

    def get_object(self):
        # 直接返回当前登录用户
        return self.request.user
