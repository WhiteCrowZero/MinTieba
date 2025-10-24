import logging
from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from common.utils.email_utils import EmailService
from common.utils.oss_utils import MinioClientWrapper
from .models import UserProfile, Role, Permission, RolePermissionMap
from apps.common.auth import CaptchaValidateMixin
from apps.common.utils.oss_utils import OssService

UserModel = get_user_model()
logger = logging.getLogger("feat")


class RegisterSerializer(CaptchaValidateMixin, serializers.ModelSerializer):
    """普通注册序列化器，负责用户名或者邮箱注册"""

    # 密码和二次确认密码
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)

    # 用户和邮箱保持唯一性，防止重复
    username = serializers.CharField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=UserModel.objects.all(), message="该用户名已被使用"
            )
        ],
    )
    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(queryset=UserModel.objects.all(), message="该邮箱已被注册")
        ],
    )

    # 额外添加的校验码字段
    captcha_id = serializers.CharField(write_only=True)
    captcha_code = serializers.CharField(write_only=True)

    class Meta:
        model = UserModel
        fields = [
            "username",
            "email",
            "password",
            "confirm_password",
            "captcha_id",
            "captcha_code",
        ]

    def validate(self, attrs):
        if not settings.DEBUG:
            # 单独使用工具类校验 captcha
            attrs = self.validate_captcha(attrs)  # 直接传 attrs
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"password": "两次输入的密码不一致"})
        return attrs

    def validate_username(self, value):
        if "@" in value or "_" in value:
            raise serializers.ValidationError({"username": "不能含有 @ 或 _ 符号"})
        return value

    def create(self, validated_data):
        # 保留密码字段
        password = validated_data.pop("password")

        # 其余字段检验完后丢弃
        validated_data.pop("confirm_password")
        validated_data.pop("captcha_id")
        validated_data.pop("captcha_code")

        # 事务保证用户主模型account和对应的profile表一起创建
        with transaction.atomic():
            # 其余字段创建模型
            user = UserModel(**validated_data)
            user.set_password(password)
            user.save()

            # 创建用户资料
            UserProfile.objects.create(user=user)

        return user


class LoginSerializer(serializers.Serializer):
    """普通登录序列化器"""

    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        identifier = attrs.get("username") or attrs.get("email")
        password = attrs.get("password")

        if not identifier:
            raise serializers.ValidationError("用户名或邮箱不能为空")

        # authenticate 会自动判断用户名或邮箱
        user = authenticate(username=identifier, password=password)

        # 检查用户状态
        if not user:
            raise serializers.ValidationError("用户名/邮箱或密码错误")
        if not user.is_active:
            raise serializers.ValidationError("用户账户已被禁用")

        attrs["user"] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    """登出序列化器"""

    refresh = serializers.CharField()


class ResetPasswordSerializer(serializers.Serializer):
    """密码重置序列化器"""

    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"password": "两次输入的密码不一致"})
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """用户扩展信息展示/修改序列化器"""

    class Meta:
        model = UserProfile
        fields = [
            "user_id",
            "birthday",
            "location",
            "signature",
            "exp_points",
            "level",
            "last_login_ip",
            "privacy_settings",
        ]
        read_only_fields = ["user_id", "exp_points", "level", "last_login_ip"]
        extra_kwargs = {
            "birthday": {"required": False},
            "location": {"required": False},
            "signature": {"required": False},
            "privacy_settings": {"required": False},
        }


class UserBasicInfoSerializer(serializers.ModelSerializer):
    """用户基本信息展示/修改序列化器"""

    username = serializers.CharField(
        required=False,
        validators=[
            UniqueValidator(
                queryset=UserModel.objects.all(), message="该用户名已被使用"
            )
        ],
    )

    class Meta:
        model = UserModel
        fields = [
            "id",
            "username",
            "email",
            "mobile",
            "avatar_url",
            "bio",
            "gender",
        ]
        read_only_fields = ["id", "email", "mobile", "avatar_url"]
        extra_kwargs = {
            "bio": {"required": False},
            "gender": {"required": False},
        }

    def validate_username(self, value):
        if "@" in value or "_" in value:
            raise serializers.ValidationError({"username": "不能含有 @ 或 _ 符号"})
        return value


