from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from . import views

urlpatterns = [
    path('send-code/', csrf_exempt(views.send_verification_code), name='send-verification-code'),
    path('verify/', csrf_exempt(views.verify_code), name='verify-code'),
    path('resend/', csrf_exempt(views.resend_code), name='resend-code'),
    path('verify-password-reset/', csrf_exempt(views.verify_password_reset), name='verify-password-reset'),
]
