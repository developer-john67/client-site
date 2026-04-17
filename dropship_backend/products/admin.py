from django.contrib import admin
from .models import Category, Product, ProductVariant, ProductReview


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'product_count', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'price', 'stock', 'is_available', 'is_featured', 'created_at')
    list_filter = ('is_available', 'is_featured', 'category')
    search_fields = ('name', 'sku', 'description')
    readonly_fields = ('product_id', 'created_at', 'updated_at')
    list_editable = ('stock', 'is_available', 'is_featured')


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('name', 'product', 'sku', 'price_adjustment', 'stock')
    list_filter = ('product',)
    search_fields = ('name', 'sku')


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('title', 'product', 'rating', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'rating')
    search_fields = ('title', 'user_name')
    readonly_fields = ('review_id', 'created_at', 'updated_at')