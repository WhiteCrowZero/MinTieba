# forums/urls.py
from django.urls import include, path
from rest_framework_nested import routers
from .views import (
    ForumViewSet,
    ForumCategoryViewSet,
    ForumCoverImageView,
    CategoryIconImageView,
    ForumMemberViewSet,
    ForumMemberReadOnlyViewSet,
    ForumMemberRoleViewSet,
)

# 创建主路由
router = routers.DefaultRouter()
router.register(r"forums", ForumViewSet, basename="forum")
router.register(r"forums/categories", ForumCategoryViewSet, basename="category")

# 嵌套路由，针对 forum_pk 的成员相关操作
forums_router = routers.NestedDefaultRouter(router, r"forums", lookup="forum")
# 只读接口
forums_router.register(
    r"members/readonly", ForumMemberReadOnlyViewSet, basename="forum-member-read"
)
# 加入/退出接口
forums_router.register(
    r"members/membership", ForumMemberViewSet, basename="forum-member-action"
)
# 管理接口（角色修改、封禁）
forums_router.register(
    r"members/role", ForumMemberRoleViewSet, basename="forum-member-manage"
)

urlpatterns = [
    # 主路由 URL
    path("", include(router.urls)),
    # 嵌套路由 URL
    path("", include(forums_router.urls)),
    # 论坛封面图和分类图标更新路径
    path(
        "forums/<int:pk>/cover/",
        ForumCoverImageView.as_view(),
        name="forum-cover-update",
    ),
    path(
        "forums/categories/<int:pk>/icon/",
        CategoryIconImageView.as_view(),
        name="category-icon-update",
    ),
]
