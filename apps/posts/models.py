from django.contrib.auth import get_user_model
from django.db import models

# 用户主模型
UserModel = get_user_model()

# ========== 帖子相关模型 ==========


class Post(models.Model):
    """帖子主表"""

    forum = models.ForeignKey(
        "forums.Forum", on_delete=models.CASCADE, related_name="posts", verbose_name="所属贴吧"
    )
    author = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name="posts", verbose_name="作者"
    )
    title = models.CharField(max_length=255, verbose_name="标题")
    content = models.TextField(verbose_name="内容")
    view_count = models.PositiveIntegerField(default=0, verbose_name="浏览数")
    like_count = models.PositiveIntegerField(default=0, verbose_name="点赞数")
    comment_count = models.PositiveIntegerField(default=0, verbose_name="评论数")
    is_pinned = models.BooleanField(default=False, verbose_name="是否置顶")
    is_locked = models.BooleanField(default=False, verbose_name="是否锁帖")
    is_essence = models.BooleanField(default=False, verbose_name="是否精华")
    is_deleted = models.BooleanField(default=False, verbose_name="是否删除")
    is_draft = models.BooleanField(default=True, verbose_name="是否草稿")
    scheduled_at = models.DateTimeField(
        blank=True, null=True, verbose_name="定时发布时间"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "post"
        verbose_name = "帖子"
        verbose_name_plural = "帖子列表"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class PostImage(models.Model):
    """帖子图片"""

    post = models.ForeignKey(
        "posts.Post", on_delete=models.CASCADE, related_name="images", verbose_name="帖子"
    )
    image_url = models.URLField(verbose_name="图片URL")
    order_index = models.PositiveIntegerField(default=0, verbose_name="排序")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="上传时间")

    class Meta:
        db_table = "post_image"
        verbose_name = "帖子图片"
        verbose_name_plural = "帖子图片列表"
        ordering = ["order_index"]

    def __str__(self):
        return f"Image for {self.post.title}"


class PostTag(models.Model):
    """帖子标签定义"""

    name = models.CharField(max_length=50, unique=True, verbose_name="标签名")
    description = models.TextField(blank=True, null=True, verbose_name="描述")
    color = models.CharField(
        max_length=9,  # 支持 #RRGGBBAA
        blank=True,
        null=True,
        verbose_name="颜色（HEX）",
        help_text="格式如 #FF5733 或 #FF573380（含透明度）",
    )

    class Meta:
        db_table = "post_tag"
        verbose_name = "帖子标签"
        verbose_name_plural = "帖子标签列表"

    def __str__(self):
        return self.name


class PostTagMap(models.Model):
    """帖子与标签映射"""

    post = models.ForeignKey(
        "posts.Post", on_delete=models.CASCADE, related_name="tag_mappings", verbose_name="帖子"
    )
    tag = models.ForeignKey(
        PostTag,
        on_delete=models.CASCADE,
        related_name="post_mappings",
        verbose_name="标签",
    )

    class Meta:
        db_table = "post_tag_map"
        verbose_name = "帖子标签映射"
        verbose_name_plural = "帖子标签映射列表"
        unique_together = ("post", "tag")

    def __str__(self):
        return f"{self.post.title} - {self.tag.name}"
