import logging

from django.contrib.auth import get_user_model
from rest_framework import serializers

from common.utils.oss_utils import (
    BaseImageUploadSerializer,
)
from .models import (
    Forum,
    ForumCategory,
    ForumMember,
    RoleChoices,
    ForumMemberAuditLog,
    ActionType,
)


UserModel = get_user_model()
logger = logging.getLogger("feat")


class ForumCategorySerializer(serializers.ModelSerializer):
    """贴吧分类序列化器"""

    class Meta:
        model = ForumCategory
        fields = ["id", "name", "description", "icon_url", "sort_order"]
        read_only_fields = ["id", "icon_url"]


class ForumSerializer(serializers.ModelSerializer):
    """贴吧主信息序列化器"""

    creator_name = serializers.CharField(source="creator.username", read_only=True)
    category_names = serializers.SerializerMethodField()

    class Meta:
        model = Forum
        fields = [
            "id",
            "name",
            "description",
            "cover_image_url",
            "creator_name",
            "post_count",
            "member_count",
            "rules",
            "category_names",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "cover_image_url",
            "creator_name",
            "post_count",
            "member_count",
            "category_names",
            "created_at",
            "updated_at",
        ]

    def get_category_names(self, obj):
        """展示贴吧分类名"""
        return [c.category.name for c in obj.categories.all()]


class ForumCoverImageSerializer(BaseImageUploadSerializer):
    """贴吧封面图片序列化器"""

    file_field_name = "cover_image_file"
    url_field_name = "cover_image_url"
    oss_folder = "cover"

    class Meta(BaseImageUploadSerializer.Meta):
        model = Forum
        fields = []


class CategoryIconImageView(BaseImageUploadSerializer):
    """贴吧分类图标序列化器"""

    file_field_name = "icon_file"
    url_field_name = "icon_url"
    oss_folder = "category_icon"

    class Meta(BaseImageUploadSerializer.Meta):
        model = ForumCategory
        fields = []


class ForumMemberReadOnlySerializer(serializers.ModelSerializer):
    """贴吧成员信息查看序列化器（只读角色信息）"""

    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ForumMember
        fields = ["id", "user", "role_type", "joined_at", "is_banned"]
        read_only_fields = ["id", "user", "role_type", "joined_at", "is_banned"]
        extra_kwargs = {
            "user": {"source": "user.username"},
        }


class RoleUpdateSerializer(serializers.ModelSerializer):
    """
    用于更新成员角色的序列化器（含审计）
    """

    user_id = serializers.PrimaryKeyRelatedField(
        queryset=UserModel.objects.all(), write_only=True, required=True
    )
    role_type = serializers.ChoiceField(choices=RoleChoices.choices, required=True)

    class Meta:
        model = ForumMember
        fields = ["role_type", "user_id"]

    def validate(self, attrs):
        forum_pk = self.context["forum_pk"]
        user = attrs["user_id"]
        operator = self.context["request"].user
        forum = Forum.objects.filter(pk=forum_pk).first()
        if not forum:
            raise serializers.ValidationError("该吧不存在")

        # 权限检查
        operator = ForumMember.objects.filter(
            forum=forum,
            user=operator,
            role_type__in=[RoleChoices.OWNER, RoleChoices.ADMIN],
        ).first()
        if not operator:
            raise serializers.ValidationError("你没有权限修改成员角色")

        if (
            operator.role_type != RoleChoices.OWNER
            and attrs["role_type"] == RoleChoices.OWNER
        ):
            raise serializers.ValidationError("仅吧主能够修改成员角色为吧主")

        # 找目标成员
        member = ForumMember.objects.filter(forum=forum, user=user).first()
        if not member:
            raise serializers.ValidationError("该用户不是本吧成员")

        attrs["forum"] = forum
        attrs["member"] = member
        return attrs

    def save(self, **kwargs):
        member = self.validated_data["member"]
        operator = self.context["request"].user
        new_role = self.validated_data["role_type"]
        old_role = member.role_type

        if old_role == new_role:
            raise serializers.ValidationError("角色未发生变化")

        # 更新
        member.role_type = new_role
        member.save(update_fields=["role_type"])

        # 审计记录
        ForumMemberAuditLog.objects.create(
            forum=member.forum,
            operator=operator,
            target_user=member.user,
            action=ActionType.CHANGE_ROLE,
            old_role=old_role,
            new_role=new_role,
        )

        return member


class BanMemberSerializer(serializers.ModelSerializer):
    """
    用于封禁成员的序列化器（含审计）
    """

    user_id = serializers.PrimaryKeyRelatedField(
        queryset=UserModel.objects.all(), write_only=True, required=True
    )
    action = serializers.ChoiceField(
        choices=[ActionType.BAN_MEMBER, ActionType.UNBAN_MEMBER], required=True
    )

    class Meta:
        model = ForumMember
        fields = ["user_id", "action"]

    def validate(self, attrs):
        forum_pk = self.context["forum_pk"]
        user = attrs["user_id"]
        forum = Forum.objects.filter(pk=forum_pk).first()
        if not forum:
            raise serializers.ValidationError("该吧不存在")

        member = ForumMember.objects.filter(forum=forum, user=user).first()
        if not member:
            raise serializers.ValidationError("该用户不是本吧成员")

        # 权限检查
        operator = self.context["request"].user
        if member.role_type != RoleChoices.MEMBER:
            raise serializers.ValidationError("该用户不是普通成员，无法被封禁")
        operator = ForumMember.objects.filter(
            forum=forum,
            user=operator,
            role_type__in=[RoleChoices.OWNER, RoleChoices.ADMIN],
        ).first()
        if not operator or operator.is_banned:
            raise serializers.ValidationError("你没有权限封禁成员角色")

        attrs["forum"] = forum
        attrs["member"] = member
        return attrs

    def save(self, **kwargs):
        member = self.validated_data["member"]
        operator = self.context["request"].user
        action = self.validated_data["action"]

        # 根据 action 选择封禁或者解封
        if action == ActionType.BAN_MEMBER:
            if member.is_banned:
                raise serializers.ValidationError("该成员已被封禁")
            member.is_banned = True
        elif action == ActionType.UNBAN_MEMBER:
            if not member.is_banned:
                raise serializers.ValidationError("该成员未被封禁")
            member.is_banned = False

        member.save(update_fields=["is_banned"])

        # 审计记录
        ForumMemberAuditLog.objects.create(
            forum=member.forum,
            operator=operator,
            target_user=member.user,
            action=action,
            old_role=member.role_type,
            new_role=member.role_type,
        )

        return member
