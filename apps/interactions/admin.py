from django.contrib import admin
from .models import (
    Comment,
    LikeRecord,
    CollectionFolder,
    CollectionItem,
    UserFollow,
    Notification,
    MessageThread,
    PrivateMessage,
)


# ========== 互动 / 评论 / 点赞 / 收藏 / 关注 ==========


class CommentInline(admin.TabularInline):
    """在帖子或评论中可嵌入子评论（回复）"""

    model = Comment
    fk_name = "parent"
    extra = 1
    readonly_fields = ("created_at",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "post",
        "parent",
        "author",
        "floor_number",
        "like_count",
        "is_deleted",
        "created_at",
    )
    search_fields = ("author__username", "post__title", "content")
    list_filter = ("is_deleted",)
    readonly_fields = ("created_at",)
    ordering = ("created_at",)
    inlines = [CommentInline]
    list_per_page = 25


@admin.register(LikeRecord)
class LikeRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "target_type", "target_id", "is_active", "created_at")
    search_fields = ("user__username",)
    list_filter = ("target_type", "is_active")
    readonly_fields = ("created_at",)
    list_per_page = 25


class CollectionItemInline(admin.TabularInline):
    model = CollectionItem
    extra = 1
    readonly_fields = ("created_at",)


@admin.register(CollectionFolder)
class CollectionFolderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "name", "is_default", "is_deleted", "created_at")
    search_fields = ("user__username", "name")
    list_filter = ("is_default", "is_deleted")
    readonly_fields = ("created_at",)
    inlines = [CollectionItemInline]
    list_per_page = 25


@admin.register(CollectionItem)
class CollectionItemAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "folder", "post", "is_deleted", "created_at")
    search_fields = ("user__username", "post__title")
    list_filter = ("is_deleted",)
    readonly_fields = ("created_at",)
    list_per_page = 25


@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    list_display = ("id", "follower", "followed", "created_at")
    search_fields = ("follower__username", "followed__username")
    readonly_fields = ("created_at",)
    list_per_page = 25


# ========== 通知 / 消息 ==========


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "title",
        "type",
        "target_type",
        "target_id",
        "is_read",
        "created_at",
    )
    search_fields = ("user__username", "title", "message")
    list_filter = ("type", "target_type", "is_read")
    readonly_fields = ("created_at",)
    list_per_page = 25


class PrivateMessageInline(admin.TabularInline):
    model = PrivateMessage
    extra = 1
    readonly_fields = ("created_at",)


@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display = ("id", "user1", "user2", "last_message_preview", "updated_at")
    search_fields = ("user1__username", "user2__username")
    readonly_fields = ("updated_at",)
    inlines = [PrivateMessageInline]
    list_per_page = 25


@admin.register(PrivateMessage)
class PrivateMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "thread", "sender", "is_read", "created_at")
    search_fields = (
        "sender__username",
        "thread__user1__username",
        "thread__user2__username",
    )
    list_filter = ("is_read",)
    readonly_fields = ("created_at",)
    list_per_page = 25
