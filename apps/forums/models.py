from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from common.delete import SoftDeleteModel

# 用户主模型
UserModel = get_user_model()

# ========== 枚举常量 ==========


class RoleChoices(models.TextChoices):
    """角色枚举"""

    OWNER = "owner", "吧主"
    ADMIN = "admin", "管理员"
    MEMBER = "member", "普通成员"


class ActionType(models.TextChoices):
    CHANGE_ROLE = "change_role", "角色变更"
    BAN_MEMBER = "ban", "封禁成员"
    UNBAN_MEMBER = "unban", "解封成员"

class ForumRelationRequestStatus(models.TextChoices):
    PENDING = "pending", "待审核"
    APPROVED = "approved", "已批准"
    REJECTED = "rejected", "已拒绝"

class ForumRelationType(models.TextChoices):
    BIND = "bind", "绑定"
    UNBIND = "unbind", "解绑"

# ========== 吧相关模型 ==========


class Forum(SoftDeleteModel):
    """贴吧主信息表"""

    name = models.CharField(max_length=100, unique=True, verbose_name="吧名称")
    description = models.TextField(blank=True, null=True, verbose_name="简介")
    cover_image_url = models.URLField(blank=True, null=True, verbose_name="封面图片URL")
    creator = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="created_forums",
        verbose_name="创建者",
    )
    post_count = models.PositiveIntegerField(default=0, verbose_name="帖子数量")
    member_count = models.PositiveIntegerField(default=1, verbose_name="成员数量")
    rules = models.TextField(blank=True, null=True, verbose_name="吧规")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "forum"
        verbose_name = "贴吧"
        verbose_name_plural = "贴吧列表"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def delete(self, using=None, keep_parents=False):
        """软删除贴吧及所有关联对象"""
        # 先软删除关联关系
        self.categories.all().update(is_deleted=True, deleted_at=timezone.now())
        self.relations.all().update(is_deleted=True, deleted_at=timezone.now())
        self.members.all().update(is_deleted=True, deleted_at=timezone.now())
        self.activities.all().update(is_deleted=True, deleted_at=timezone.now())
        super().delete(using, keep_parents)


class ForumCategory(SoftDeleteModel):
    """贴吧分类"""

    name = models.CharField(max_length=50, unique=True, verbose_name="分类名称")
    description = models.TextField(blank=True, null=True, verbose_name="描述")
    icon_url = models.URLField(blank=True, null=True, verbose_name="图标URL")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="排序")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "forum_category"
        verbose_name = "贴吧分类"
        verbose_name_plural = "贴吧分类列表"
        ordering = ["sort_order"]

    def __str__(self):
        return self.name

    def delete(self, using=None, keep_parents=False):
        """软删除分类及其映射"""
        self.forums.all().update(is_deleted=True, deleted_at=timezone.now())
        super().delete(using, keep_parents)


class ForumCategoryMap(SoftDeleteModel):
    """贴吧与分类映射"""

    forum = models.ForeignKey(
        "forums.Forum",
        on_delete=models.CASCADE,
        related_name="categories",
        verbose_name="贴吧",
    )
    category = models.ForeignKey(
        "forums.ForumCategory",
        on_delete=models.CASCADE,
        related_name="forums",
        verbose_name="分类",
    )

    class Meta:
        db_table = "forum_category_map"
        verbose_name = "贴吧分类映射"
        verbose_name_plural = "贴吧分类映射列表"
        unique_together = ("forum", "category")

    def __str__(self):
        return f"{self.forum.name} - {self.category.name}"


