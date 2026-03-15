from django.urls import path
from . import views

urlpatterns = [
    # Public endpoints
    path('', views.product_list, name='product-list'),
    path('category/', views.category_list, name='category-list'),
    path('category/<slug:slug>/', views.category_detail, name='category-detail'),

    # Admin endpoints — must come BEFORE <slug:slug>
    path('admin/all/', views.admin_products, name='admin-products'),
    path('admin/category/create/', views.admin_create_category, name='admin-create-category'),
    path('admin/<uuid:product_id>/', views.admin_product_detail, name='admin-product-detail'),

    # These go last since they're catch-all slug/uuid patterns
    path('<uuid:product_id>/review/', views.add_product_review, name='add-review'),
    path('<slug:slug>/', views.product_detail, name='product-detail'),
]