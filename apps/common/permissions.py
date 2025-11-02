import logging
from typing import Optional

from rest_framework.permissions import BasePermission

from forums.models import RoleChoices, Forum, ForumMember
from interactions.models import UserFollow
from accounts.models import VisibilityChoices

logger = logging.getLogger("feat")


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
    通用 RBAC 权限类
    支持：
      - 单视图（GenericAPIView）
      - ViewSet 中基于 action 的权限映射
    """

    def get_permission_code(self, view):
        """
        自动从 View 或 ViewSet 中获取对应的权限码
        优先级：
          1. view.permission_code（单接口）
          2. view.action_permissions[view.action]（ViewSet）
        """
        # 单 APIView 场景
        """
        使用示例：
        permission_code = "rbac.view_roles"
        """
        if hasattr(view, "permission_code"):
            return view.permission_code

        # ViewSet 场景
        """
        使用示例：
        permission_classes = [IsAuthenticated, RBACPermission]
        action_permissions = {
            'create': 'forums.create_forum',
            'update': 'forums.edit_forum',
            'partial_update': 'forums.edit_forum',
            'destroy': 'forums.delete_forum',
        }
        """
        action_perms = getattr(view, "action_permissions", {})
        perm_code = action_perms.get(view.action)
        if perm_code:
            return perm_code
        else:
            logger.warning(
                f"[RBAC] 未为 {view.__class__.__name__}.{view.action} 定义权限码"
            )
            return None

    @staticmethod
    def user_has_permission(user, perm_code):
        """判断用户是否拥有指定权限"""
        if not user.is_authenticated:
            return False

        # 超级管理员放行
        if getattr(user.role, "level", 0) >= 100:
            return True

        # 普通角色权限判断
        return user.role.permissions.filter(permission__code=perm_code).exists()

    def has_permission(self, request, view):
        """统一入口"""
        perm_code = self.get_permission_code(view)
        if not perm_code:
            return True  # 未定义权限码则默认放行

        return self.user_has_permission(request.user, perm_code)


class IsForumAdmin(BasePermission):
    """
    判断用户是否为当前请求目标贴吧的管理员或吧主（ADMIN / OWNER）
    支持以下场景：
      - URL 中包含 forum id
      - 对象本身是 Forum 或带 forum 外键
    """

    def _is_super_admin(self, user) -> bool:
        """平台级超级管理员判定"""
        if getattr(user, "is_superuser", False):
            return True
        return getattr(getattr(user, "role", None), "level", 0) >= 100

    def _get_forum_from_view(self, view) -> Optional[Forum]:
        """从 URL kwargs 中提取论坛对象"""
        for key in ("pk", "id", "forum_pk", "forum_id"):
            forum_id = view.kwargs.get(key)
            if forum_id:
                try:
                    return Forum.objects.get(pk=forum_id)
                except Forum.DoesNotExist:
                    return None
        return None

    def _user_is_forum_admin(self, user, forum: Forum) -> bool:
        """检查用户是否为该吧的管理员或吧主"""
        if not user or not user.is_authenticated:
            return False
        if self._is_super_admin(user):
            return True
        return ForumMember.objects.filter(
            forum=forum,
            user=user,
            role_type__in=[RoleChoices.ADMIN, RoleChoices.OWNER],
        ).exists()

    def has_permission(self, request, view):
        """全局权限：登录检查 + URL 贴吧检查"""

        user = request.user
        # 1. 基础认证检查
        if not user.is_authenticated:
            return False
        # 2. 超级管理员直接通过
        if self._is_super_admin(user):
            return True

        # 3. 尝试从 URL 获取贴吧并检查权限
        forum = self._get_forum_from_view(view)
        if forum:
            return self._user_is_forum_admin(user, forum)

        # 4. 无法确定贴吧时，暂时通过（留给后续检查）
        return True

    def has_object_permission(self, request, view, obj):
        """对象级权限"""

        user = request.user
        # 1. 基础检查
        if not user or not user.is_authenticated:
            return False
        # 2. 超级管理员直接通过
        if self._is_super_admin(user):
            return True

        # 3. 从对象中提取贴吧信息
        # 对象本身就是贴吧
        if isinstance(obj, Forum):
            forum = obj
        # 常见情况： obj 可能有 .forum 外键（例如 ForumMember, Post, Thread）
        else:
            forum = getattr(obj, "forum", None)  # 对象有关联的贴吧

        # 4. 如果还找不到贴吧，尝试从 URL 获取
        if forum is None:
            forum = self._get_forum_from_view(view)

        # 5. 最终检查
        if not forum:
            return False  # 完全无法确定贴吧，拒绝访问

        return self._user_is_forum_admin(user, forum)
