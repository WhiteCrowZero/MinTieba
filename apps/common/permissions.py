from rest_framework.permissions import BasePermission


class IsSelf(BasePermission):
    """验证操作用户是否是自己"""

    def has_object_permission(self, request, view, obj):
        return request.user == obj
