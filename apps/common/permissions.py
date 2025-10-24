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
            return UserFollow.objects.filter(
                user=obj, followed_user=request.user
            ).exists()
        elif privacy == VisibilityChoices.PRIVATE:
            return False

        # 默认不允许
        return False


class RBACPermission(BasePermission):
    """
    检查用户是否具备 view.permission_code 指定的权限
    """

    @staticmethod
    def user_has_permission(user, perm_code):
        """判断用户是否拥有指定权限"""
        if not user.is_authenticated:
            return False

        if getattr(user.role, "level", 0) >= 100:  # 超级管理员放行
            return True

        return user.role.permissions.filter(permission__code=perm_code).exists()

    def has_permission(self, request, view):
        perm_code = getattr(view, "permission_code", None)
        if not perm_code:
            return True  # 默认不限制

        return self.user_has_permission(request.user, perm_code)
