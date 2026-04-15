# users/urls.py

from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from . import views

urlpatterns = [
    # Auth
    path('register/', csrf_exempt(views.register), name='register'),
    path('login/', csrf_exempt(views.login), name='login'),
    path('logout/', views.logout, name='logout'),
    
    # Email Verification
    path('verify-email/', csrf_exempt(views.verify_email), name='verify-email'),
    path('resend-verification/', csrf_exempt(views.resend_verification), name='resend-verification'),

    # Profile
    path('profile/', views.get_profile, name='profile'),
    path('profile/update/', views.update_profile, name='update-profile'),
    path('change-password/', views.change_password, name='change-password'),

    # Addresses
    path('addresses/', views.address_list, name='address-list'),
    path('addresses/create/', views.create_address, name='create-address'),
    path('addresses/<uuid:address_id>/', views.address_detail, name='address-detail'),
    path('addresses/<uuid:address_id>/update/', views.update_address, name='update-address'),
    path('addresses/<uuid:address_id>/delete/', views.delete_address, name='delete-address'),
]