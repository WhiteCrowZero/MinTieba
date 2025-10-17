from django.contrib import admin
from .models import (
    Role,
    Permission,
    RolePermissionMap,
    UserAccount,
    UserProfile,
    UserLoginHistory,
)


# ========== RBAC 部分 ==========


class RolePermissionMapInline(admin.TabularInline):
    """在角色页面中显示角色-权限映射"""

    model = RolePermissionMap
    extra = 1
    autocomplete_fields = ["permission"]
    readonly_fields = ["created_at"]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """角色管理"""

    list_display = ("id", "name", "level", "description")
    search_fields = ("name",)
    ordering = ("level",)
    inlines = [RolePermissionMapInline]
    list_filter = ("level",)
    list_per_page = 20


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """权限管理"""

    list_display = ("id", "code", "name", "category", "description")
    search_fields = ("code", "name")
    list_filter = ("category",)
    ordering = ("category", "id")
    list_per_page = 25


@admin.register(RolePermissionMap)
class RolePermissionMapAdmin(admin.ModelAdmin):
    """角色权限映射管理"""

    list_display = ("id", "role", "permission", "created_at")
    search_fields = ("role__name", "permission__name", "permission__code")
    list_filter = ("role", "permission__category")
    readonly_fields = ("created_at",)
    list_per_page = 30


# ========== 用户信息部分 ==========


class UserProfileInline(admin.StackedInline):
    """在用户账户详情中显示扩展信息"""

    model = UserProfile
    extra = 0
    can_delete = False
    readonly_fields = ("created_at", "updated_at")


class UserLoginHistoryInline(admin.TabularInline):
    """在用户详情中显示最近登录记录"""

    model = UserLoginHistory
    extra = 0
    readonly_fields = ("login_ip", "device_info", "login_time")
    can_delete = False
    ordering = ("-login_time",)


@admin.register(UserAccount)
class UserAccountAdmin(admin.ModelAdmin):
    """用户主要信息管理"""

    list_display = (
        "id",
        "username",
        "email",
        "mobile",
        "role",
        "is_active",
        "is_banned",
        "created_at",
    )
    search_fields = ("username", "email", "mobile")
    list_filter = ("is_active", "is_banned", "role")
    readonly_fields = ("created_at", "updated_at")
    inlines = [UserProfileInline, UserLoginHistoryInline]
    list_per_page = 25
    fieldsets = (
        ("基础信息", {"fields": ("username", "password", "email", "mobile", "role")}),
        ("状态信息", {"fields": ("is_active", "is_banned")}),
        ("个性信息", {"fields": ("avatar_url", "bio", "gender")}),
        ("系统信息", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """用户补充信息管理"""

    list_display = (
        "id",
        "user",
        "level",
        "exp_points",
        "location",
        "last_login_ip",
        "updated_at",
    )
    search_fields = ("user__username", "location")
    list_filter = ("level",)
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 25


@admin.register(UserLoginHistory)
class UserLoginHistoryAdmin(admin.ModelAdmin):
    """用户登录历史记录管理"""

    list_display = ("id", "user", "login_ip", "device_info", "login_time")
    search_fields = ("user__username", "login_ip", "device_info")
    list_filter = ("login_time",)
    readonly_fields = ("login_time",)
    ordering = ("-login_time",)
    list_per_page = 50