class UserAvatarSerializer(serializers.ModelSerializer):
    """用户头像查看、修改序列化器"""

    avatar_file = serializers.ImageField(write_only=True, required=True)

    class Meta:
        model = UserModel
        fields = ["avatar_file", "avatar_url"]
        read_only_fields = ["avatar_url"]

    def validate_avatar_file(self, f):
        if f.size > getattr(settings, "OSS_MAX_IMAGE_SIZE", 5 * 1024 * 1024):
            raise serializers.ValidationError("文件大小超过限制")
        return f

    def update(self, instance, validated_data):
        # 取出上传文件
        logger.info(f"用户 {self.context['request'].user} 正在上传图片")
        avatar_file = validated_data.pop("avatar_file", None)
        if avatar_file:
            # 上传到 OSS，返回 URL
            try:
                oss_url = self.upload_to_oss(avatar_file)
                instance.avatar_url = oss_url
            except Exception as e:
                logger.error(f"用户 {self.context['request'].user} 上传图片失败: {e}")
                raise serializers.ValidationError("上传图片失败")
        else:
            logger.warning(f"用户 {self.context['request'].user} 没有上传图片")
            return instance

        instance.save()
        logger.info(f"用户 {self.context['request'].user} 上传图片成功")
        return instance

    def upload_to_oss(self, file):
        """上传文件到 OSS，并返回 URL"""
        data = OssService.upload_image(
            uploaded_file=file,
            folder_name="avatar",
            compress=True,
            client_wrapper=MinioClientWrapper,  # 压缩
        )
        oss_url = data.get("url")
        return oss_url


class UserEmailUpdateSerializer(serializers.ModelSerializer):
    """用户邮箱修改序列化器"""

    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(queryset=UserModel.objects.all(), message="该邮箱已被注册")
        ],
    )
    verify_code = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = UserModel
        fields = ["email", "verify_code"]
        read_only_fields = ["email"]

    def validate(self, attrs):
        email = attrs.get("email")
        verify_code = attrs.pop("verify_code")
        # 校验验证码
        if not EmailService.check_verify_code(email, verify_code):
            raise serializers.ValidationError({"verify_code": "验证码错误"})
        return attrs


class UserEmailSendSerializer(serializers.ModelSerializer):
    """用户邮箱验证码发送序列化器"""

    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(queryset=UserModel.objects.all(), message="该邮箱已被注册")
        ],
    )

    class Meta:
        model = UserModel
        fields = ["email"]


class UserEmailActivateSerializer(serializers.ModelSerializer):
    """用户账户激活序列化器（通过邮件）"""

    verify_code = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = UserModel
        fields = ["verify_code"]

    def validate(self, attrs):
        verify_code = attrs.pop("verify_code")
        # 校验验证码
        if not EmailService.check_activate_code(verify_code):
            raise serializers.ValidationError({"verify_code": "激活链接错误或失效"})
        return attrs


class UserMobileUpdateSerializer(serializers.ModelSerializer):
    """用户手机号修改序列化器"""

    pass


class UserMobileVerifySendSerializer(serializers.ModelSerializer):
    """用户手机号验证码发送序列化器"""

    pass


class RoleListSerializer(serializers.ModelSerializer):
    """角色列表序列化器"""

    class Meta:
        model = Role
        fields = ["id", "name", "description", "level"]


class PermissionListSerializer(serializers.ModelSerializer):
    """权限列表序列化器（支持层级）"""

    parent = serializers.PrimaryKeyRelatedField(read_only=True)
    children = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Permission
        fields = [
            "id",
            "name",
            "code",
            "type",
            "parent",
            "description",
            "category",
            "children",
        ]

    def get_children(self, obj):
        """递归获取子权限"""
        children = obj.children.all()
        if not children:
            return []
        return PermissionListSerializer(children, many=True).data


class RoleNestedSerializer(serializers.ModelSerializer):
    """角色嵌套序列化器"""

    class Meta:
        model = Role
        fields = ["id", "name", "level"]


class PermissionNestedSerializer(serializers.ModelSerializer):
    """权限嵌套序列化器"""
    parent = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Permission
        fields = ["id", "name", "code", "type", "parent"]


class RolePermissionSerializer(serializers.ModelSerializer):
    """角色权限序列化器"""

    permission = PermissionNestedSerializer(read_only=True)

    class Meta:
        model = RolePermissionMap
        fields = ["id", "permission", "created_at"]
