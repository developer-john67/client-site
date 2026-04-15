# cart/serializers.py

from rest_framework import serializers
from django.utils import timezone
import uuid
from .models import Cart, CartItem


class CartItemSerializer(serializers.Serializer):
    item_id = serializers.UUIDField(read_only=True)
    cart_id = serializers.UUIDField(required=True)
    product_id = serializers.UUIDField(required=True)
    product_name = serializers.CharField(required=True)
    product_image = serializers.CharField(required=False, allow_blank=True)
    product_slug = serializers.CharField(required=False, allow_blank=True)
    variant_id = serializers.UUIDField(required=False, allow_null=True)
    variant_name = serializers.CharField(required=False, allow_blank=True)
    variant_info = serializers.DictField(required=False, default=dict)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    quantity = serializers.IntegerField(default=1, min_value=1)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    added_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        validated_data['item_id'] = uuid.uuid4()
        validated_data['total_price'] = (
            validated_data['unit_price'] * validated_data['quantity']
        )
        validated_data['added_at'] = timezone.now()
        validated_data['updated_at'] = timezone.now()
        return CartItem.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.total_price = instance.unit_price * instance.quantity
        instance.updated_at = timezone.now()
        instance.save()
        return instance


class CartSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField(read_only=True)
    user_id = serializers.UUIDField(required=False, allow_null=True)
    session_id = serializers.CharField(required=False, allow_blank=True)
    item_count = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        validated_data['cart_id'] = uuid.uuid4()
        validated_data['item_count'] = 0
        validated_data['subtotal'] = 0
        validated_data['created_at'] = timezone.now()
        validated_data['updated_at'] = timezone.now()
        return Cart.objects.create(**validated_data)