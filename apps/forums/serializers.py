import logging

from rest_framework import serializers

from common.utils.oss_utils import (
    BaseImageUploadSerializer,
)
from .models import Forum, ForumCategory

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
