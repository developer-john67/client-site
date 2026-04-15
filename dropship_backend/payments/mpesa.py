"""M-Pesa payment service using Safaricom Daraja API for STK Push integration."""

import logging
import base64
import datetime
import json
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class DarajaService:
    def __init__(self):
        self.consumer_key = getattr(settings, 'DARAJA_CONSUMER_KEY', '')
        self.consumer_secret = getattr(settings, 'DARAJA_CONSUMER_SECRET', '')
        self.short_code = getattr(settings, 'DARAJA_SHORT_CODE', '174379')
        self.passkey = getattr(settings, 'DARAJA_PASSKEY', 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919')
        self.callback_url = getattr(settings, 'DARAJA_CALLBACK_URL', '')
        self.environment = getattr(settings, 'DARAJA_ENV', 'sandbox')
        
        self.base_url = 'https://sandbox.safaricom.co.ke' if self.environment == 'sandbox' else 'https://api.safaricom.co.ke'
        self._access_token = None

    def _get_access_token(self):
        """Get OAuth access token from Safaricom."""
        if self._access_token:
            return self._access_token
        
        if not self.consumer_key or not self.consumer_secret:
            logger.error(f"[MPESA] Missing credentials - key: {bool(self.consumer_key)}, secret: {bool(self.consumer_secret)}")
            return None
        
        try:
            auth_url = f'{self.base_url}/oauth/v1/generate?grant_type=client_credentials'
            logger.info(f"[MPESA] Getting token from: {auth_url}")
            logger.info(f"[MPESA] Using consumer_key: {self.consumer_key[:10]}...")
            
            auth_response = requests.get(
                auth_url,
                auth=(self.consumer_key, self.consumer_secret),
                timeout=30
            )
            
            logger.info(f"[MPESA] Auth response status: {auth_response.status_code}")
            logger.info(f"[MPESA] Auth response body: {auth_response.text[:500]}")
            
            if auth_response.status_code == 200:
                auth_data = auth_response.json()
                token = auth_data.get('access_token')
                logger.info(f"[MPESA] Token obtained, length: {len(token) if token else 0}")
                self._access_token = token
                return token
            else:
                logger.error(f"[MPESA] Failed to get access token: {auth_response.text}")
                return None
        except Exception as e:
            logger.exception(f"[MPESA] Error getting access token: {e}")
            return None

    def _generate_password(self):
        """Generate STK Push password (Base64 encoded shortcode + passkey + timestamp)."""
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        password_string = f'{self.short_code}{self.passkey}{timestamp}'
        password = base64.b64encode(password_string.encode('utf-8')).decode('utf-8')
        return password, timestamp

    def initiate_stk_push(self, phone_number, amount, order_id=None):
        """
        Initiate STK Push payment using Daraja API.

        Args:
            phone_number: Customer phone number (format: +254XXXXXXXXX)
            amount: Amount in KES
            order_id: Optional order ID for reference

        Returns:
            dict with response data
        """
        if not self.consumer_key or not self.consumer_secret:
            return {'success': False, 'error': 'Daraja API credentials not configured'}

        access_token = self._get_access_token()
        if not access_token:
            return {'success': False, 'error': 'Failed to obtain access token'}

        password, timestamp = self._generate_password()

        payload = {
            'BusinessShortCode': self.short_code,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': int(amount),
            'PartyA': phone_number.replace('+', ''),
            'PartyB': self.short_code,
            'PhoneNumber': phone_number.replace('+', ''),
            'CallBackURL': self.callback_url or 'https://example.com/callback',
            'AccountReference': str(order_id) if order_id else 'Order Payment',
            'TransactionDesc': f'Payment for order {order_id}' if order_id else 'Order Payment'
        }

        try:
            logger.info(f"[MPESA] Initiating STK Push to {phone_number} for KES {amount}, order_id={order_id}")

            stk_url = f'{self.base_url}/mpesa/stkpush/v1/processrequest'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            logger.info(f"[MPESA] STK Push URL: {stk_url}")
            logger.info(f"[MPESA] Payload: {json.dumps(payload)}")

            response = requests.post(
                stk_url,
                json=payload,
                headers=headers,
                timeout=30,
            )

            logger.info(f"[MPESA] Response status: {response.status_code}")
            logger.info(f"[MPESA] Response headers: {dict(response.headers)}")
            logger.info(f"[MPESA] Response body: {response.text}")

            if response.status_code == 200:
                data = response.json()
                
                if data.get('ResponseCode') == '0':
                    return {
                        'success': True,
                        'transaction_id': data.get('MerchantRequestID'),
                        'checkout_request_id': data.get('CheckoutRequestID'),
                        'phone_number': phone_number,
                        'amount': amount,
                        'order_id': order_id,
                        'status': 'pending',
                        'message': data.get('ResponseDescription', 'STK push initiated'),
                    }
                else:
                    return {
                        'success': False,
                        'error': data.get('ResponseDescription', 'Failed to initiate STK push'),
                    }
            else:
                error_data = response.json() if response.content else {}
                logger.error(f"[MPESA] HTTP {response.status_code}: {error_data}")
                return {
                    'success': False,
                    'error': error_data.get('ResponseDescription', f'HTTP {response.status_code}'),
                }

        except requests.exceptions.Timeout:
            logger.error("[MPESA] Request timeout")
            return {'success': False, 'error': 'Request timeout'}
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"[MPESA] Connection failed: {e}")
            return {'success': False, 'error': 'Connection failed - cannot reach M-Pesa API'}
        except Exception as e:
            logger.exception(f"[MPESA] Unexpected error: {e}")
            return {'success': False, 'error': str(e)}

    def check_transaction(self, checkout_request_id):
        """
        Check transaction status using Daraja API.

        Args:
            checkout_request_id: The CheckoutRequestID from STK push

        Returns:
            dict with transaction status
        """
        if not self.consumer_key or not self.consumer_secret:
            return {'success': False, 'error': 'Daraja API credentials not configured'}

        access_token = self._get_access_token()
        if not access_token:
            return {'success': False, 'error': 'Failed to obtain access token'}

        try:
            stk_query_url = f'{self.base_url}/mpesa/stkpushquery/v1/query'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            payload = {
                'BusinessShortCode': self.short_code,
                'CheckoutRequestID': checkout_request_id,
                'Password': self._generate_password()[0],
                'Timestamp': self._generate_password()[1],
            }

            response = requests.post(
                stk_query_url,
                json=payload,
                headers=headers,
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                
                result_code = data.get('ResultCode', '0')
                if result_code == '0':
                    return {
                        'success': True,
                        'transaction_id': data.get('MerchantRequestID'),
                        'checkout_request_id': checkout_request_id,
                        'status': 'completed',
                        'message': data.get('ResultDesc', 'Payment completed'),
                    }
                else:
                    return {
                        'success': False,
                        'status': 'failed',
                        'error': data.get('ResultDesc', 'Transaction failed'),
                    }
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}

        except Exception as e:
            logger.exception(f"[MPESA] Transaction check error: {e}")
            return {'success': False, 'error': str(e)}


