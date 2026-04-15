# users/email_service.py

import secrets
import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def generate_verification_token():
    """Generate a random verification token."""
    return secrets.token_urlsafe(32)


def send_verification_email(user_email, token):
    """Send verification email to user."""
    import sys
    print("=" * 50, file=sys.stderr)
    print(f"[EMAIL] Sending to: {user_email}", file=sys.stderr)
    print(f"[EMAIL] Token: {token}", file=sys.stderr)
    
    verification_url = f"{settings.FRONTEND_URL}/html/verify-email.html?token={token}"
    print(f"[EMAIL] URL: {verification_url}", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    
    subject = 'Verify your Dropship account'
    message = f"""
    Welcome to Dropship!
    
    Please verify your email address by clicking the link below:
    {verification_url}
    
    If you didn't create this account, please ignore this email.
    
    Thanks,
    Dropship Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
        logger.info(f"Verification email sent to {user_email}")
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}", file=sys.stderr)
        logger.error(f"Failed to send verification email: {e}")
        return False


def send_welcome_email(user_email, username):
    """Send welcome email after email verification."""
    subject = 'Welcome to Dropship!'
    message = f"""
    Hi {username},
    
    Your email has been verified successfully!
    
    You can now:
    - Browse products
    - Add items to your cart
    - Complete purchases
    
    Happy shopping!
    
    Thanks,
    Dropship Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send welcome email: {e}")
        return False
