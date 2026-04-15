import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta


class EmailVerification(models.Model):
    """Model to store email verification codes"""
    verification_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    email = models.EmailField(db_index=True)
    code = models.CharField(max_length=6, db_index=True)
    purpose = models.CharField(max_length=50, default='email_verify')  # email_verify, password_reset
    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    is_verified = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'email_verifications'
        ordering = ['-created_at']

    def is_valid(self):
        """Check if the verification code is still valid"""
        return not self.is_verified and timezone.now() < self.expires_at

    def __str__(self):
        return f"{self.email} - {self.purpose}"
