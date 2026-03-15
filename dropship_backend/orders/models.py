from cassandra.cqlengine import columns
from django_cassandra_engine.models import DjangoCassandraModel
import uuid
from datetime import datetime


class Order(DjangoCassandraModel):
    __keyspace__ = 'dropship_keyspace'
    __table_name__ = 'orders'

    order_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    order_number = columns.Text(required=True, index=True)
    user_id = columns.UUID(required=True, index=True)

    status = columns.Text(default='pending')
    payment_status = columns.Text(default='pending')
    payment_method = columns.Text()

    subtotal = columns.Decimal(required=True)
    shipping_cost = columns.Decimal(default=0)
    tax_amount = columns.Decimal(default=0)
    discount_amount = columns.Decimal(default=0)
    total_amount = columns.Decimal(required=True)

    shipping_address = columns.Map(key_type=columns.Text, value_type=columns.Text)
    billing_address = columns.Map(key_type=columns.Text, value_type=columns.Text)

    shipping_method = columns.Text()
    tracking_number = columns.Text()
    estimated_delivery = columns.Date()
    delivered_at = columns.DateTime()

    customer_email = columns.Text()
    customer_name = columns.Text()
    customer_phone = columns.Text()

    customer_notes = columns.Text()
    admin_notes = columns.Text()

    transaction_id = columns.Text()
    payment_details = columns.Map(key_type=columns.Text, value_type=columns.Text)

    item_count = columns.Integer(default=0)
    order_items = columns.List(value_type=columns.Text)  # ✅ renamed from 'items'

    created_at = columns.DateTime(default=datetime.utcnow, index=True)
    updated_at = columns.DateTime(default=datetime.utcnow)

    class Meta:
        get_pk_field = 'order_id'


class OrderItem(DjangoCassandraModel):
    __keyspace__ = 'dropship_keyspace'
    __table_name__ = 'order_items'

    order_item_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    order_id = columns.UUID(required=True, index=True)
    order_number = columns.Text()

    product_id = columns.UUID(index=True)
    product_name = columns.Text(required=True)
    product_sku = columns.Text()
    product_image = columns.Text()

    variant_id = columns.UUID()
    variant_name = columns.Text()
    variant_info = columns.Map(key_type=columns.Text, value_type=columns.Text)

    unit_price = columns.Decimal(required=True)
    quantity = columns.Integer(required=True)
    discount = columns.Decimal(default=0)
    total_price = columns.Decimal(required=True)

    created_at = columns.DateTime(default=datetime.utcnow, index=True)

    class Meta:
        get_pk_field = 'order_item_id'


class OrderStatusHistory(DjangoCassandraModel):
    __keyspace__ = 'dropship_keyspace'
    __table_name__ = 'order_status_history'

    history_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    order_id = columns.UUID(required=True, index=True)
    order_number = columns.Text()

    status = columns.Text(required=True)
    note = columns.Text()
    changed_by = columns.UUID()
    changed_by_name = columns.Text()

    created_at = columns.DateTime(default=datetime.utcnow, index=True)

    class Meta:
        get_pk_field = 'history_id'