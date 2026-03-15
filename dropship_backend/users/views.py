# users/views.py

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from .models import User, UserAddress, UserSession
from .serializers import UserSerializer, UserAddressSerializer


def hash_password(password):
    import os
    salt = os.urandom(32).hex()
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${password_hash}"


def verify_password(password, stored_hash):
    salt, hashed = stored_hash.split('$', 1)
    return hashlib.sha256((password + salt).encode()).hexdigest() == hashed


def get_user_from_token(request):
    """Extract user from session token in Authorization header"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    try:
        sessions = list(UserSession.objects.filter(token=token))
        if not sessions:
            return None
        session = sessions[0]
        if session.expires_at < datetime.utcnow():
            session.delete()
            return None
        users = list(User.objects.filter(user_id=session.user_id))
        return users[0] if users else None
    except Exception:
        return None


# ─── Auth ────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    """Register a new user"""
    username = request.data.get('username', '').strip()
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '')

    # Validate required fields
    if not username:
        return Response({'error': 'Full name is required.'}, status=status.HTTP_400_BAD_REQUEST)
    if not email:
        return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
    if not password:
        return Response({'error': 'Password is required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Validate email format
    import re
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
        return Response({'error': 'Please enter a valid email address.'}, status=status.HTTP_400_BAD_REQUEST)

    # Validate password length
    if len(password) < 8:
        return Response({'error': 'Password must be at least 8 characters.'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if email already exists
    if list(User.objects.filter(email=email)):
        return Response({'error': 'Email already registered.'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if username already exists
    if list(User.objects.filter(username=username)):
        return Response({'error': 'Username already taken.'}, status=status.HTTP_400_BAD_REQUEST)

    # Create user
    user = User.objects.create(
        user_id=uuid.uuid4(),
        username=username,
        email=email,
        password_hash=hash_password(password),
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    return Response({
        'message': 'Registration successful.',
        'user_id': str(user.user_id),
        'email': user.email,
        'username': user.username,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    """Login and return session token"""
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '')

    if not email or not password:
        return Response({'error': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        users = list(User.objects.filter(email=email))
        if not users:
            return Response({'error': 'Invalid email or password.'}, status=status.HTTP_401_UNAUTHORIZED)

        user = users[0]

        if not user.is_active:
            return Response({'error': 'Account is disabled.'}, status=status.HTTP_403_FORBIDDEN)

        if not verify_password(password, user.password_hash):
            return Response({'error': 'Invalid email or password.'}, status=status.HTTP_401_UNAUTHORIZED)

        # Create session token
        token = secrets.token_hex(32)
        expires_at = datetime.utcnow() + timedelta(days=7)

        UserSession.objects.create(
            session_id=uuid.uuid4(),
            user_id=user.user_id,
            token=token,
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            expires_at=expires_at,
            created_at=datetime.utcnow(),
        )

        # Update last login
        user.last_login = datetime.utcnow()
        user.last_login_ip = request.META.get('REMOTE_ADDR', '')
        user.save()

        return Response({
            'token': token,
            'expires_at': expires_at.isoformat(),
            'user': {
                'user_id': str(user.user_id),
                'email': user.email,
                'username': user.username,
                'first_name': getattr(user, 'first_name', ''),
                'last_name': getattr(user, 'last_name', ''),
                'user_type': getattr(user, 'user_type', 'customer'),
            }
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def logout(request):
    """Invalidate session token"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response({'error': 'No token provided.'}, status=status.HTTP_400_BAD_REQUEST)

    token = auth_header.split(' ')[1]
    try:
        sessions = list(UserSession.objects.filter(token=token))
        for session in sessions:
            session.delete()
        return Response({'message': 'Logged out successfully.'})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─── Profile ─────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_profile(request):
    """Get current user profile"""
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized. Please log in.'}, status=status.HTTP_401_UNAUTHORIZED)

    serializer = UserSerializer(user)
    return Response(serializer.data)


@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.AllowAny])
def update_profile(request):
    """Update current user profile"""
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized. Please log in.'}, status=status.HTTP_401_UNAUTHORIZED)

    data = request.data.copy()
    data.pop('email', None)
    data.pop('username', None)
    data.pop('password', None)

    serializer = UserSerializer(user, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def change_password(request):
    """Change user password"""
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized. Please log in.'}, status=status.HTTP_401_UNAUTHORIZED)

    old_password = request.data.get('old_password', '')
    new_password = request.data.get('new_password', '')

    if not old_password or not new_password:
        return Response({'error': 'old_password and new_password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    if not verify_password(old_password, user.password_hash):
        return Response({'error': 'Current password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

    if len(new_password) < 8:
        return Response({'error': 'New password must be at least 8 characters.'}, status=status.HTTP_400_BAD_REQUEST)

    user.password_hash = hash_password(new_password)
    user.updated_at = datetime.utcnow()
    user.save()

    return Response({'message': 'Password changed successfully.'})


# ─── Addresses ───────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def address_list(request):
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized. Please log in.'}, status=status.HTTP_401_UNAUTHORIZED)

    addresses = list(UserAddress.objects.filter(user_id=user.user_id))
    serializer = UserAddressSerializer(addresses, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def create_address(request):
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized. Please log in.'}, status=status.HTTP_401_UNAUTHORIZED)

    data = request.data.copy()
    data['user_id'] = str(user.user_id)

    serializer = UserAddressSerializer(data=data)
    if serializer.is_valid():
        address = serializer.save()
        return Response(UserAddressSerializer(address).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def address_detail(request, address_id):
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized. Please log in.'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        address = UserAddress.objects.get(address_id=address_id)
        if address.user_id != user.user_id:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(UserAddressSerializer(address).data)
    except UserAddress.DoesNotExist:
        return Response({'error': 'Address not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.AllowAny])
def update_address(request, address_id):
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized. Please log in.'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        address = UserAddress.objects.get(address_id=address_id)
        if address.user_id != user.user_id:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserAddressSerializer(address, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except UserAddress.DoesNotExist:
        return Response({'error': 'Address not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([permissions.AllowAny])
def delete_address(request, address_id):
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized. Please log in.'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        address = UserAddress.objects.get(address_id=address_id)
        if address.user_id != user.user_id:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        address.delete()
        return Response({'message': 'Address deleted.'}, status=status.HTTP_204_NO_CONTENT)
    except UserAddress.DoesNotExist:
        return Response({'error': 'Address not found.'}, status=status.HTTP_404_NOT_FOUND)