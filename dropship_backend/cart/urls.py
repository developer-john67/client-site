# cart/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.get_cart, name='cart'),
    path('add/', views.add_to_cart, name='cart-add'),
    path('merge/', views.merge_cart, name='cart-merge'),
    path('clear/<uuid:cart_id>/', views.clear_cart, name='cart-clear'),
    path('items/<uuid:item_id>/', views.update_cart_item, name='cart-item-update'),
    path('items/<uuid:item_id>/remove/', views.remove_from_cart, name='cart-item-remove'),
]