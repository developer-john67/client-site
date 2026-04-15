import uuid
from django.db import models
from datetime import datetime


class Cart(models.Model):
    cart_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    session_id = models.CharField(max_length=200, blank=True, default='', db_index=True)

    item_count = models.IntegerField(default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    cart_items = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'carts'

    def __str__(self):
        return f"Cart {self.cart_id}"


class CartItem(models.Model):
    item_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', db_index=True)

    product_id = models.UUIDField(db_index=True)
    product_name = models.CharField(max_length=255)
    product_image = models.TextField(blank=True, default='')
    product_slug = models.SlugField(max_length=255, blank=True, default='')

    variant_id = models.UUIDField(null=True, blank=True)
    variant_name = models.CharField(max_length=200, blank=True, default='')
    variant_info = models.JSONField(default=dict)

    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cart_items'

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"