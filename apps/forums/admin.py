from django.contrib import admin
from .models import (
    Forum,
    ForumCategory,
    ForumCategoryMap,
    ForumRelation,
    ForumMember,
    ForumActivity,
)


# ========== Forum 相关 ==========


class ForumCategoryMapInline(admin.TabularInline):
    model = ForumCategoryMap
    extra = 1


class ForumMemberInline(admin.TabularInline):
    model = ForumMember
    extra = 0
    readonly_fields = ("joined_at",)


@admin.register(Forum)
class ForumAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "creator", "post_count", "member_count", "created_at")
    search_fields = ("name", "creator__username")
    list_filter = ("created_at",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [ForumCategoryMapInline, ForumMemberInline]
    list_per_page = 25


@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "sort_order")
    search_fields = ("name",)
    ordering = ("sort_order",)
    list_per_page = 25


@admin.register(ForumRelation)
class ForumRelationAdmin(admin.ModelAdmin):
    list_display = ("id", "forum", "related", "created_at")
    search_fields = ("forum__name", "related__name")
    readonly_fields = ("created_at",)
    list_per_page = 25


@admin.register(ForumMember)
class ForumMemberAdmin(admin.ModelAdmin):
    list_display = ("id", "forum", "user", "role_type", "joined_at", "is_banned")
    search_fields = ("forum__name", "user__username")
    list_filter = ("role_type", "is_banned")
    readonly_fields = ("joined_at",)
    list_per_page = 25


@admin.register(ForumActivity)
class ForumActivityAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "forum",
        "forum_member",
        "exp_points",
        "level",
        "sign_in_streak",
        "last_active_at",
    )
    search_fields = ("forum__name", "forum_member__user__username")
    list_filter = ("level",)
    list_per_page = 25
