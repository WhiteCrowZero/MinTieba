from rest_framework.permissions import BasePermission

from interactions.models import UserFollow
from accounts.models import VisibilityChoices


class IsSelf(BasePermission):
    """验证操作用户是否是自己"""

    def has_object_permission(self, request, view, obj):
        return request.user == obj

class CanViewUserProfile(BasePermission):
    """
    根据用户隐私设置判断是否允许访问
    """

    def has_object_permission(self, request, view, obj):
        """
        obj 是 UserAccount
        """
        # 用户本人始终可以访问
        if obj == request.user:
            return True

        # 获取隐私设置
        privacy = getattr(obj.profile, "privacy_settings", VisibilityChoices.PUBLIC)

        if privacy == VisibilityChoices.PUBLIC:
            return True
        elif privacy == VisibilityChoices.FOLLOW:
            return UserFollow.objects.filter(user=obj, followed_user=request.user).exists()
        elif privacy == VisibilityChoices.PRIVATE:
            return False

        # 默认不允许
        return False