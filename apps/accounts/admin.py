from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import (
    Role,
    Permission,
    RolePermissionMap,
    UserAccount,
    UserProfile,
    UserLoginHistory,
)


# ========== RBAC 部分 ==========


class PermissionInline(admin.TabularInline):
    """权限内联显示"""

    model = Permission
    extra = 0
    fields = ("code", "name", "type")
    readonly_fields = ("code", "name", "type")
    can_delete = False
    max_num = 0


class RolePermissionMapInline(admin.TabularInline):
    """在角色页面中显示角色-权限映射"""

    model = RolePermissionMap
    extra = 1
    autocomplete_fields = ["permission"]
    readonly_fields = ["created_at"]
    classes = ["collapse"]  # 默认折叠


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """角色管理优化版"""

    list_display = (
        "id",
        "name",
        "level",
        "user_count",
        "permission_count",
        "description",
    )
    list_display_links = ("id", "name")
    search_fields = ("name", "description")
    list_filter = ("level",)
    ordering = ("-level", "name")
    inlines = [RolePermissionMapInline]
    list_per_page = 20
    actions = ["duplicate_role"]

    fieldsets = (("基本信息", {"fields": ("name", "level", "description")}),)

    def user_count(self, obj):
        return obj.users.count()

    user_count.short_description = "用户数"

    def permission_count(self, obj):
        return obj.permissions.count()

    permission_count.short_description = "权限数"

    def duplicate_role(self, request, queryset):
        """复制角色动作"""
        for role in queryset:
            new_role = Role.objects.create(
                name=f"{role.name}_复制", description=role.description, level=role.level
            )
            # 复制权限
            for rp in role.permissions.all():
                RolePermissionMap.objects.create(
                    role=new_role, permission=rp.permission
                )
            self.message_user(request, f"角色 {role.name} 已复制")

    duplicate_role.short_description = "复制选中角色"


class PermissionChildrenInline(admin.TabularInline):
    """权限子项内联"""

    model = Permission
    fk_name = "parent"
    extra = 0
    fields = ("code", "name", "type")
    readonly_fields = ("code", "name", "type")
    can_delete = False


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """权限管理优化版"""

    list_display = ("id", "code", "name", "type", "parent", "role_count")
    list_display_links = ("id", "code", "name")
    search_fields = ("code", "name", "description")
    list_filter = ("type",)
    ordering = ("id", "name")
    list_per_page = 25
    inlines = [PermissionChildrenInline]

    fieldsets = (
        ("基本信息", {"fields": ("code", "name", "type", "description")}),
        ("层级关系", {"fields": ("parent",), "classes": ("collapse",)}),
    )

    def role_count(self, obj):
        return obj.roles.count()

    role_count.short_description = "角色数"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("parent")


@admin.register(RolePermissionMap)
class RolePermissionMapAdmin(admin.ModelAdmin):
    """角色权限映射管理优化版"""

    list_display = (
        "id",
        "role",
        "permission",
        "permission_type",
        "created_at",
    )
    list_display_links = ("id",)
    search_fields = ("role__name", "permission__name", "permission__code")
    list_filter = ("role", "permission__type")
    readonly_fields = ("created_at",)
    list_per_page = 30
    autocomplete_fields = ["role", "permission"]

    def permission_type(self, obj):
        return obj.permission.get_type_display()

    permission_type.short_description = "权限类型"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("role", "permission")


# ========== 用户信息部分 ==========


