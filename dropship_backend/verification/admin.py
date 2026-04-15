from django.contrib import admin
from .models import EmailVerification


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ['email', 'code', 'purpose', 'is_verified', 'expires_at', 'created_at']
    list_filter = ['purpose', 'is_verified']
    search_fields = ['email']
    readonly_fields = ['verification_id', 'created_at', 'updated_at']
