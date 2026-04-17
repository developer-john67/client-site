# users/models.py — Complete fixed version

import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


# ─── Custom User Manager ──────────────────────────────────────────────────────

class UserManager(BaseUserManager):

    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required.')
        if not username:
            raise ValueError('Username is required.')

        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        user = self.model(
            email=email,
            username=username,
            **extra_fields
        )
        user.set_password(password)  # ✅ Hashes password properly
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('email_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, username, password, **extra_fields)


# ─── User Model ───────────────────────────────────────────────────────────────

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model that works with Django admin and createsuperuser.
    Inherits AbstractBaseUser and PermissionsMixin for full auth support.
    """

    user_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        db_index=True
    )
    email = models.EmailField(
        unique=True,
        db_index=True
    )

    # ✅ AbstractBaseUser provides password field and hashing
    # Do NOT add password_hash manually — use set_password() instead

    first_name = models.CharField(max_length=100, blank=True, default='')
    last_name = models.CharField(max_length=100, blank=True, default='')
    phone = models.CharField(max_length=20, blank=True, default='')
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.TextField(blank=True, default='')
    user_type = models.CharField(max_length=50, default='customer')

    newsletter_subscribed = models.BooleanField(default=False)
    email_notifications = models.BooleanField(default=True)

    email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=255, blank=True, default='')
    reset_password_token = models.CharField(max_length=255, blank=True, default='')

    # ✅ These are provided by AbstractBaseUser + PermissionsMixin
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    # is_superuser is provided by PermissionsMixin

    last_login_ip = models.CharField(max_length=50, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ✅ Required for AbstractBaseUser
    USERNAME_FIELD = 'email'           # Login with email
    REQUIRED_FIELDS = ['username']     # Required when creating superuser

    objects = UserManager()

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.email} ({self.username})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    def get_short_name(self):
        return self.first_name or self.username


# ─── UserAddress ──────────────────────────────────────────────────────────────

class UserAddress(models.Model):
    address_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses',
        db_index=True
    )
    address_type = models.CharField(max_length=50, default='shipping')
    is_default = models.BooleanField(default=False)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    company = models.CharField(max_length=200, blank=True, default='')
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, default='')
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=50, default='KE')
    phone = models.CharField(max_length=20)
    delivery_instructions = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_addresses'

    def __str__(self):
        return f"{self.first_name} {self.last_name} — {self.city}"


# ─── UserSession ──────────────────────────────────────────────────────────────

class UserSession(models.Model):
    session_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions',
        db_index=True
    )
    token = models.CharField(max_length=500, unique=True, db_index=True)
    ip_address = models.CharField(max_length=50, blank=True, default='')
    user_agent = models.TextField(blank=True, default='')
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_sessions'

    def __str__(self):
        return f"{self.user.email} — {self.token[:20]}..."