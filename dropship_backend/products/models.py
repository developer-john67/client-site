import uuid
from django.db import models


class Category(models.Model):
    category_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True, db_index=True)
    description = models.TextField(blank=True, default='')
    image = models.TextField(blank=True, default='')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=True)
    product_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    product_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    sku = models.CharField(max_length=100, unique=True, db_index=True)

    description = models.TextField(blank=True, default='')
    short_description = models.TextField(blank=True, default='')

    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cost_per_item = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products', db_index=True)
    category_name = models.CharField(max_length=200, blank=True, default='')
    tags = models.JSONField(default=list)

    main_image = models.TextField(blank=True, default='')
    additional_images = models.JSONField(default=list)

    stock = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=5)
    track_quantity = models.BooleanField(default=True)
    continue_selling = models.BooleanField(default=False)

    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, db_index=True)

    meta_title = models.CharField(max_length=200, blank=True, default='')
    meta_description = models.TextField(blank=True, default='')

    specifications = models.JSONField(default=dict)

    created_by = models.UUIDField(null=True, blank=True)
    created_by_name = models.CharField(max_length=200, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    variant_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', db_index=True)
    product_name = models.CharField(max_length=255, blank=True, default='')

    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, unique=True, db_index=True)

    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    stock = models.IntegerField(default=0)

    image = models.TextField(blank=True, default='')

    attributes = models.JSONField(default=dict)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_variants'

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class ProductReview(models.Model):
    review_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', db_index=True)
    user_id = models.UUIDField(db_index=True)
    user_name = models.CharField(max_length=200, blank=True, default='')

    rating = models.IntegerField()
    title = models.CharField(max_length=255, blank=True, default='')
    comment = models.TextField(blank=True, default='')

    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    helpful_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_reviews'

    def __str__(self):
        return f"Review for {self.product.name}"


class ProductView(models.Model):
    view_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='views', db_index=True)
    user_id = models.UUIDField(null=True, blank=True)
    session_id = models.CharField(max_length=200, blank=True, default='')
    ip_address = models.CharField(max_length=50, blank=True, default='')
    viewed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'product_views'

    def __str__(self):
        return f"View: {self.product.name}"