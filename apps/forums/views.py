import logging
import time

from django.db import transaction
from django.db.models import F
from django.http import Http404
from django.utils import timezone
from django.utils.timezone import localdate
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
from .models import (
    Forum,
    ForumCategory,
    ForumMember,
    RoleChoices,
    ForumRelation,
    ForumActivity,
)
from .serializers import (
    ForumSerializer,
    ForumCategorySerializer,
    ForumCoverImageSerializer,
    ForumMemberReadOnlySerializer,
    RoleUpdateSerializer,
    BanMemberSerializer,
    ForumRelationSerializer,
    RelationDeleteInputSerializer,
    ForumActivitySerializer,
    ForumSignInInputSerializer,
)

logger = logging.getLogger("feat")


# 贴吧管理视图
class ForumViewSet(ModelViewSet):
    """
    贴吧管理接口：
      - 创建贴吧（登录用户）
      - 加入/退出贴吧（登录用户/吧成员）
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

    # @action(detail=False, methods=["post"], url_path="toggle")
    # def join_toggle(self, request, forum_pk=None):
    #     forum = get_object_or_404(Forum, pk=forum_pk)
    #     user = request.user
    #
    #     redis = get_redis_connection("default")
    #     lock_key = f"forum:membership:{forum.id}:{user.id}"
    #     lock_value = str(time.time())
    #
    #     # 使用 SETNX 实现分布式锁
    #     lock_acquired = redis.set(lock_key, lock_value, nx=True, ex=5)
    #     if not lock_acquired:
    #         return Response(
    #             {"detail": "操作过于频繁，请稍后再试"},
    #             status=status.HTTP_429_TOO_MANY_REQUESTS,
    #         )
    #
    #     # 异步触发任务
    #     toggle_forum_membership_task.delay(forum.id, user.id)
    #
    #     return Response(
    #         {"detail": "操作已提交，后台处理中"},
    #         status=status.HTTP_202_ACCEPTED,
    #     )

    @action(detail=True, methods=["post"], url_path="toggle")
    def join_toggle(self, request, pk=None):
        user = request.user
        with transaction.atomic():
            # 锁住论坛行，确保 member_count 的加减是原子且串行的
            forum = (
                Forum.objects.select_for_update().only("id", "member_count").get(pk=pk)
            )

            # 查找包含软删除的记录；必要时也可以 .select_for_update() 锁住这一行
            member = ForumMember.all_objects.filter(
                forum=forum, user_id=user.id
            ).first()

            if not member:
                # 新加入
                ForumMember.objects.create(
                    forum=forum,
                    user_id=user.id,
                    role_type=RoleChoices.MEMBER,
                )
                Forum.objects.filter(pk=forum.pk).update(
                    member_count=F("member_count") + 1
                )
                action = "joined"

            elif member.is_deleted:
                # 恢复加入
                member.is_deleted = False
                member.deleted_at = None
                member.joined_at = timezone.now()
                member.save(update_fields=["is_deleted", "deleted_at", "joined_at"])
                Forum.objects.filter(pk=forum.pk).update(
                    member_count=F("member_count") + 1
                )
                action = "rejoined"

            else:
                # 退出（软删除）
                member.is_deleted = True
                member.deleted_at = timezone.now()
                member.save(update_fields=["is_deleted", "deleted_at"])
                Forum.objects.filter(pk=forum.pk).update(
                    member_count=F("member_count") - 1
                )
                action = "left"

            # 读回最新计数（F() 只在数据库里生效，reload 一下内存值）
            forum.refresh_from_db(fields=["member_count"])

        return Response(
            {
                "status": "success",
                "action": action,
                "forum": forum.id,
                "member_count": forum.member_count,
            },
            status=status.HTTP_200_OK,
        )


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


class ForumActivityViewSet(GenericViewSet):
    """贴吧活跃度管理"""

    queryset = ForumActivity.objects.all()
    serializer_class = ForumActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "sign_in":
            return ForumSignInInputSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=["get"], url_path="recent")
    def rank_ten(self, request, *args, **kwargs):
        forum_id = request.query_params.get("forum")
        if not forum_id:
            return Response(
                {"detail": "缺少 forum 参数"}, status=status.HTTP_400_BAD_REQUEST
            )

        queryset = (
            self.get_queryset()
            .filter(forum__pk=forum_id)
            .order_by("-last_active_at")[:10]
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="myactivity")
    def my_activity(self, request, *args, **kwargs):
        forum_id = request.query_params.get("forum")
        if not forum_id:
            return Response(
                {"detail": "缺少 forum 参数"}, status=status.HTTP_400_BAD_REQUEST
            )

        instance = (
            self.get_queryset()
            .select_related("forum", "forum_member", "forum_member__user")
            .filter(
                forum__pk=forum_id,
                forum_member__user=request.user,
            )
            .first()
        )
        if not instance:
            return Response(
                {"detail": "未找到该吧的个人活跃记录"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="signin")
    def sign_in(self, request, *args, **kwargs):
        in_ser = self.get_serializer(data=request.data)
        in_ser.is_valid(raise_exception=True)
        forum = in_ser.validated_data["forum"]
        member = in_ser.validated_data["forum_member"]

        today = localdate()

        with transaction.atomic():
            # 行级锁，避免并发重复签到
            activity, created = ForumActivity.objects.select_for_update().get_or_create(
                forum=forum,
                forum_member=member,
            )

            # 已经签过今天
            if activity.last_active_at == today and not created:
                out = ForumActivitySerializer(activity).data
                return Response(
                    {"detail": "今日已签到", "activity": out}, status=status.HTTP_200_OK
                )

            # 计算连续天数
            if activity.last_active_at is None:
                new_streak = 1
            else:
                delta_days = (today - activity.last_active_at).days
                if delta_days == 1:
                    new_streak = activity.sign_in_streak + 1
                else:
                    new_streak = 1

            # 经验与等级规则
            gained_exp = max(30, 10 + max(0, new_streak - 1))  # 连续越久奖励越多
            activity.exp_points = F("exp_points") + gained_exp
            activity.sign_in_streak = new_streak
            activity.last_active_at = today
            activity.save(
                update_fields=["exp_points", "sign_in_streak", "last_active_at"]
            )

        # 重新读出 F() 更新后的值
        activity.refresh_from_db()
        # 简单的升级规则
        activity.level = 1 + activity.exp_points // 100
        activity.save(update_fields=["level"])

        return Response(
            {
                "detail": "签到成功",
                "gained_exp": gained_exp,
                "activity": ForumActivitySerializer(activity).data,
            },
            status=status.HTTP_200_OK,
        )
