import uuid
from cassandra.cqlengine import columns
from django_cassandra_engine.models import DjangoCassandraModel


class Product(DjangoCassandraModel):
    """Product model stored in CassandraDB."""

    class Meta:
        get_pk_field = 'product_id'
        app_label = 'shop'

    product_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    name = columns.Text(required=True, index=True)
    description = columns.Text(default='')
    price = columns.Decimal(required=True)
    category = columns.Text(required=True, index=True)
    stock_quantity = columns.Integer(default=0)
    image_url = columns.Text(default='')      # Store image path/URL as text
    is_active = columns.Boolean(default=True)
    created_at = columns.DateTime()
    updated_at = columns.DateTime()

    def __str__(self):
        return self.name