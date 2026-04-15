import uuid
from django.db import models
from datetime import datetime


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    order_number = models.CharField(max_length=100, unique=True, db_index=True)
    user_id = models.UUIDField(db_index=True)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, blank=True, default='')

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    shipping_address = models.JSONField(default=dict)
    billing_address = models.JSONField(default=dict)

    shipping_method = models.CharField(max_length=100, blank=True, default='')
    tracking_number = models.CharField(max_length=200, blank=True, default='')
    estimated_delivery = models.DateField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    customer_email = models.EmailField(blank=True, default='')
    customer_name = models.CharField(max_length=200, blank=True, default='')
    customer_phone = models.CharField(max_length=20, blank=True, default='')

    customer_notes = models.TextField(blank=True, default='')
    admin_notes = models.TextField(blank=True, default='')

    transaction_id = models.CharField(max_length=200, blank=True, default='')
    payment_details = models.JSONField(default=dict)

    item_count = models.IntegerField(default=0)
    order_items = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'

    def __str__(self):
        return f"Order {self.order_number}"


class OrderItem(models.Model):
    order_item_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', db_index=True)
    order_number = models.CharField(max_length=100, blank=True, default='')

    product_id = models.UUIDField(db_index=True, null=True, blank=True)
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=100, blank=True, default='')
    product_image = models.TextField(blank=True, default='')

    variant_id = models.UUIDField(null=True, blank=True)
    variant_name = models.CharField(max_length=200, blank=True, default='')
    variant_info = models.JSONField(default=dict)

    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'order_items'

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"


class OrderStatusHistory(models.Model):
    history_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history', db_index=True)
    order_number = models.CharField(max_length=100, blank=True, default='')

    status = models.CharField(max_length=50)
    note = models.TextField(blank=True, default='')
    changed_by = models.UUIDField(null=True, blank=True)
    changed_by_name = models.CharField(max_length=200, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'order_status_history'

    def __str__(self):
        return f"Order {self.order_number} - {self.status}"