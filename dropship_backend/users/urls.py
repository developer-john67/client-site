# users/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),

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