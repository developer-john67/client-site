# orders/serializers.py

from rest_framework import serializers
import uuid
from datetime import datetime
from .models import Order, OrderItem, OrderStatusHistory


class OrderItemSerializer(serializers.Serializer):
    order_item_id = serializers.UUIDField(read_only=True)
    order_id = serializers.UUIDField(required=True)
    order_number = serializers.CharField(required=False, allow_blank=True)
    product_id = serializers.UUIDField(required=True)
    product_name = serializers.CharField(required=True)
    product_sku = serializers.CharField(required=False, allow_blank=True)
    product_image = serializers.CharField(required=False, allow_blank=True)
    variant_id = serializers.UUIDField(required=False, allow_null=True)
    variant_name = serializers.CharField(required=False, allow_blank=True)
    variant_info = serializers.DictField(required=False, default=dict)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    quantity = serializers.IntegerField(min_value=1)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    created_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        validated_data['order_item_id'] = uuid.uuid4()
        validated_data['created_at'] = datetime.utcnow()
        return OrderItem.objects.create(**validated_data)


class OrderStatusHistorySerializer(serializers.Serializer):
    history_id = serializers.UUIDField(read_only=True)
    order_id = serializers.UUIDField(read_only=True)
    order_number = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=True)
    note = serializers.CharField(required=False, allow_blank=True)
    changed_by = serializers.UUIDField(required=False, allow_null=True)
    changed_by_name = serializers.CharField(required=False, allow_blank=True)
    created_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        validated_data['history_id'] = uuid.uuid4()
        validated_data['created_at'] = datetime.utcnow()
        return OrderStatusHistory.objects.create(**validated_data)


class OrderSerializer(serializers.Serializer):
    order_id = serializers.UUIDField(read_only=True)
    order_number = serializers.CharField(read_only=True)
    user_id = serializers.UUIDField(required=True)
    status = serializers.CharField(default='pending')
    payment_status = serializers.CharField(default='pending')
    payment_method = serializers.CharField(required=False, allow_blank=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = serializers.DictField(required=False, default=dict)
    billing_address = serializers.DictField(required=False, default=dict)
    shipping_method = serializers.CharField(required=False, allow_blank=True)
    tracking_number = serializers.CharField(required=False, allow_blank=True)
    estimated_delivery = serializers.DateField(required=False, allow_null=True)
    delivered_at = serializers.DateTimeField(required=False, allow_null=True)
    customer_email = serializers.CharField(required=False, allow_blank=True)
    customer_name = serializers.CharField(required=False, allow_blank=True)
    customer_phone = serializers.CharField(required=False, allow_blank=True)
    customer_notes = serializers.CharField(required=False, allow_blank=True)
    admin_notes = serializers.CharField(required=False, allow_blank=True)
    transaction_id = serializers.CharField(required=False, allow_blank=True)
    payment_details = serializers.DictField(required=False, default=dict)
    item_count = serializers.IntegerField(default=0)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        import random
        import string
        order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        validated_data['order_id'] = uuid.uuid4()
        validated_data['order_number'] = order_number
        validated_data['created_at'] = datetime.utcnow()
        validated_data['updated_at'] = datetime.utcnow()
        return Order.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.updated_at = datetime.utcnow()
        instance.save()
        return instance