class ForumRelation(SoftDeleteModel):
    """贴吧关联表"""

    forum = models.ForeignKey(
        "forums.Forum",
        on_delete=models.CASCADE,
        related_name="relations",
        verbose_name="贴吧",
    )
    related = models.ForeignKey(
        "forums.Forum",
        on_delete=models.CASCADE,
        related_name="related_to",
        verbose_name="关联贴吧",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "forum_relation"
        verbose_name = "贴吧关联"
        verbose_name_plural = "贴吧关联列表"
        unique_together = ("forum", "related")

    def __str__(self):
        return f"{self.forum.name} ↔ {self.related.name}"


# class ForumRelationRequest(models.Model):
#     from_forum = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name="relation_requests_sent")
#     to_forum = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name="relation_requests_received")
#     relation_type = models.CharField(
#         max_length=20,
#         choices=ForumRelationType.choices,
#         default=ForumRelationType.BIND,
#     )
#
#     status = models.CharField(
#         max_length=20,
#         choices=ForumRelationRequestStatus.choices,
#         default=ForumRelationRequestStatus.PENDING,
#     )
#
#     created_at = models.DateTimeField(auto_now_add=True)
#     acted_at = models.DateTimeField(null=True, blank=True)
#
#     class Meta:
#         unique_together = ("from_forum", "to_forum")


class ForumMember(SoftDeleteModel):
    """吧成员表"""

    forum = models.ForeignKey(
        "forums.Forum",
        on_delete=models.CASCADE,
        related_name="members",
        verbose_name="贴吧",
    )
    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="forum_memberships",
        verbose_name="用户",
    )
    role_type = models.CharField(
        max_length=10,
        choices=RoleChoices.choices,
        default=RoleChoices.MEMBER,
        verbose_name="成员角色",
    )
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="加入时间")
    is_banned = models.BooleanField(default=False, verbose_name="是否被封禁")

    class Meta:
        db_table = "forum_member"
        verbose_name = "贴吧成员"
        verbose_name_plural = "贴吧成员列表"
        unique_together = ("forum", "user")

    def __str__(self):
        return f"{self.user.username} in {self.forum.name}"


class ForumMemberAuditLog(models.Model):
    """
    贴吧成员权限或状态变更审计日志
    """

    forum = models.ForeignKey(
        "forums.Forum",
        on_delete=models.CASCADE,
        related_name="audit_logs",
        verbose_name="所属贴吧",
    )
    operator = models.ForeignKey(
        UserModel,
        on_delete=models.SET_NULL,
        null=True,
        related_name="performed_audit_logs",
        verbose_name="操作人",
    )
    target_user = models.ForeignKey(
        UserModel,
        on_delete=models.SET_NULL,
        null=True,
        related_name="target_audit_logs",
        verbose_name="被操作成员",
    )
    action = models.CharField(max_length=32, choices=ActionType.choices)
    old_role = models.CharField(max_length=20, blank=True, null=True)
    new_role = models.CharField(max_length=20, blank=True, null=True)
    old_banned = models.BooleanField(null=True, blank=True)
    new_banned = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "forum_member_audit_log"
        verbose_name = "成员权限变更日志"
        verbose_name_plural = "成员权限变更日志"

    def __str__(self):
        return f"[{self.forum.name}] {self.operator} {self.action} {self.target_user}"


class ForumActivity(SoftDeleteModel):
    """吧内活跃度表"""

    forum = models.ForeignKey(
        "forums.Forum",
        on_delete=models.CASCADE,
        related_name="activities",
        verbose_name="贴吧",
    )
    forum_member = models.ForeignKey(
        "forums.ForumMember",
        on_delete=models.CASCADE,
        related_name="forum_activities",
        verbose_name="吧成员",
    )
    exp_points = models.PositiveIntegerField(default=0, verbose_name="经验值")
    level = models.PositiveIntegerField(default=1, verbose_name="等级")
    last_active_at = models.DateTimeField(auto_now=True, verbose_name="最后活跃时间")
    sign_in_streak = models.PositiveIntegerField(default=0, verbose_name="签到连天数")

    class Meta:
        db_table = "forum_activity"
        verbose_name = "贴吧活跃度"
        verbose_name_plural = "贴吧活跃度列表"
        unique_together = ("forum", "forum_member")

    @property
    def user(self):
        return self.forum_member.user

    def __str__(self):
        return f"{self.user.username} @ {self.forum.name}"
