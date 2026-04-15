from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import EmailVerification
from .email_service import generate_6digit_code, send_verification_email
import uuid


@api_view(['POST'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def send_verification_code(request):
    """Send a 6-digit verification code to the user's email."""
    email = request.data.get('email', '').strip()
    purpose = request.data.get('purpose', 'email_verify')  # email_verify or password_reset
    user_id = request.data.get('user_id', None)

    if not email:
        return Response(
            {'error': 'Email is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    import re
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
        return Response(
            {'error': 'Please enter a valid email address.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Delete any existing unverified codes for this email
    EmailVerification.objects.filter(email=email, is_verified=False).delete()

    # Generate new 6-digit code
    code = generate_6digit_code()
    expires_at = timezone.now() + timedelta(minutes=15)  # Code valid for 15 minutes

    # Create verification record
    verification = EmailVerification.objects.create(
        verification_id=uuid.uuid4(),
        email=email,
        code=code,
        purpose=purpose,
        user_id=uuid.UUID(user_id) if user_id else None,
        expires_at=expires_at,
        created_at=timezone.now(),
    )

    # Send the verification email
    send_verification_email(email, code, purpose)

    import sys
    print(f"[VERIFICATION] Code sent to {email}: {code}", file=sys.stderr)

    return Response(
        {
            'message': 'Verification code sent to your email.',
            'email': email,
            'expires_in': 900  # 15 minutes in seconds
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def verify_code(request):
    """Verify the 6-digit code entered by the user."""
    email = request.data.get('email', '').strip()
    code = request.data.get('code', '').strip()

    if not email or not code:
        return Response(
            {'error': 'Email and code are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(code) != 6 or not code.isdigit():
        return Response(
            {'error': 'Please enter a valid 6-digit code.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        verification = EmailVerification.objects.get(email=email, code=code, is_verified=False)
    except EmailVerification.DoesNotExist:
        return Response(
            {'error': 'Invalid or expired verification code.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not verification.is_valid():
        verification.delete()
        return Response(
            {'error': 'Verification code has expired. Please request a new one.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Mark verification as verified
    verification.is_verified = True
    verification.updated_at = timezone.now()
    verification.save()
    
    # Update user's email_verified status
    from users.models import User
    User.objects.filter(email=email).update(email_verified=True)

    return Response(
        {
            'message': 'Email verified successfully!',
            'email': email
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def resend_code(request):
    """Resend verification code (rate limited)."""
    email = request.data.get('email', '').strip()

    if not email:
        return Response(
            {'error': 'Email is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check for recent requests (rate limiting)
    recent = EmailVerification.objects.filter(
        email=email,
        created_at__gte=timezone.now() - timedelta(minutes=1)
    ).count()

    if recent >= 3:
        return Response(
            {'error': 'Too many requests. Please wait 1 minute before requesting again.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    # Delete old codes
    EmailVerification.objects.filter(email=email, is_verified=False).delete()

    # Generate new code
    code = generate_6digit_code()
    expires_at = timezone.now() + timedelta(minutes=15)

    verification = EmailVerification.objects.create(
        verification_id=uuid.uuid4(),
        email=email,
        code=code,
        purpose='email_verify',
        expires_at=expires_at,
    )

    send_verification_email(email, code, 'email_verify')

    import sys
    print(f"[VERIFICATION] Code resent to {email}: {code}", file=sys.stderr)

    return Response(
        {'message': 'Verification code sent.'},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def verify_password_reset(request):
    """Verify password reset code and return success."""
    email = request.data.get('email', '').strip()
    code = request.data.get('code', '').strip()

    if not email or not code:
        return Response(
            {'error': 'Email and code are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        verification = EmailVerification.objects.get(
            email=email,
            code=code,
            purpose='password_reset',
            is_verified=False
        )
    except EmailVerification.DoesNotExist:
        return Response(
            {'error': 'Invalid or expired reset code.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not verification.is_valid():
        verification.delete()
        return Response(
            {'error': 'Reset code has expired.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Mark as verified
    verification.is_verified = True
    verification.save()

    return Response(
        {'message': 'Password reset code verified. You can now set a new password.'},
        status=status.HTTP_200_OK
    )
