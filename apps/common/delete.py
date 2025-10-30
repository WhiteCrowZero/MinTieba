# common/models/soft_delete.py
from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        """批量软删除"""
        return super().update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        """批量物理删除"""
        return super().delete()

    def active(self):
        """仅返回未删除记录"""
        return self.filter(is_deleted=False)

    def deleted(self):
        """仅返回已删除记录"""
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    """默认返回未删除的数据"""
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).active()

    def all_with_deleted(self):
        """返回所有数据，包括软删除的"""
        return SoftDeleteQuerySet(self.model, using=self._db)

    def deleted_only(self):
        """仅返回已删除的数据"""
        return SoftDeleteQuerySet(self.model, using=self._db).deleted()

    def soft_delete(self, queryset=None):
        """批量软删除"""
        if queryset is None:
            queryset = self.get_queryset()
        queryset.delete()


class SoftDeleteModel(models.Model):
    """通用软删除基类"""
    is_deleted = models.BooleanField(default=False, verbose_name="是否删除")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="删除时间")

    # 默认管理器只显示未删除
    objects = SoftDeleteManager()
    # 如果你要访问所有（包含删除的）
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """单个实例软删除"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def hard_delete(self, using=None, keep_parents=False):
        """物理删除"""
        super().delete(using=using, keep_parents=keep_parents)
