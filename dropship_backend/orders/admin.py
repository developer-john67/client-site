# orders/admin.py

from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'order_number', 'user_id', 'status',
                    'payment_status', 'total_amount', 'created_at')
    readonly_fields = ('order_id', 'order_number', 'created_at', 'updated_at')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order_item_id', 'order_id', 'product_name',
                    'quantity', 'unit_price', 'total_price')
    readonly_fields = ('order_item_id', 'created_at')


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('history_id', 'order_id', 'order_number', 'status', 'created_at')
    readonly_fields = ('history_id', 'created_at')