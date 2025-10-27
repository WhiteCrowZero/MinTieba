# forums/urls.py
from django.urls import include, path
from rest_framework_nested import routers
from .views import (
    ForumViewSet,
    ForumCategoryViewSet,
    ForumCoverImageView,
    CategoryIconImageView,
)

router = routers.DefaultRouter()
router.register(r"forums", ForumViewSet, basename="forum")
router.register(r"categories", ForumCategoryViewSet, basename="category")


urlpatterns = [
    path("", include(router.urls)),
    path(
        "forums/<int:pk>/cover/",
        ForumCoverImageView.as_view(),
        name="forum-cover-update",
    ),
    path(
        "categories/<int:pk>/icon/",
        CategoryIconImageView.as_view(),
        name="category-icon-update",
    ),
]
