from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),        # localhost:8000/
    path('upload/', views.product_upload, name='product_upload'),  # localhost:8000/upload/
    path('admin-login/', views.admin_login, name='admin_login'),   # localhost:8000/admin-login/
    path('admin-logout/', views.admin_logout, name='admin_logout'),
]