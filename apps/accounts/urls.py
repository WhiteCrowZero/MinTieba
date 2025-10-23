from django.urls import path

from .views import (
    RegisterView,
    LoginView,
    ImageCaptchaView,
    LogoutView,
    ResetPasswordView,
    DestroyUserView,
    UserProfileView,
    UserProfileRetrieveUpdateView,
    UserBasicInfoView,
    UserBasicInfoUpdateView,
    UserAvatarView,
    UserEmailUpdateView,
    UserEmailVerifySendView,
    UserActivateSendView,
    UserActivateVerifyView,
)

urlpatterns = [
    # 普通注册、登录
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    # 图片验证码发送
    path("captcha/", ImageCaptchaView.as_view(), name="image-captcha"),
    # 账户激活（原本是email和mobile，但是目前sms服务有问题，只用email）
    path("activate/email/send/", UserActivateSendView.as_view(), name="activate-email-send"),
    path("activate/email/verify/", UserActivateVerifyView.as_view(), name="activate-email-verify"),
    # 登出
    path("logout/", LogoutView.as_view(), name="logout"),
    # 基本信息展示和修改
    path("info/", UserBasicInfoUpdateView.as_view(), name="info-update"),
    path("info/<int:pk>/", UserBasicInfoView.as_view(), name="info-retrieve"),
    # 头像修改
    path("info/avatar/", UserAvatarView.as_view(), name="info-avatar"),
    # 邮箱修改和验证码发送
    path("email/update/", UserEmailUpdateView.as_view(), name="email-update"),
    path("email/verify/", UserEmailVerifySendView.as_view(), name="email-verify"),
    # 手机号修改和验证码发送（sms服务有问题，无法申请或者发送收不到，弃用）
    # path("mobile/update/", UserMobileUpdateView.as_view(), name="mobile-update"),
    # path("mobile/verify/", UserMobileVerifySendView.as_view(), name="mobile-verify"),
    # 扩展信息展示和修改
    path("profile/", UserProfileRetrieveUpdateView.as_view(), name="profile-update"),
    path("profile/<int:pk>/", UserProfileView.as_view(), name="profile-retrieve"),
    # 密码重置
    path("password/reset/", ResetPasswordView.as_view(), name="password-reset"),
    # 删除账号（软删除）
    path("destroy/", DestroyUserView.as_view(), name="destroy-user"),
]
