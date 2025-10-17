from django.contrib.auth import get_user_model
from posts.models import Post
from django.db import models

# 用户主模型
UserModel = get_user_model()

# ========== 枚举常量 ==========


class TargeTypeChoices(models.TextChoices):
    """目标对象枚举"""

    POST = ("post", "帖子")
    COMMENT = ("comment", "评论")


class NotificationTypeChoices(models.TextChoices):
    """通知类型枚举"""

    SYSTEM = ("system", "系统")
    REPLY = ("reply", "回复")
    LIKE = ("like", "点赞")
    MENTION = ("mention", "提及")
    FOLLOW = ("follow", "关注")


# ========== 互动 / 评论 / 点赞 / 收藏 / 关注 ==========


class Comment(models.Model):
    """评论表"""

    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments", verbose_name="帖子"
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="replies",
        verbose_name="父评论",
    )
    author = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="作者",
    )
    content = models.TextField(verbose_name="评论内容")
    like_count = models.PositiveIntegerField(default=0, verbose_name="点赞数")
    floor_number = models.PositiveIntegerField(default=0, verbose_name="楼层号")
    is_deleted = models.BooleanField(default=False, verbose_name="是否删除")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "comment"
        verbose_name = "评论"
        verbose_name_plural = "评论列表"
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment #{self.id} by {self.author.username}"


class LikeRecord(models.Model):
    """点赞记录表，可对帖子或评论点赞"""

    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="like_records",
        verbose_name="用户",
    )
    target_type = models.CharField(
        max_length=20, choices=TargeTypeChoices.choices, verbose_name="目标类型"
    )
    target_id = models.PositiveIntegerField(verbose_name="目标 ID")
    is_active = models.BooleanField(default=True, verbose_name="是否生效")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "like_record"
        verbose_name = "点赞记录"
        verbose_name_plural = "点赞记录列表"
        # 防止点赞数重复：("user", "target_type", "target_id") 建立唯一索引
        unique_together = ("user", "target_type", "target_id")

    def __str__(self):
        return f"{self.user.username} likes {self.target_type} {self.target_id}"


class CollectionFolder(models.Model):
    """用户收藏夹表"""

    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="collection_folders",
        verbose_name="用户",
    )
    name = models.CharField(max_length=100, verbose_name="收藏夹名称")
    description = models.TextField(blank=True, null=True, verbose_name="描述")
    is_default = models.BooleanField(default=False, verbose_name="是否默认")
    is_deleted = models.BooleanField(default=False, verbose_name="是否删除")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "collection_folder"
        verbose_name = "收藏夹"
        verbose_name_plural = "收藏夹列表"

    def __str__(self):
        return f"{self.user.username} - {self.name}"


class CollectionItem(models.Model):
    """收藏的帖子"""

    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="collection_items",
        verbose_name="用户",
    )
    folder = models.ForeignKey(
        CollectionFolder,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="收藏夹",
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="collected_by", verbose_name="帖子"
    )
    is_deleted = models.BooleanField(default=False, verbose_name="是否删除")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "collection_item"
        verbose_name = "收藏项"
        verbose_name_plural = "收藏项列表"
        # 防止重复收藏： (user, folder, post) 唯一
        unique_together = ("user", "folder", "post")

    def __str__(self):
        return f"{self.user.username}收藏 {self.post.title}"


class UserFollow(models.Model):
    """用户关注 / 被关注表"""

    follower = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="关注者",
    )
    followed = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="followers",
        verbose_name="被关注者",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "user_follow"
        verbose_name = "用户关注"
        verbose_name_plural = "用户关注列表"
        # 避免 A->B,B->A 同时出现，建立唯一索引
        unique_together = ("follower", "followed")

    def __str__(self):
        return f"{self.follower.username} → {self.followed.username}"


# ========== 通知 / 消息 ==========


class Notification(models.Model):
    """系统 / 用户通知表"""

    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="接收用户",
    )
    title = models.CharField(max_length=200, verbose_name="标题")
    message = models.TextField(verbose_name="消息内容")
    type = models.CharField(
        max_length=20, choices=NotificationTypeChoices.choices, verbose_name="通知类型"
    )
    target_type = models.CharField(
        max_length=20,
        choices=TargeTypeChoices.choices,
        blank=True,
        null=True,
        verbose_name="目标类型",
    )
    target_id = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="目标 ID"
    )
    is_read = models.BooleanField(default=False, verbose_name="已读状态")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "notification"
        verbose_name = "通知"
        verbose_name_plural = "通知列表"
        ordering = ["-created_at"]

    def __str__(self):
        return f"通知给 {self.user.username}: {self.title}"


class MessageThread(models.Model):
    """私信会话 (两人一对一)"""

    user1 = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="threads_as_user1",
        verbose_name="用户1",
    )
    user2 = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="threads_as_user2",
        verbose_name="用户2",
    )
    last_message_preview = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="最近消息预览"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "message_thread"
        verbose_name = "私信会话"
        verbose_name_plural = "私信会话列表"
        # 加一个约束，保证唯一组合 (user1, user2) 与 (user2, user1) 视作相同
        unique_together = ("user1", "user2")

    def __str__(self):
        return f"Thread: {self.user1.username} ↔ {self.user2.username}"


class PrivateMessage(models.Model):
    """私信消息表"""

    thread = models.ForeignKey(
        MessageThread,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="会话",
    )
    sender = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="sent_messages",
        verbose_name="发送者",
    )
    content = models.TextField(verbose_name="消息内容")
    image_url = models.URLField(blank=True, null=True, verbose_name="图片 URL")
    is_read = models.BooleanField(default=False, verbose_name="已读状态")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "private_message"
        verbose_name = "私信消息"
        verbose_name_plural = "私信消息列表"
        ordering = ["created_at"]

    def __str__(self):
        return f"From {self.sender.username} at {self.created_at}"
