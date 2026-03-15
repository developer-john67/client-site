from django.db import models
from cassandra.cqlengine import columns
from django_cassandra_engine.models import DjangoCassandraModel
import uuid
from datetime import datetime


class User(DjangoCassandraModel):
    """User model for Cassandra"""
    __keyspace__ = 'dropship_keyspace'
    __table_name__ = 'users'

    user_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    username = columns.Text(required=True, index=True)
    email = columns.Text(required=True, index=True)
    password_hash = columns.Text(required=True)
    first_name = columns.Text()
    last_name = columns.Text()
    phone = columns.Text()
    date_of_birth = columns.Date()
    profile_picture = columns.Text()
    user_type = columns.Text(default='customer')

    # Email preferences
    newsletter_subscribed = columns.Boolean(default=False)
    email_notifications = columns.Boolean(default=True)

    # Account status
    email_verified = columns.Boolean(default=False)
    verification_token = columns.Text()
    reset_password_token = columns.Text()
    is_active = columns.Boolean(default=True)
    is_staff = columns.Boolean(default=False)
    is_superuser = columns.Boolean(default=False)

    # Timestamps
    last_login = columns.DateTime()
    last_login_ip = columns.Text()
    created_at = columns.DateTime(default=datetime.utcnow)
    updated_at = columns.DateTime(default=datetime.utcnow)

    class Meta:
        get_pk_field = 'user_id'


class UserAddress(DjangoCassandraModel):
    """User addresses model"""
    __keyspace__ = 'dropship_keyspace'
    __table_name__ = 'user_addresses'

    address_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    user_id = columns.UUID(required=True, index=True)
    address_type = columns.Text(default='shipping')
    is_default = columns.Boolean(default=False)

    # Address details
    first_name = columns.Text(required=True)
    last_name = columns.Text(required=True)
    company = columns.Text()
    address_line1 = columns.Text(required=True)
    address_line2 = columns.Text()
    city = columns.Text(required=True)
    state = columns.Text(required=True)
    postal_code = columns.Text(required=True)
    country = columns.Text(required=True, default='US')
    phone = columns.Text(required=True)

    # Additional info
    delivery_instructions = columns.Text()
    created_at = columns.DateTime(default=datetime.utcnow)
    updated_at = columns.DateTime(default=datetime.utcnow)

    class Meta:
        get_pk_field = 'address_id'


class UserSession(DjangoCassandraModel):
    """User sessions for authentication"""
    __keyspace__ = 'dropship_keyspace'
    __table_name__ = 'user_sessions'

    session_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    user_id = columns.UUID(required=True, index=True)
    token = columns.Text(required=True, index=True)
    ip_address = columns.Text()
    user_agent = columns.Text()
    expires_at = columns.DateTime()
    created_at = columns.DateTime(default=datetime.utcnow)

    class Meta:
        get_pk_field = 'session_id'