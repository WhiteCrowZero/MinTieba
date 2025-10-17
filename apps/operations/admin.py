from django.contrib import admin
from .models import Report, SystemLog, Announcement


# ========== 系统 / 举报 / 日志 / 公告 ==========


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "reporter",
        "reviewed_by",
        "target_type",
        "target_id",
        "status",
        "created_at",
    )
    search_fields = ("reporter__username", "reviewed_by__username", "reason")
    list_filter = ("status", "target_type")
    readonly_fields = ("created_at",)
    list_per_page = 25


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "action_type",
        "target_type",
        "target_id",
        "ip_address",
        "created_at",
    )
    search_fields = ("user__username",)
    list_filter = ("action_type", "target_type")
    readonly_fields = ("created_at",)
    list_per_page = 50


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "is_active", "start_time", "end_time", "created_at")
    search_fields = ("title",)
    list_filter = ("is_active",)
    readonly_fields = ("created_at",)
    list_per_page = 25
