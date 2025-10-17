from django.contrib.auth import get_user_model
from django.db import models

# 用户主模型
UserModel = get_user_model()

# ========== 枚举常量 ==========


class TargeTypeChoices(models.TextChoices):
    """目标对象枚举"""

    USER = ("user", "用户")
    FORUM = ("forum", "贴吧")
    POST = ("post", "帖子")
    COMMENT = ("comment", "评论")


class ReportStatusChoices(models.TextChoices):
    """举报状态枚举"""

    PENDING = ("pending", "待处理")
    APPROVED = ("approved", "已通过")
    REJECTED = ("rejected", "已拒绝")


class ActionTypeChoices(models.TextChoices):
    """通知类型枚举"""

    UPDATE = ("update", "更新")
    CREATE = ("create", "创建")
    DELETE = ("delete", "删除")
    SELECT = ("select", "查询")
    LOGIN = ("login", "登录")
    LOGOUT = ("logout", "登出")
    REGISTER = ("register", "注册")
    BAN = ("ban", "封禁")
    UPLOAD = ("upload", "上传")
    RECOVER = ("recover", "恢复")
    APPROVE = ("approve", "审核通过")
    REJECT = ("reject", "审核拒绝")


# ========== 系统 / 举报 / 日志 / 公告 ==========


class Report(models.Model):
    """举报记录表"""

    reporter = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="reports_made",
        verbose_name="举报者",
    )
    reviewed_by = models.ForeignKey(
        UserModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports_reviewed",
        verbose_name="审核者",
    )
    target_type = models.CharField(
        max_length=20, choices=TargeTypeChoices.choices, verbose_name="目标类型"
    )
    target_id = models.PositiveIntegerField(verbose_name="目标 ID")
    reason = models.TextField(verbose_name="举报原因")
    status = models.CharField(
        max_length=20,
        choices=ReportStatusChoices.choices,
        default=ReportStatusChoices.PENDING,
        verbose_name="状态",
    )
    evidence_url = models.URLField(blank=True, null=True, verbose_name="证据 URL")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "report"
        verbose_name = "举报"
        verbose_name_plural = "举报列表"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report #{self.id} by {self.reporter.username}"


class SystemLog(models.Model):
    """系统操作日志表"""

    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="system_logs",
        verbose_name="操作用户",
    )
    action_type = models.CharField(
        max_length=20, choices=ActionTypeChoices.choices, verbose_name="操作类型"
    )
    target_type = models.CharField(
        max_length=20, choices=TargeTypeChoices.choices, verbose_name="目标类型"
    )
    target_id = models.PositiveIntegerField(verbose_name="目标 ID")
    ip_address = models.GenericIPAddressField(
        blank=True, null=True, verbose_name="IP 地址"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="操作时间")

    class Meta:
        db_table = "system_log"
        verbose_name = "系统日志"
        verbose_name_plural = "系统日志列表"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} {self.action_type} {self.target_type}#{self.target_id}"


class Announcement(models.Model):
    """系统公告表"""

    title = models.CharField(max_length=200, verbose_name="标题")
    content = models.TextField(verbose_name="内容")
    start_time = models.DateTimeField(verbose_name="开始时间")
    end_time = models.DateTimeField(verbose_name="结束时间")
    is_active = models.BooleanField(default=True, verbose_name="是否生效")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="发布时间")

    class Meta:
        db_table = "announcement"
        verbose_name = "公告"
        verbose_name_plural = "公告列表"
        ordering = ["-start_time"]

    def __str__(self):
        return self.title
