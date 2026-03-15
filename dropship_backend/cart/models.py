from cassandra.cqlengine import columns
from django_cassandra_engine.models import DjangoCassandraModel
import uuid
from datetime import datetime


class Cart(DjangoCassandraModel):
    """Shopping cart"""
    __keyspace__ = 'dropship_keyspace'
    __table_name__ = 'carts'

    cart_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    user_id = columns.UUID(index=True)
    session_id = columns.Text(index=True)

    item_count = columns.Integer(default=0)
    subtotal = columns.Decimal(default=0)

    cart_items = columns.List(value_type=columns.Text)  # renamed from 'items'

    created_at = columns.DateTime(default=datetime.utcnow)
    updated_at = columns.DateTime(default=datetime.utcnow)
    expires_at = columns.DateTime()

    class Meta:
        get_pk_field = 'cart_id'


class CartItem(DjangoCassandraModel):
    """Individual cart items"""
    __keyspace__ = 'dropship_keyspace'
    __table_name__ = 'cart_items'

    item_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    cart_id = columns.UUID(required=True, index=True)

    product_id = columns.UUID(required=True, index=True)
    product_name = columns.Text(required=True)
    product_image = columns.Text()
    product_slug = columns.Text()

    variant_id = columns.UUID()
    variant_name = columns.Text()
    variant_info = columns.Map(key_type=columns.Text, value_type=columns.Text)

    unit_price = columns.Decimal(required=True)
    quantity = columns.Integer(required=True, default=1)
    total_price = columns.Decimal()

    added_at = columns.DateTime(default=datetime.utcnow)
    updated_at = columns.DateTime(default=datetime.utcnow)

    class Meta:
        get_pk_field = 'item_id'