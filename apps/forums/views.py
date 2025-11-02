import logging
import time

from django.http import Http404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from django_redis import get_redis_connection
from rest_framework import status, filters, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.generics import UpdateAPIView, get_object_or_404
from rest_framework.viewsets import ModelViewSet, GenericViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from common.permissions import IsForumAdmin, RBACPermission
from .tasks import toggle_forum_membership_task
from .models import Forum, ForumCategory, ForumMember, RoleChoices, ForumRelation
from .serializers import (
    ForumSerializer,
    ForumCategorySerializer,
    ForumCoverImageSerializer,
    ForumMemberReadOnlySerializer,
    RoleUpdateSerializer,
    BanMemberSerializer,
    ForumRelationSerializer,
    RelationDeleteInputSerializer,
)

logger = logging.getLogger("feat")


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
    lookup_value_regex = r"\d+"  # 只有纯数字才当成 pk

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy", "modify_rules"):
            # 需要贴吧管理员权限
            return [IsForumAdmin()]
        elif self.action == "create":
            # 创建贴吧需要登录
            return [IsAuthenticated()]
        # 其他 GET 请求放行
        return [AllowAny()]

    def create(self, request, *args, **kwargs):
        forum_name = request.data.get("name")

        # 检查是否有已软删除的论坛，且当前用户为创建者
        existing_forum = Forum.all_objects.filter(name=forum_name).first()
        if existing_forum:
            if existing_forum.creator == request.user and existing_forum.is_deleted:
                existing_forum.is_deleted = False
                existing_forum.deleted_at = None
                existing_forum.save(update_fields=["is_deleted", "deleted_at"])
                logger.info(
                    f"{request.user} 于 {time.strftime('%Y-%m-%d %H:%M:%S')} 恢复论坛 {existing_forum.name}"
                )
                return Response(
                    {"message": "恢复软删除的论坛"}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": "该贴吧名称已被占用"}, status=status.HTTP_400_BAD_REQUEST
                )

        # 没有被软删除且没有同名未删除论坛，继续创建
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        forum = serializer.save(creator=request.user)

        ForumMember.objects.create(
            forum=forum,
            user=request.user,
            role_type=RoleChoices.OWNER,
        )

        logger.info(
            f"{request.user} 于 {time.strftime('%Y-%m-%d %H:%M:%S')} 创建论坛 {forum.name}"
        )
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def get_queryset(self):
        """支持搜索和分类过滤"""
        queryset = self.queryset.filter(is_deleted=False)
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


class ForumMemberReadOnlyViewSet(ReadOnlyModelViewSet):
    """
    贴吧成员只读接口：
      - 获取吧成员列表（匿名可访问）
        - GET /forums/{forum_pk}/members/read/   （列表）
      - 获取吧成员详情（匿名可访问）
        - GET /forums/{forum_pk}/members/read/{user_id}/         （详情）
    """

    serializer_class = ForumMemberReadOnlySerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["forum"]
    search_fields = ["user__username"]

    def get_queryset(self):
        forum_pk = self.kwargs.get("forum_pk")
        return ForumMember.objects.select_related("user", "forum").filter(
            forum__pk=forum_pk, forum__is_deleted=False
        )

    def get_object(self):
        obj = super().get_object()
        if obj.forum.is_deleted:
            raise Http404("该贴吧已被删除")
        return obj


class ForumMemberViewSet(GenericViewSet):
    """
    贴吧成员接口：加入 / 退出贴吧（异步 + 分布式锁）
        - POST /forums/{forum_pk}/members/membership/toggle/  -> 切换 (join/leave)
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="toggle")
    def join_toggle(self, request, forum_pk=None):
        forum = get_object_or_404(Forum, pk=forum_pk)
        user = request.user

        redis = get_redis_connection("default")
        lock_key = f"forum:membership:{forum.id}:{user.id}"
        lock_value = str(time.time())

        # 使用 SETNX 实现分布式锁
        lock_acquired = redis.set(lock_key, lock_value, nx=True, ex=5)
        if not lock_acquired:
            return Response(
                {"detail": "操作过于频繁，请稍后再试"},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # 异步触发任务
        toggle_forum_membership_task.delay(forum.id, user.id)

        return Response(
            {"detail": "操作已提交，后台处理中"},
            status=status.HTTP_202_ACCEPTED,
        )


class ForumMemberRoleViewSet(GenericViewSet):
    """
    管理成员角色与封禁（只有吧主/管理员）
    """

    queryset = ForumMember.objects.select_related("user", "forum")
    permission_classes = [IsForumAdmin]

    @action(detail=False, methods=["post"], url_path="change")
    def update_role(self, request, forum_pk=None):
        user_id = request.data.get("user_id")
        if not user_id:
            return Response(
                {"detail": "请提供用户ID"}, status=status.HTTP_400_BAD_REQUEST
            )

        # 使用 RoleUpdateSerializer 来处理角色更新
        serializer = RoleUpdateSerializer(
            data=request.data, context={"forum_pk": forum_pk, "request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "detail": f"{serializer.validated_data['member'].user.username} 的角色已更新"
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], url_path="ban")
    def ban_member(self, request, forum_pk=None):
        serializer = BanMemberSerializer(
            data=request.data,
            context={"request": request, "forum_pk": forum_pk},
        )
        serializer.is_valid(raise_exception=True)
        member = serializer.save()

        return Response(
            {"detail": f"{member.user.username} 封禁状态已修改"},
            status=status.HTTP_200_OK,
        )


class ForumRelationViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    """贴吧关联关系管理接口"""

    queryset = ForumRelation.objects.select_related("forum")
    serializer_class = ForumRelationSerializer
    lookup_value_regex = r"\d+"  # 只有纯数字才当成 pk

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsForumAdmin()]
        return [IsAuthenticated()]

    def retrieve(self, request, *args, **kwargs):
        related_forums = ForumRelation.objects.filter(forum__pk=kwargs.get("pk"))
        serializer = self.get_serializer(related_forums, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="delete")
    def delete(self, request, *args, **kwargs):
        serializer = RelationDeleteInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        relationship = ForumRelation.objects.filter(
            forum=data["forum"], related=data["related"]
        )
        if not relationship.exists():
            return Response(
                {"detail": "未找到指定的关联关系"}, status=status.HTTP_404_NOT_FOUND
            )
        relationship.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
