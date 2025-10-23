from django.conf import settings
from django.core.cache import caches


class CacheService:
    """缓存服务"""

    @staticmethod
    def set_value(key, val, cache="default", exp=settings.DEFAULT_EXPIRE_SECONDS):
        """设置缓存值"""
        caches[cache].set(key, val, exp)

    @staticmethod
    def validate_value(key, val, cache="default"):
        """校验缓存值"""
        cached_val = caches[cache].get(key)
        if cached_val is None:
            return False
        if val != cached_val:
            return False
        return True

    @staticmethod
    def del_value(key, cache="default"):
        """删除缓存值"""
        caches[cache].delete(key)

    @staticmethod
    def get_value(key, cache="default"):
        """获取缓存值"""
        return caches[cache].get(key)
