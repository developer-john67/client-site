from django.urls import path
from . import views

urlpatterns = [
    # Customer endpoints
    path('', views.my_orders, name='my-orders'),
    path('create/', views.create_order, name='create-order'),
    path('<uuid:order_id>/', views.order_detail, name='order-detail'),
    path('<uuid:order_id>/cancel/', views.cancel_order, name='cancel-order'),

    # M-Pesa payment endpoints (Daraja API)
    path('mpesa/initiate/', views.initiate_mpesa_payment, name='initiate-mpesa'),
    path('mpesa/check/', views.check_mpesa_payment, name='check-mpesa'),
    path('mpesa/webhook/', views.daraja_webhook, name='daraja-webhook'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa-callback'),

    # Admin endpoints
    path('admin/all/', views.admin_order_list, name='admin-order-list'),
    path('admin/<uuid:order_id>/status/', views.admin_update_order_status, name='admin-update-status'),
    path('admin/<uuid:order_id>/payment/', views.admin_update_payment_status, name='admin-update-payment'),
]