class UserProfileInline(admin.StackedInline):
    """在用户账户详情中显示扩展信息"""

    model = UserProfile
    extra = 0
    can_delete = False
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("个人信息", {"fields": ("birthday", "location", "signature")}),
        ("等级系统", {"fields": ("exp_points", "level"), "classes": ("collapse",)}),
        (
            "隐私设置",
            {"fields": ("privacy_settings", "last_login_ip"), "classes": ("collapse",)},
        ),
        (
            "时间信息",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


class UserLoginHistoryInline(admin.TabularInline):
    """在用户详情中显示最近登录记录"""

    model = UserLoginHistory
    extra = 0
    readonly_fields = ("login_ip", "device_info", "login_time")
    can_delete = False
    ordering = ("-login_time",)
    max_num = 10  # 只显示最近10条记录
    classes = ["collapse"]  # 默认折叠

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(UserAccount)
class UserAccountAdmin(BaseUserAdmin):
    """用户主要信息管理优化版"""

    list_display = (
        "id",
        "username",
        "email",
        "mobile",
        "role",
        "status_display",
        "created_at",
        "last_login",
    )
    list_display_links = ("id", "username")
    search_fields = ("username", "email", "mobile", "first_name", "last_name")
    list_filter = (
        "is_active",
        "is_deleted",
        "is_active_account",
        "is_banned",
        "role",
        "gender",
        "created_at",
    )
    readonly_fields = ("created_at", "updated_at", "last_login")
    inlines = [UserProfileInline, UserLoginHistoryInline]
    list_per_page = 25
    actions = ["activate_users", "deactivate_users", "ban_users", "unban_users"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("个人信息"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "mobile",
                    "avatar_url",
                    "bio",
                    "gender",
                )
            },
        ),
        (
            _("权限信息"),
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            _("状态信息"),
            {"fields": ("is_active_account", "is_banned", "is_deleted", "deleted_at")},
        ),
        (
            _("重要日期"),
            {
                "fields": ("last_login", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )

    def status_display(self, obj):
        """状态显示"""
        status = []
        if obj.is_active:
            status.append("✅激活")
        else:
            status.append("❌未激活")

        if obj.is_active_account:
            status.append("✅业务激活")
        else:
            status.append("❌业务未激活")

        if obj.is_banned:
            status.append("🚫封禁")

        if obj.is_deleted:
            status.append("🗑️注销")

        return " | ".join(status)

    status_display.short_description = "账户状态"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("role", "profile")

    def activate_users(self, request, queryset):
        """批量激活用户"""
        updated = queryset.update(is_active=True, is_active_account=True)
        self.message_user(request, f"成功激活 {updated} 个用户")

    activate_users.short_description = "激活选中用户"

    def deactivate_users(self, request, queryset):
        """批量停用用户"""
        updated = queryset.update(is_active=False, is_active_account=False)
        self.message_user(request, f"成功停用 {updated} 个用户")

    deactivate_users.short_description = "停用选中用户"

    def ban_users(self, request, queryset):
        """批量封禁用户"""
        updated = queryset.update(is_banned=True)
        self.message_user(request, f"成功封禁 {updated} 个用户")

    ban_users.short_description = "封禁选中用户"

    def unban_users(self, request, queryset):
        """批量解封用户"""
        updated = queryset.update(is_banned=False)
        self.message_user(request, f"成功解封 {updated} 个用户")

    unban_users.short_description = "解封选中用户"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """用户补充信息管理优化版"""

    list_display = (
        "id",
        "user__id",
        "level",
        "last_login_ip",
        "privacy_settings",
        "updated_at",
    )

    list_display_links = ("id", "user__id")
    search_fields = ("user__username", "user__email", "location", "signature")
    list_filter = ("level", "privacy_settings", "created_at")
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 25
    autocomplete_fields = ["user"]

    fieldsets = (
        ("基础信息", {"fields": ("user", "birthday", "location", "signature")}),
        ("等级系统", {"fields": ("exp_points", "level")}),
        ("隐私安全", {"fields": ("privacy_settings", "last_login_ip")}),
        (
            "时间信息",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def privacy_display(self, obj):
        privacy_map = {"public": "🌐公开", "follow": "🔒仅关注", "private": "🚫私密"}
        return privacy_map.get(obj.privacy_settings, obj.privacy_settings)

    privacy_display.short_description = "隐私设置"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")


@admin.register(UserLoginHistory)
class UserLoginHistoryAdmin(admin.ModelAdmin):
    """用户登录历史记录管理优化版"""

    list_display = ("id", "login_ip", "device_display", "login_time")
    list_display_links = ("id",)
    search_fields = ("user__username", "login_ip", "device_info")
    list_filter = ("login_time",)
    readonly_fields = ("login_time",)
    ordering = ("-login_time",)
    list_per_page = 50
    date_hierarchy = "login_time"

    def device_display(self, obj):
        if obj.device_info:
            return (
                obj.device_info[:50] + "..."
                if len(obj.device_info) > 50
                else obj.device_info
            )
        return "-"

    device_display.short_description = "设备信息"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")


# ========== 管理后台全局配置 ==========

# 设置管理后台标题
admin.site.site_header = "MiniTieba管理系统"
admin.site.site_title = "MiniTieba管理后台"
