# orders/views.py

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from typing import Optional
import uuid
from datetime import datetime
from .models import Order, OrderItem, OrderStatusHistory
from .serializers import OrderSerializer, OrderItemSerializer, OrderStatusHistorySerializer
from dropship_backend.security import sanitize_integer, sanitize_string


def get_user_from_token(request):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.replace('Bearer ', '')
    
    try:
        from users.models import UserSession
        session = UserSession.objects.filter(token=token).first()
        
        if not session:
            return None
            
        from django.utils import timezone
        if session.expires_at < timezone.now():
            return None
            
        return session.user
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
    import sys
    print(f"[DEBUG] Authorization header: {request.headers.get('Authorization', 'NOT FOUND')}", file=sys.stderr)
    user = get_user_from_token(request)
    print(f"[DEBUG] User from token: {user}", file=sys.stderr)
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


import logging
logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def initiate_mpesa_payment(request):
    """Initiate M-Pesa STK Push payment for an order using Daraja API."""
    import sys
    print(f"[MPESA VIEW] Request received: phone={request.data.get('phone')}, amount={request.data.get('amount')}, order_id={request.data.get('order_id')}", file=sys.stderr, flush=True)
    
    phone = sanitize_string(request.data.get('phone', ''))
    amount = sanitize_integer(request.data.get('amount'), min_val=1)
    order_id = sanitize_string(request.data.get('order_id', ''))
    
    if not phone:
        return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not amount or amount <= 0:
        return Response({'error': 'Valid amount is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not order_id:
        return Response({'error': 'Order ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        import sys
        print(f"[MPESA VIEW] Starting...", file=sys.stderr, flush=True)
        
        from payments.mpesa import initiate_mpesa_payment as daraja_initiate_payment
        print(f"[MPESA VIEW] Imported successfully", file=sys.stderr, flush=True)
        
        result = daraja_initiate_payment(order_id, phone, amount)
        
        print(f"[MPESA VIEW] Daraja result: {result}", file=sys.stderr, flush=True)
        
        if result.get('success'):
            return Response({
                'success': True,
                'message': 'STK push sent to your phone',
                'transaction_id': result.get('transaction_id'),
                'checkout_request_id': result.get('checkout_request_id'),
                'phone_number': result.get('phone_number'),
                'amount': result.get('amount'),
                'status': result.get('status', 'pending')
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'Payment initiation failed')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        import sys
        print(f"[MPESA VIEW] ERROR: {str(e)}", file=sys.stderr, flush=True)
        logger.error(f"M-Pesa payment error: {str(e)}")
        return Response({'error': 'Payment service unavailable'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def check_mpesa_payment(request):
    """Check M-Pesa payment status using Daraja API."""
    checkout_request_id = sanitize_string(request.data.get('transaction_id', '')) or sanitize_string(request.data.get('checkout_request_id', ''))
    
    if not checkout_request_id:
        return Response({'error': 'Transaction ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        from payments.mpesa import check_payment_status
        result = check_payment_status(checkout_request_id)
        
        return Response({
            'success': result.get('success', False),
            'payment_status': result.get('status', 'unknown'),
            'checkout_request_id': checkout_request_id,
            'transaction_id': result.get('transaction_id'),
            'amount': result.get('amount'),
            'phone': result.get('phone'),
            'mpesa_receipt': result.get('mpesa_receipt'),
            'created_at': result.get('created_at')
        })
        
    except Exception as e:
        logger.error(f"M-Pesa query error: {str(e)}")
        return Response({'error': 'Payment status check failed'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def daraja_webhook(request):
    """Handle Daraja webhook for payment updates."""
    try:
        data = request.data
        
        transaction_id = data.get('transaction_id')
        status = data.get('status')
        amount = data.get('amount')
        phone = data.get('phone')
        mpesa_receipt = data.get('mpesa_receipt')
        reference = data.get('reference')
        
        if transaction_id and status == 'success':
            try:
                order = Order.objects.get(order_id=reference)
                order.payment_status = 'paid'
                order.transaction_id = mpesa_receipt or transaction_id
                order.payment_details = {
                    'daraja_transaction_id': transaction_id,
                    'mpesa_receipt': mpesa_receipt,
                    'phone': phone,
                    'amount': amount,
                }
                order.save()
                
                OrderStatusHistory.objects.create(
                    history_id=uuid.uuid4(),
                    order_id=order.order_id,
                    order_number=order.order_number,
                    status='paid',
                    note=f'Payment received via Daraja. Receipt: {mpesa_receipt}',
                    created_at=datetime.utcnow(),
                )
            except Order.DoesNotExist:
                logger.error(f"Order not found for webhook: {reference}")
        
        return Response({'success': True})
        
    except Exception as e:
        logger.error(f"Daraja webhook error: {str(e)}")
        return Response({'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def mpesa_callback(request):
    """Handle M-Pesa payment callback (webhook)."""
    try:
        data = request.data
        
        result_code = data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
        result_desc = data.get('Body', {}).get('stkCallback', {}).get('ResultDesc')
        checkout_request_id = data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
        merchant_request_id = data.get('Body', {}).get('stkCallback', {}).get('MerchantRequestID')
        
        callback_items = data.get('Body', {}).get('stkCallback', {}).get('CallbackMetadata', {}).get('Item', [])
        
        mpesa_receipt_number = ''
        phone_number = ''
        amount = ''
        transaction_date = ''
        
        for item in callback_items:
            if item.get('Name') == 'MpesaReceiptNumber':
                mpesa_receipt_number = item.get('Value', '')
            elif item.get('Name') == 'PhoneNumber':
                phone_number = item.get('Value', '')
            elif item.get('Name') == 'Amount':
                amount = item.get('Value', '')
            elif item.get('Name') == 'TransactionDate':
                transaction_date = item.get('Value', '')
        
        if result_code == 0:
            account_reference = data.get('Body', {}).get('stkCallback', {}).get('AccountReference', '')
            
            try:
                order = Order.objects.get(order_id=account_reference)
                order.payment_status = 'paid'
                order.transaction_id = mpesa_receipt_number
                order.payment_details = {
                    'mpesa_receipt_number': mpesa_receipt_number,
                    'phone_number': phone_number,
                    'amount': amount,
                    'transaction_date': transaction_date,
                    'checkout_request_id': checkout_request_id,
                    'merchant_request_id': merchant_request_id
                }
                order.save()
                
                OrderStatusHistory.objects.create(
                    history_id=uuid.uuid4(),
                    order_id=order.order_id,
                    order_number=order.order_number,
                    status='paid',
                    note=f'Payment received via M-Pesa. Receipt: {mpesa_receipt_number}',
                    created_at=datetime.utcnow(),
                )
                
            except Order.DoesNotExist:
                logger.error(f"Order not found for callback: {account_reference}")
        
        return Response({'success': True})
        
    except Exception as e:
        logger.error(f"M-Pesa callback error: {str(e)}")
        return Response({'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)