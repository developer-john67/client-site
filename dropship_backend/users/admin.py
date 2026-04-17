from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserAddress, UserSession


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'is_active', 'is_staff', 'email_verified', 'created_at')
    list_filter = ('is_active', 'is_staff', 'email_verified', 'user_type')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    readonly_fields = ('user_id', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('user_id', 'email', 'password')}),
        ('Personal info', {'fields': ('username', 'first_name', 'last_name', 'phone', 'date_of_birth', 'profile_picture')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_type', 'groups', 'user_permissions')}),
        ('Verification', {'fields': ('email_verified', 'verification_token')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'address_type', 'is_default', 'city', 'created_at')  # removed 'label'
    list_filter = ('address_type', 'is_default')
    search_fields = ('user__email', 'city', 'first_name', 'last_name')
    readonly_fields = ('address_id', 'created_at', 'updated_at')


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_agent', 'ip_address', 'expires_at', 'created_at')  # replaced 'device_info'/'is_active'
    list_filter = ('created_at',)  # removed 'is_active'
    search_fields = ('user__email', 'ip_address', 'user_agent')
    readonly_fields = ('session_id', 'created_at', 'expires_at')