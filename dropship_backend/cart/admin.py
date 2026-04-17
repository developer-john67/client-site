# cart/admin.py

from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('item_id', 'total_price', 'added_at')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('cart_id', 'user_id', 'session_id', 'item_count', 'subtotal', 'created_at', 'updated_at')
    list_filter = ('created_at',)
    search_fields = ('cart_id', 'user_id', 'session_id')
    readonly_fields = ('cart_id', 'created_at', 'updated_at')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('item_id', 'cart_id', 'product_name', 'quantity', 'unit_price', 'total_price')
    readonly_fields = ('item_id', 'added_at', 'updated_at')