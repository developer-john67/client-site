from django.urls import path
from ...migrations import views

urlpatterns = [
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
    path('admin/upload/', views.product_upload, name='product_upload'),
    path('admin/products/', views.product_list, name='product_list'),
]