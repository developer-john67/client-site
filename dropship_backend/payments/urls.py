from django.urls import path
from . import views

urlpatterns = [
    path('initiate/', views.initiate_payment, name='initiate-payment'),
    path('callback/', views.payment_callback, name='payment-callback'),
    path('status/<str:transaction_id>/', views.payment_status, name='payment-status'),
    path('create-link/', views.create_payment_link, name='create-payment-link'),
]
