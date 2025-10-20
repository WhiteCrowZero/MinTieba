from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    ResetPasswordView,
    DestroyUserView,
)

urlpatterns = [
    # 普通注册
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path('password/reset/', ResetPasswordView.as_view(), name='password-reset'),
    # # 第三方注册和登录（合并为同一个接口）
    # path('oauth/login/', OauthLoginView.as_view(), name='oauth-login'),
    # 删除账号（软删除）
    path('destroy/', DestroyUserView.as_view(), name='destroy-user'),
    # # 基本信息
    # path('info/', UserInfoView.as_view(), name='info'),
    # path('info/detial/', UserInfoDetailView.as_view(), name='info-detail'),
    # # 用户头像
    # path('info/avatar/', UserAvatarView.as_view(), name='info-avatar'),
    # # 绑定账号
    # path('contact/', UserContactView.as_view(), name='contact'),
    # path('contact/<str:type>/', UserContactDetailView.as_view(), name='contact-detail'),
]
