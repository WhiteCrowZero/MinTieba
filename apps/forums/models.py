from django.contrib.auth import get_user_model
from django.db import models

# 用户主模型
UserModel = get_user_model()

# ========== 枚举常量 ==========


class RoleChoices(models.TextChoices):
    """角色枚举"""

    OWNER = "owner", "吧主"
    ADMIN = "admin", "管理员"
    MEMBER = "member", "普通成员"


# ========== 吧相关模型 ==========


class Forum(models.Model):
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
    member_count = models.PositiveIntegerField(default=0, verbose_name="成员数量")
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


class ForumCategory(models.Model):
    """贴吧分类"""

    name = models.CharField(max_length=50, unique=True, verbose_name="分类名称")
    description = models.TextField(blank=True, null=True, verbose_name="描述")
    icon_url = models.URLField(blank=True, null=True, verbose_name="图标URL")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="排序")

    class Meta:
        db_table = "forum_category"
        verbose_name = "贴吧分类"
        verbose_name_plural = "贴吧分类列表"
        ordering = ["sort_order"]

    def __str__(self):
        return self.name


class ForumCategoryMap(models.Model):
    """贴吧与分类映射"""

    forum = models.ForeignKey(
        Forum, on_delete=models.CASCADE, related_name="categories", verbose_name="贴吧"
    )
    category = models.ForeignKey(
        ForumCategory,
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


class ForumRelation(models.Model):
    """贴吧关联表"""

    forum = models.ForeignKey(
        Forum, on_delete=models.CASCADE, related_name="relations", verbose_name="贴吧"
    )
    related = models.ForeignKey(
        Forum,
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


class ForumMember(models.Model):
    """吧成员表"""

    forum = models.ForeignKey(
        Forum, on_delete=models.CASCADE, related_name="members", verbose_name="贴吧"
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


class ForumActivity(models.Model):
    """吧内活跃度表"""

    forum = models.ForeignKey(
        Forum, on_delete=models.CASCADE, related_name="activities", verbose_name="贴吧"
    )
    forum_member = models.ForeignKey(
        ForumMember,
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