# ---------------------------------------------------------------------------
# Phone number helpers
# ---------------------------------------------------------------------------

def format_phone_number(phone):
    """Format phone number to Daraja format (254XXXXXXXXX)."""
    if not phone:
        return None

    phone = phone.strip().replace(' ', '').replace('-', '').replace('+', '')

    if phone.startswith('0'):
        phone = '254' + phone[1:]
    elif phone.startswith('7') or phone.startswith('1'):
        phone = '254' + phone
    elif not phone.startswith('254'):
        phone = '254' + phone

    if len(phone) == 12 and phone.isdigit():
        return phone

    return None


# ---------------------------------------------------------------------------
# Convenience helpers used by views
# ---------------------------------------------------------------------------

def initiate_mpesa_payment(order_id, phone_number, amount):
    """
    Initiate M-Pesa STK Push and persist a pending transaction record.

    Returns:
        dict with payment initiation result
    """
    from payments.models import MpesaTransaction

    formatted_phone = format_phone_number(phone_number)
    if not formatted_phone:
        return {'success': False, 'error': 'Invalid phone number format'}

    daraja = DarajaService()
    result = daraja.initiate_stk_push(
        phone_number='+' + formatted_phone,
        amount=amount,
        order_id=order_id,
    )

    if result.get('success'):
        MpesaTransaction.objects.create(
            transaction_id=result.get('transaction_id'),
            checkout_request_id=result.get('checkout_request_id'),
            phone_number='+' + formatted_phone,
            amount=amount,
            order_id=order_id,
            status=MpesaTransaction.Status.PENDING,
        )

    return result


def check_payment_status(checkout_request_id):
    """Check M-Pesa payment status via Daraja and sync local record."""
    from payments.models import MpesaTransaction

    daraja = DarajaService()
    result = daraja.check_transaction(checkout_request_id)

    if result.get('success'):
        status = result.get('status', 'unknown')
        MpesaTransaction.objects.filter(
            checkout_request_id=checkout_request_id
        ).update(
            status=MpesaTransaction.Status.COMPLETED if status == 'completed' else MpesaTransaction.Status.PENDING,
            mpesa_receipt=result.get('transaction_id', ''),
        )
        result['payment_status'] = 'completed' if status == 'completed' else status

    return result