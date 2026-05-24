# otp/urls.py
from django.urls import path
from .views import RequestOTPView, VerifyOTPView

urlpatterns = [
    path("request/", RequestOTPView.as_view(), name="request_otp"),
    path("verify/", VerifyOTPView.as_view(), name="verify_otp"),
]
