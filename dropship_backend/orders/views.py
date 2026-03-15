# orders/views.py

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from typing import Optional
import uuid
from datetime import datetime
from .models import Order, OrderItem, OrderStatusHistory
from .serializers import OrderSerializer, OrderItemSerializer, OrderStatusHistorySerializer


def get_user_from_token(request):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    try:
        from users.models import UserSession, User
        sessions = list(UserSession.objects.filter(token=token))
        if not sessions:
            return None
        session = sessions[0]
        if session.expires_at < datetime.utcnow():
            return None
        users = list(User.objects.filter(user_id=session.user_id))
        return users[0] if users else None
    except Exception:
        return None


def is_admin(user) -> bool:
    if user is None:
        return False
    return user.user_type == 'admin' or user.is_staff


# ─── Customer Views ───────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def my_orders(request):
    """Get all orders for current user"""
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    orders = list(Order.objects.filter(user_id=user.user_id))
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def order_detail(request, order_id):
    """Get single order detail"""
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        order = Order.objects.get(order_id=order_id)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

    if str(order.user_id) != str(user.user_id) and not is_admin(user):
        return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    order_items = list(OrderItem.objects.filter(order_id=order_id))
    history = list(OrderStatusHistory.objects.filter(order_id=order_id))

    # Build response dict manually to avoid __setitem__ type issues
    data = OrderSerializer(order).data
    response_data = {
        **data,
        'items': OrderItemSerializer(order_items, many=True).data,
        'status_history': OrderStatusHistorySerializer(history, many=True).data,
    }

    return Response(response_data)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def create_order(request):
    """Create a new order"""
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    # Build data dict cleanly
    data = {
        **request.data,
        'user_id': str(user.user_id),
        'customer_email': getattr(user, 'email', ''),
        'customer_name': f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip(),
        'customer_phone': getattr(user, 'phone', '') or '',
    }

    serializer = OrderSerializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    order = serializer.save()

    # Save order items
    items_data = request.data.get('items', [])
    for item_data in items_data:
        enriched_item = {
            **item_data,
            'order_id': str(order.order_id),
            'order_number': order.order_number,
        }
        item_serializer = OrderItemSerializer(data=enriched_item)
        if item_serializer.is_valid():
            item_serializer.save()

    # Log initial status
    OrderStatusHistory.objects.create(
        history_id=uuid.uuid4(),
        order_id=order.order_id,
        order_number=order.order_number,
        status='pending',
        note='Order created',
        changed_by=user.user_id,
        changed_by_name=f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip(),
        created_at=datetime.utcnow(),
    )

    return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def cancel_order(request, order_id):
    """Cancel an order"""
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        order = Order.objects.get(order_id=order_id)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

    if str(order.user_id) != str(user.user_id) and not is_admin(user):
        return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    if order.status not in ['pending', 'confirmed']:
        return Response(
            {'error': f'Cannot cancel order with status: {order.status}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    order.status = 'cancelled'
    order.updated_at = datetime.utcnow()
    order.save()

    OrderStatusHistory.objects.create(
        history_id=uuid.uuid4(),
        order_id=order.order_id,
        order_number=order.order_number,
        status='cancelled',
        note=request.data.get('reason', 'Cancelled by customer'),
        changed_by=user.user_id,
        changed_by_name=f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip(),
        created_at=datetime.utcnow(),
    )

    return Response(OrderSerializer(order).data)


# ─── Admin Views ──────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def admin_order_list(request):
    """Admin: Get all orders"""
    user = get_user_from_token(request)
    if not is_admin(user):
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

    orders = list(Order.objects.all())

    filter_status = request.query_params.get('status')
    if filter_status:
        orders = [o for o in orders if o.status == filter_status]

    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([permissions.AllowAny])
def admin_update_order_status(request, order_id):
    """Admin: Update order status"""
    user = get_user_from_token(request)
    if not is_admin(user):
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

    try:
        order = Order.objects.get(order_id=order_id)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

    new_status = request.data.get('status')
    valid_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded']
    if not new_status or new_status not in valid_statuses:
        return Response(
            {'error': f'Invalid status. Valid options: {valid_statuses}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    old_status = order.status
    order.status = new_status
    order.updated_at = datetime.utcnow()

    if new_status == 'delivered':
        order.delivered_at = datetime.utcnow()

    tracking_number = request.data.get('tracking_number')
    if tracking_number:
        order.tracking_number = tracking_number

    order.save()

    # user is guaranteed non-None here since is_admin passed
    changed_by_name = f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()

    OrderStatusHistory.objects.create(
        history_id=uuid.uuid4(),
        order_id=order.order_id,
        order_number=order.order_number,
        status=new_status,
        note=request.data.get('note', f'Status changed from {old_status} to {new_status}'),
        changed_by=getattr(user, 'user_id', None),
        changed_by_name=changed_by_name,
        created_at=datetime.utcnow(),
    )

    return Response(OrderSerializer(order).data)


@api_view(['PATCH'])
@permission_classes([permissions.AllowAny])
def admin_update_payment_status(request, order_id):
    """Admin: Update payment status"""
    user = get_user_from_token(request)
    if not is_admin(user):
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

    try:
        order = Order.objects.get(order_id=order_id)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

    new_payment_status = request.data.get('payment_status')
    valid_statuses = ['pending', 'paid', 'failed', 'refunded', 'partially_refunded']
    if not new_payment_status or new_payment_status not in valid_statuses:
        return Response(
            {'error': f'Invalid payment status. Valid options: {valid_statuses}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    order.payment_status = new_payment_status
    order.updated_at = datetime.utcnow()

    if request.data.get('transaction_id'):
        order.transaction_id = request.data.get('transaction_id')

    order.save()

    return Response(OrderSerializer(order).data)