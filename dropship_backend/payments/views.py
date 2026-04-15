"""Payment views — STK Push initiation, Daraja webhook callback, status polling."""

import json
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from payments.models import MpesaTransaction

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def initiate_payment(request):
    """Initiate M-Pesa STK Push payment."""
    phone_number = request.data.get('phone_number', '').strip()
    amount = request.data.get('amount')
    order_id = request.data.get('order_id')

    if not phone_number:
        return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)

    if not amount:
        return Response({'error': 'Amount is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return Response({'error': 'Invalid amount'}, status=status.HTTP_400_BAD_REQUEST)

    if amount < 1:
        return Response({'error': 'Amount must be at least 1 KES'}, status=status.HTTP_400_BAD_REQUEST)

    from payments.mpesa import initiate_mpesa_payment
    result = initiate_mpesa_payment(order_id, phone_number, amount)

    if result.get('success'):
        return Response(result, status=status.HTTP_200_OK)
    else:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def payment_callback(request):
    """
    Handle payment webhook callback from Daraja.

    Daraja posts here when a transaction status changes (success, failed, cancelled).
    Always return 200 so Daraja doesn't keep retrying.
    """
    data = request.data
    logger.info(f"[MPESA] Callback received: {json.dumps(data)}")

    transaction_id = data.get('transaction_id') or data.get('checkout_request_id')
    incoming_status = data.get('status')
    mpesa_receipt = data.get('mpesa_receipt') or ''
    reference = data.get('reference')

    if not transaction_id:
        logger.warning("[MPESA] Callback missing transaction_id — ignoring")
        return Response({'status': 'received'}, status=status.HTTP_200_OK)

    # Map Daraja status strings to our model choices
    status_map = {
        'success': MpesaTransaction.Status.SUCCESS,
        'completed': MpesaTransaction.Status.SUCCESS,
        'failed': MpesaTransaction.Status.FAILED,
        'cancelled': MpesaTransaction.Status.CANCELLED,
        'pending': MpesaTransaction.Status.PENDING,
    }
    mapped_status = status_map.get(incoming_status)

    try:
        txn = MpesaTransaction.objects.get(transaction_id=transaction_id)
    except MpesaTransaction.DoesNotExist:
        # Callback arrived before or without a local record — create one defensively
        logger.warning(f"[MPESA] No local record for transaction_id={transaction_id}; creating from callback")
        txn = MpesaTransaction(
            transaction_id=transaction_id,
            phone_number=data.get('phone', ''),
            amount=data.get('amount', 0),
            order_id=reference,
        )

    if mapped_status:
        txn.status = mapped_status
    if mpesa_receipt:
        txn.mpesa_receipt = mpesa_receipt

    # Always store the raw callback for auditing
    txn.callback_data = data
    txn.save()

    logger.info(f"[MPESA] Transaction {transaction_id} updated → {txn.status}")

    # ----------------------------------------------------------------
    # Hook: put your post-payment business logic here.
    # Example: mark an order as paid, send a receipt email, etc.
    # ----------------------------------------------------------------
    if txn.is_successful:
        logger.info(f"[MPESA] Payment confirmed for order {txn.order_id}, receipt {txn.mpesa_receipt}")
        # e.g. Order.objects.filter(id=txn.order_id).update(payment_status='paid')

    return Response({'status': 'received'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def payment_status(request, transaction_id):
    """
    Check payment status — first tries the local DB, then polls Daraja if still pending.
    """
    try:
        txn = MpesaTransaction.objects.get(transaction_id=transaction_id)
    except MpesaTransaction.DoesNotExist:
        return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

    # If still pending, sync with Daraja before responding
    if txn.is_pending:
        from payments.mpesa import check_payment_status
        check_payment_status(transaction_id)
        txn.refresh_from_db()

    return Response({
        'success': True,
        'transaction_id': txn.transaction_id,
        'status': txn.status,
        'amount': str(txn.amount),
        'phone_number': txn.phone_number,
        'mpesa_receipt': txn.mpesa_receipt,
        'order_id': txn.order_id,
        'created_at': txn.created_at,
        'updated_at': txn.updated_at,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_payment_link(request):
    """Create a payment link for manual/shareable payments."""
    title = request.data.get('title', 'Payment')
    description = request.data.get('description', 'Payment for order')
    amount = request.data.get('amount')
    success_url = request.data.get('success_url')

    if not amount:
        return Response({'error': 'Amount is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return Response({'error': 'Invalid amount'}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'success': False,
        'error': 'Payment links not supported in Daraja API'
    }, status=status.HTTP_400_BAD_REQUEST)