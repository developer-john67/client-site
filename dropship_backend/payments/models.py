"""Payment models for tracking M-Pesa transactions."""

from django.db import models
import uuid


class MpesaTransaction(models.Model):
    """Tracks every STK Push transaction initiated via Daraja API."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUCCESS = 'success', 'Success'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        CANCELLED = 'cancelled', 'Cancelled'
        TIMEOUT = 'timeout', 'Timeout'

    # Internal reference
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Daraja / M-Pesa identifiers
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True,
                                      help_text="Daraja transaction ID returned on STK push initiation")
    checkout_request_id = models.CharField(max_length=100, null=True, blank=True,
                                           help_text="Safaricom checkout request ID")
    mpesa_receipt = models.CharField(max_length=50, null=True, blank=True,
                                     help_text="M-Pesa receipt number (only present on success)")

    # Payment details
    phone_number = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    # Link back to whatever is being paid for (order, subscription, etc.)
    order_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)

    # Raw callback payload from Daraja for debugging/auditing
    callback_data = models.JSONField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['checkout_request_id']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"MpesaTransaction({self.phone_number}, KES {self.amount}, {self.status})"

    @property
    def is_successful(self):
        return self.status == self.Status.SUCCESS

    @property
    def is_pending(self):
        return self.status == self.Status.PENDING