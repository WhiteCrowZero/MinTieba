from django.contrib import admin
from .models import Post, PostImage, PostTag, PostTagMap


# ========== Post 相关 ==========


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1
    readonly_fields = ("uploaded_at",)


class PostTagMapInline(admin.TabularInline):
    model = PostTagMap
    extra = 1


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "forum",
        "author",
        "view_count",
        "like_count",
        "is_pinned",
        "is_essence",
        "created_at",
    )
    search_fields = ("title", "author__username", "forum__name")
    list_filter = ("is_pinned", "is_locked", "is_essence", "is_deleted", "is_draft")
    readonly_fields = ("created_at", "updated_at")
    inlines = [PostImageInline, PostTagMapInline]
    ordering = ("-created_at",)
    list_per_page = 25


@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "image_url", "order_index", "uploaded_at")
    search_fields = ("post__title",)
    readonly_fields = ("uploaded_at",)
    list_per_page = 25


@admin.register(PostTag)
class PostTagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "color")
    search_fields = ("name",)
    list_per_page = 25


@admin.register(PostTagMap)
class PostTagMapAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "tag")
    search_fields = ("post__title", "tag__name")
    list_per_page = 25
