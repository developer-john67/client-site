import secrets
import logging
import threading
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


def generate_6digit_code():
    """Generate a random 6-digit code."""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


def send_verification_email_sync(email, code, purpose='email_verify'):
    """Send verification email synchronously."""
    if purpose == 'email_verify':
        subject = 'Verify your Dropship account'
        message = f"""
Welcome to Dropship!

Your verification code is: {code}

Enter this code on the verification page to confirm your email address.

If you didn't create this account, please ignore this email.

Thanks,
Dropship Team
"""
    elif purpose == 'password_reset':
        subject = 'Reset your Dropship password'
        message = f"""
Reset Your Password

Your password reset code is: {code}

Enter this code on the password reset page to create a new password.

If you didn't request a password reset, please ignore this email.

Thanks,
Dropship Team
"""
    else:
        subject = 'Dropship Verification'
        message = f"Your verification code is: {code}"

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        logger.info(f"Verification email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
        print(f"[EMAIL ERROR] {e}")
        return False


def send_verification_email(email, code, purpose='email_verify'):
    """Send verification email asynchronously (non-blocking)."""
    thread = threading.Thread(
        target=send_verification_email_sync,
        args=(email, code, purpose)
    )
    thread.daemon = True
    thread.start()
    return True


def send_welcome_email(email, username):
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
            [email],
            fail_silently=False,
        )
        logger.info(f"Welcome email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send welcome email: {e}")
        return False
