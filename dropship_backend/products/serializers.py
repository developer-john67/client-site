from rest_framework import serializers
import uuid
from datetime import datetime
from .models import Category, Product, ProductVariant, ProductReview

MEDIA_BASE_URL = 'http://localhost:8000/media/'


class CategorySerializer(serializers.Serializer):
    category_id  = serializers.UUIDField(read_only=True)
    name         = serializers.CharField(required=True)
    slug         = serializers.CharField(required=True)
    description  = serializers.CharField(required=False, allow_blank=True)
    image        = serializers.SerializerMethodField()
    parent_id    = serializers.UUIDField(required=False, allow_null=True)
    is_active    = serializers.BooleanField(default=True)
    product_count= serializers.IntegerField(read_only=True)
    created_at   = serializers.DateTimeField(read_only=True)
    updated_at   = serializers.DateTimeField(read_only=True)

    def get_image(self, obj):
        if obj.image:
            if obj.image.startswith('http'):
                return obj.image
            return f"{MEDIA_BASE_URL}{obj.image}"
        return None

    def create(self, validated_data):
        validated_data['category_id'] = uuid.uuid4()
        validated_data['created_at']  = datetime.now()
        validated_data['updated_at']  = datetime.now()
        return Category.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.updated_at = datetime.now()
        instance.save()
        return instance


class ProductVariantSerializer(serializers.Serializer):
    variant_id       = serializers.UUIDField(read_only=True)
    product_id       = serializers.UUIDField(required=True)
    name             = serializers.CharField(required=True)
    sku              = serializers.CharField(required=True)
    price_adjustment = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock            = serializers.IntegerField(default=0)
    image            = serializers.SerializerMethodField()
    attributes       = serializers.DictField(child=serializers.CharField(), required=False)
    is_active        = serializers.BooleanField(default=True)

    def get_image(self, obj):
        if obj.image:
            if obj.image.startswith('http'):
                return obj.image
            return f"{MEDIA_BASE_URL}{obj.image}"
        return None

    def create(self, validated_data):
        validated_data['variant_id']  = uuid.uuid4()
        validated_data['created_at']  = datetime.now()
        validated_data['updated_at']  = datetime.now()
        return ProductVariant.objects.create(**validated_data)


class ProductSerializer(serializers.Serializer):
    product_id        = serializers.UUIDField(read_only=True)
    name              = serializers.CharField(required=True)
    slug              = serializers.CharField(required=True)
    sku               = serializers.CharField(required=True)
    description       = serializers.CharField(required=False, allow_blank=True)
    short_description = serializers.CharField(required=False, allow_blank=True)
    price             = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    compare_at_price  = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    cost_per_item     = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    category_id       = serializers.UUIDField(required=True)
    category_name     = serializers.CharField(read_only=True)
    tags              = serializers.ListField(child=serializers.CharField(), required=False)

    # ← Returns full URL instead of bare filename
    main_image        = serializers.SerializerMethodField()
    image_url         = serializers.SerializerMethodField()  # alias for frontend compatibility
    additional_images = serializers.ListField(child=serializers.CharField(), required=False)

    stock               = serializers.IntegerField(default=0)
    low_stock_threshold = serializers.IntegerField(default=5)
    track_quantity      = serializers.BooleanField(default=True)
    continue_selling    = serializers.BooleanField(default=False)
    is_available        = serializers.BooleanField(default=True)
    is_featured         = serializers.BooleanField(default=False)
    specifications      = serializers.DictField(child=serializers.CharField(), required=False)
    created_at          = serializers.DateTimeField(read_only=True)
    updated_at          = serializers.DateTimeField(read_only=True)

    def get_main_image(self, obj):
        if obj.main_image:
            if obj.main_image.startswith('http'):
                return obj.main_image
            if obj.main_image.startswith('/'):
                return f"http://localhost:8000{obj.main_image}"
            return f"{MEDIA_BASE_URL}{obj.main_image}"
        return None

    # Alias so frontend can use either product.main_image or product.image_url
    def get_image_url(self, obj):
        return self.get_main_image(obj)

    def create(self, validated_data):
        validated_data['product_id'] = uuid.uuid4()
        validated_data['created_at'] = datetime.now()
        validated_data['updated_at'] = datetime.now()
        return Product.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.updated_at = datetime.now()
        instance.save()
        return instance


class ProductReviewSerializer(serializers.Serializer):
    review_id             = serializers.UUIDField(read_only=True)
    product_id            = serializers.UUIDField(required=True)
    user_id               = serializers.UUIDField(required=True)
    user_name             = serializers.CharField(read_only=True)
    rating                = serializers.IntegerField(required=True, min_value=1, max_value=5)
    title                 = serializers.CharField(required=False, allow_blank=True)
    comment               = serializers.CharField(required=False, allow_blank=True)
    is_verified_purchase  = serializers.BooleanField(read_only=True)
    is_approved           = serializers.BooleanField(read_only=True)
    helpful_count         = serializers.IntegerField(read_only=True)
    created_at            = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        validated_data['review_id']  = uuid.uuid4()
        validated_data['created_at'] = datetime.now()
        validated_data['updated_at'] = datetime.now()
        return ProductReview.objects.create(**validated_data)