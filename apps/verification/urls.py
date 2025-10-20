from django.urls import path
from .views import (
    ImageCaptchaView,
)

urlpatterns = [
    # path('email/activate/', views.EmailActivateView.as_view(), name='email-activate'),
    # path('email/send/activate/', views.EmailActivateSendView.as_view(), name='email-activate-send'),
    # path('email/verify/', views.EmailVerifyView.as_view(), name='email-verify'),
    # path('email/send/verify/', views.EmailSendVerifyView.as_view(), name='email-verify-send'),
    path("captcha/", ImageCaptchaView.as_view(), name="image-captcha"),
]
