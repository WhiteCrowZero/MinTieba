from django.urls import path

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    ResetPasswordView,
    DestroyUserView,
    UserProfileView,
    UserProfileRetrieveUpdateView,
    UserBasicInfoView,
    UserBasicInfoUpdateView,
    UserAvatarView,
)

urlpatterns = [
    # 普通注册、登录
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    # 账户激活
    # path('activate/', ActivateUserView.as_view(), name='activate-user'),
    # 登出
    path("logout/", LogoutView.as_view(), name="logout"),
    # 基本信息展示和修改
    path("info/", UserBasicInfoUpdateView.as_view(), name="info-update"),
    path("info/<int:pk>/", UserBasicInfoView.as_view(), name="info-retrieve"),
    # 头像修改
    path('info/avatar/', UserAvatarView.as_view(), name='info-avatar'),
    # 邮箱修改
    # 手机号修改
    # 扩展信息展示和修改
    path("profile/", UserProfileRetrieveUpdateView.as_view(), name="profile-update"),
    path("profile/<int:pk>/", UserProfileView.as_view(), name="profile-retrieve"),
    # 密码重置
    path("password/reset/", ResetPasswordView.as_view(), name="password-reset"),
    # 删除账号（软删除）
    path("destroy/", DestroyUserView.as_view(), name="destroy-user"),
    # # 第三方注册和登录（合并为同一个接口）
    # path('oauth/login/', OauthLoginView.as_view(), name='oauth-login'),
    # # 绑定账号
    # path('contact/', UserContactView.as_view(), name='contact'),
    # path('contact/<str:type>/', UserContactDetailView.as_view(), name='contact-detail'),
]
