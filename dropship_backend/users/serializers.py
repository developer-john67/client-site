from rest_framework import serializers
import uuid
from datetime import datetime
from .models import User, UserAddress
import hashlib
import os

class UserSerializer(serializers.Serializer):
    user_id = serializers.UUIDField(read_only=True)
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    profile_picture = serializers.CharField(required=False, allow_blank=True)
    user_type = serializers.CharField(default='customer')
    newsletter_subscribed = serializers.BooleanField(default=False)
    email_notifications = serializers.BooleanField(default=True)
    email_verified = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    
    def create(self, validated_data):
        # Hash password
        password = validated_data.pop('password')
        salt = os.urandom(32).hex()
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        
        validated_data['user_id'] = uuid.uuid4()
        validated_data['password_hash'] = f"{salt}${password_hash}"
        validated_data['created_at'] = datetime.now()
        validated_data['updated_at'] = datetime.now()
        validated_data['is_active'] = True
        
        return User.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            salt = os.urandom(32).hex()
            password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            instance.password_hash = f"{salt}${password_hash}"
        
        for key, value in validated_data.items():
            setattr(instance, key, value)
        
        instance.updated_at = datetime.now()
        instance.save()
        return instance

class UserAddressSerializer(serializers.Serializer):
    address_id = serializers.UUIDField(read_only=True)
    user_id = serializers.UUIDField(required=True)
    address_type = serializers.CharField(default='shipping')
    is_default = serializers.BooleanField(default=False)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    company = serializers.CharField(required=False, allow_blank=True)
    address_line1 = serializers.CharField(required=True)
    address_line2 = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=True)
    state = serializers.CharField(required=True)
    postal_code = serializers.CharField(required=True)
    country = serializers.CharField(default='US')
    phone = serializers.CharField(required=True)
    delivery_instructions = serializers.CharField(required=False, allow_blank=True)
    
    def create(self, validated_data):
        validated_data['address_id'] = uuid.uuid4()
        validated_data['created_at'] = datetime.now()
        validated_data['updated_at'] = datetime.now()
        
        # If this is default, unset other defaults
        if validated_data.get('is_default'):
            addresses = UserAddress.objects.filter(
                user_id=validated_data['user_id'],
                address_type=validated_data['address_type']
            )
            for addr in addresses:
                addr.is_default = False
                addr.save()
        
        return UserAddress.objects.create(**validated_data)