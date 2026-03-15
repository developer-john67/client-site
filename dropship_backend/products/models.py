from cassandra.cqlengine import columns
from django_cassandra_engine.models import DjangoCassandraModel
import uuid


class Category(DjangoCassandraModel):
    """Product categories"""
    __keyspace__ = 'dropship_keyspace'
    __table_name__ = 'categories'

    category_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    name = columns.Text(required=True, index=True)
    slug = columns.Text(required=True, index=True)
    description = columns.Text()
    image = columns.Text()
    parent_id = columns.UUID()
    is_active = columns.Boolean(default=True)
    product_count = columns.Integer(default=0)
    created_at = columns.DateTime()
    updated_at = columns.DateTime()

    class Meta:
        get_pk_field = 'category_id'


class Product(DjangoCassandraModel):
    """Main product model"""
    __keyspace__ = 'dropship_keyspace'
    __table_name__ = 'products'

    product_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    name = columns.Text(required=True)
    slug = columns.Text(required=True, index=True)
    sku = columns.Text(required=True, index=True)

    # Description
    description = columns.Text()
    short_description = columns.Text()

    # Pricing
    price = columns.Decimal(required=True)
    compare_at_price = columns.Decimal()
    cost_per_item = columns.Decimal()

    # Categorization
    category_id = columns.UUID(required=True, index=True)
    category_name = columns.Text()
    tags = columns.List(value_type=columns.Text)

    # Media
    main_image = columns.Text()
    additional_images = columns.List(value_type=columns.Text)

    # Inventory
    stock = columns.Integer(default=0)
    low_stock_threshold = columns.Integer(default=5)
    track_quantity = columns.Boolean(default=True)
    continue_selling = columns.Boolean(default=False)

    # Status
    is_available = columns.Boolean(default=True)
    is_featured = columns.Boolean(default=False, index=True)

    # SEO
    meta_title = columns.Text()
    meta_description = columns.Text()

    # Specifications
    specifications = columns.Map(key_type=columns.Text, value_type=columns.Text)

    # Vendor info
    created_by = columns.UUID()
    created_by_name = columns.Text()

    # Timestamps
    created_at = columns.DateTime(index=True)
    updated_at = columns.DateTime()

    class Meta:
        get_pk_field = 'product_id'


class ProductVariant(DjangoCassandraModel):
    """Product variants (size, color, etc.)"""
    __keyspace__ = 'dropship_keyspace'
    __table_name__ = 'product_variants'

    variant_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    product_id = columns.UUID(required=True, index=True)
    product_name = columns.Text()

    name = columns.Text(required=True)
    sku = columns.Text(required=True, index=True)

    # Pricing
    price_adjustment = columns.Decimal(default=0)

    # Inventory
    stock = columns.Integer(default=0)

    # Media
    image = columns.Text()

    # Attributes
    attributes = columns.Map(key_type=columns.Text, value_type=columns.Text)

    # Status
    is_active = columns.Boolean(default=True)

    created_at = columns.DateTime()
    updated_at = columns.DateTime()

    class Meta:
        get_pk_field = 'variant_id'


class ProductReview(DjangoCassandraModel):
    """Product reviews"""
    __keyspace__ = 'dropship_keyspace'
    __table_name__ = 'product_reviews'

    review_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    product_id = columns.UUID(required=True, index=True)
    user_id = columns.UUID(required=True, index=True)
    user_name = columns.Text()

    rating = columns.Integer(required=True)
    title = columns.Text()
    comment = columns.Text()

    is_verified_purchase = columns.Boolean(default=False)
    is_approved = columns.Boolean(default=False)
    helpful_count = columns.Integer(default=0)

    created_at = columns.DateTime(index=True)
    updated_at = columns.DateTime()

    class Meta:
        get_pk_field = 'review_id'


class ProductView(DjangoCassandraModel):
    """Track product views for analytics"""
    __keyspace__ = 'dropship_keyspace'
    __table_name__ = 'product_views'

    view_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    product_id = columns.UUID(required=True, index=True)
    user_id = columns.UUID()
    session_id = columns.Text()
    ip_address = columns.Text()
    viewed_at = columns.DateTime(index=True)

    class Meta:
        get_pk_field = 'view_id'