from django.contrib.auth.models import AbstractUser
from django.db import models


# ========== RBAC 权限相关表 ==========


class Role(models.Model):
    """角色表"""

    name = models.CharField(max_length=50, unique=True, verbose_name="角色名称")
    description = models.TextField(blank=True, null=True, verbose_name="角色描述")
    # 用于表明角色权限的高低，数值越高，权限越高
    level = models.PositiveIntegerField(default=1, verbose_name="角色等级")

    class Meta:
        db_table = "role"
        verbose_name = "角色"
        verbose_name_plural = "角色列表"
        ordering = ["level"]

    def __str__(self):
        return self.name


class Permission(models.Model):
    """权限表"""

    code = models.CharField(max_length=100, unique=True, verbose_name="权限编码")
    name = models.CharField(max_length=100, verbose_name="权限名称")
    description = models.TextField(blank=True, null=True, verbose_name="权限描述")
    category = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="权限分类"
    )

    class Meta:
        db_table = "permission"
        verbose_name = "权限"
        verbose_name_plural = "权限列表"
        ordering = ["category", "id"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class RolePermissionMap(models.Model):
    """角色-权限映射表"""

    role = models.ForeignKey(
        Role, on_delete=models.PROTECT, related_name="permissions", verbose_name="角色"
    )
    permission = models.ForeignKey(
        Permission, on_delete=models.PROTECT, related_name="roles", verbose_name="权限"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "role_permission_map"
        verbose_name = "角色权限映射"
        verbose_name_plural = "角色权限映射列表"
        unique_together = ("role", "permission")

    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"


# ========== 枚举常量 ==========


class GenderChoices(models.TextChoices):
    """性别枚举"""

    MALE = "male", "男"
    FEMALE = "female", "女"
    OTHER = "other", "其他"


class VisibilityChoices(models.TextChoices):
    """隐私设置枚举"""

    PUBLIC = "public", "公开"
    FRIENDS = "friends", "仅好友"
    PRIVATE = "private", "私密"


# ========== 用户主信息表 ==========


class UserAccount(AbstractUser):
    """用户主信息表"""

    username = models.CharField(max_length=150, unique=True, verbose_name="用户名")
    password = models.CharField(max_length=128, verbose_name="密码")
    email = models.EmailField(unique=True, verbose_name="邮箱")
    mobile = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="手机号"
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        related_name="users",
        verbose_name="角色",
    )
    avatar_url = models.URLField(blank=True, null=True, verbose_name="头像URL")
    bio = models.TextField(blank=True, null=True, verbose_name="个人简介")
    gender = models.CharField(
        max_length=10,
        choices=GenderChoices.choices,
        default=GenderChoices.OTHER,
        verbose_name="性别",
    )
    # 用户是否激活（业务逻辑用，系统的 is_activate 保留，用作系统逻辑）
    is_active_account = models.BooleanField(default=False, verbose_name="是否激活")
    is_banned = models.BooleanField(default=False, verbose_name="是否封禁")
    is_deleted = models.BooleanField(default=False, verbose_name="是否注销")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "user_account"
        verbose_name = "用户账户"
        verbose_name_plural = "用户账户列表"
        ordering = ["-created_at"]

    def __str__(self):
        return self.username


# ========== 用户扩展信息表 ==========


class UserProfile(models.Model):
    """用户扩展信息表"""

    user = models.OneToOneField(
        UserAccount,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="用户",
    )
    birthday = models.DateField(blank=True, null=True, verbose_name="生日")
    location = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="所在地"
    )
    signature = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="个性签名"
    )
    exp_points = models.IntegerField(default=0, verbose_name="经验值")
    level = models.PositiveIntegerField(default=1, verbose_name="等级")
    last_login_ip = models.GenericIPAddressField(
        blank=True, null=True, verbose_name="最后登录IP"
    )
    privacy_settings = models.CharField(
        max_length=50,
        choices=VisibilityChoices.choices,
        default=VisibilityChoices.FRIENDS,
        verbose_name="隐私设置",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "user_profile"
        verbose_name = "用户扩展信息"
        verbose_name_plural = "用户扩展信息列表"

    def __str__(self):
        return f"Profile of {self.user.username}"


# ========== 用户登录记录表 ==========


class UserLoginHistory(models.Model):
    """用户登录历史表"""

    user = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE,
        related_name="login_history",
        verbose_name="用户",
    )
    login_ip = models.GenericIPAddressField(verbose_name="登录IP")
    device_info = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="设备信息"
    )
    login_time = models.DateTimeField(auto_now_add=True, verbose_name="登录时间")

    class Meta:
        db_table = "user_login_history"
        verbose_name = "用户登录历史"
        verbose_name_plural = "用户登录历史列表"
        ordering = ["-login_time"]

    def __str__(self):
        return f"{self.user.username} - {self.login_ip} ({self.login_time})"
