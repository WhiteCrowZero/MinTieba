from rest_framework.generics import UpdateAPIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny

from common.permissions import IsForumAdmin, RBACPermission
from .models import Forum, ForumCategory, ForumMember, RoleChoices
from .serializers import (
    ForumSerializer,
    ForumCategorySerializer,
    ForumCoverImageSerializer,
)


# 贴吧管理视图
class ForumViewSet(ModelViewSet):
    """
    贴吧管理接口：
      - 创建贴吧（登录用户）
      - 获取贴吧列表（匿名可访问）
      - 获取贴吧详情（匿名可访问）
      - 更新贴吧信息（吧主/管理员）
      - 删除贴吧（吧主/管理员）
    """

    queryset = Forum.objects.all().select_related("creator")
    serializer_class = ForumSerializer

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy", "modify_rules"):
            # 需要贴吧管理员权限
            return [IsForumAdmin()]
        elif self.action == "create":
            # 创建贴吧需要登录
            return [IsAuthenticated()]
        # 其他 GET 请求放行
        return [AllowAny()]

    def perform_create(self, serializer):
        forum = serializer.save(creator=self.request.user)
        # 创建贴吧的用户自动成为吧主
        ForumMember.objects.get_or_create(
            forum=forum,
            user=self.request.user,
            defaults={"role_type": RoleChoices.OWNER},
        )

    def get_queryset(self):
        """支持搜索和分类过滤"""
        queryset = self.queryset
        name = self.request.query_params.get("search")
        category = self.request.query_params.get("category")
        if name:
            queryset = queryset.filter(name__icontains=name)
        if category:
            queryset = queryset.filter(categories__category__id=category)
        return queryset


# 吧分类管理视图
class ForumCategoryViewSet(ModelViewSet):
    """
    吧分类管理接口：
      - 获取分类列表（匿名可访问）
      - 创建分类（系统管理员）
      - 删除分类（系统管理员）
    """

    queryset = ForumCategory.objects.all()
    serializer_class = ForumCategorySerializer
    action_permissions = {
        "create": "forums.create_category",
        "update": "forums.edit_category",
        "partial_update": "forums.edit_category",
        "destroy": "forums.delete_category",
    }

    def get_permissions(self):
        if self.action == "list":
            return [AllowAny()]
        return [IsAuthenticated(), RBACPermission()]


class ForumCoverImageView(UpdateAPIView):
    """贴吧封面图修改接口"""

    serializer_class = ForumCoverImageSerializer
    permission_classes = [IsAuthenticated, IsForumAdmin]

    def get_object(self):
        return Forum.objects.get(id=self.kwargs.get("pk"))


class CategoryIconImageView(UpdateAPIView):
    """吧分类图标修改接口"""

    serializer_class = ForumCoverImageSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    permission_code = "forums.edit_category"

    def get_object(self):
        return ForumCategory.objects.get(id=self.kwargs.get("pk"))
