# cart/views.py

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
import uuid
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer


def get_user_from_token(request):
    import sys
    from django.utils import timezone
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None
    print(f"[DEBUG get_user] Token: {token[:40] if token else 'NONE'}", file=sys.stderr)
    if not token:
        print("[DEBUG get_user] No token, returning None", file=sys.stderr)
        return None
    try:
        from users.models import UserSession, User
        sessions = list(UserSession.objects.filter(token=token))
        if not sessions:
            print(f"[DEBUG get_user] Token NOT FOUND in DB", file=sys.stderr)
            return None
        session = sessions[0]
        if session.expires_at < timezone.now():
            print(f"[DEBUG get_user] Session expired", file=sys.stderr)
            return None
        users = list(User.objects.filter(user_id=session.user_id))
        print(f"[DEBUG get_user] Found user: {users[0].email if users else 'NONE'}", file=sys.stderr)
        return users[0] if users else None
    except Exception as e:
        print(f"[DEBUG get_user] Error: {e}", file=sys.stderr)
        return None


def parse_uuid(value):
    """Safely parse a UUID from any type. Returns UUID or None."""
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value).strip())
    except (ValueError, AttributeError):
        return None


def get_or_create_cart(user_id=None, session_id=None):
    """Get existing cart or create a new one"""
    if user_id:
        carts = list(Cart.objects.filter(user_id=user_id))
        if carts:
            return carts[0]
    elif session_id:
        carts = list(Cart.objects.filter(session_id=session_id))
        if carts:
            return carts[0]

    cart = Cart.objects.create(
        cart_id    = uuid.uuid4(),
        user_id    = user_id,
        session_id = session_id or '',
        item_count = 0,
        subtotal   = 0,
        created_at = timezone.now(),
        updated_at = timezone.now(),
    )
    return cart


def recalculate_cart(cart):
    """Recalculate cart totals from its items"""
    cart_items     = list(CartItem.objects.filter(cart_id=cart.cart_id))
    cart.item_count = sum(item.quantity for item in cart_items)
    cart.subtotal   = sum(item.total_price for item in cart_items)
    cart.updated_at = timezone.now()
    cart.save()
    return cart


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_cart(request):
    """Get current cart with all items"""
    user       = get_user_from_token(request)
    session_id = request.headers.get('X-Session-ID', '')
    user_id    = user.user_id if user else None
    cart       = get_or_create_cart(user_id=user_id, session_id=session_id)

    cart_items = list(CartItem.objects.filter(cart_id=cart.cart_id))
    cart_data  = CartSerializer(cart).data
    cart_data['cart_items'] = CartItemSerializer(cart_items, many=True).data

    return Response(cart_data)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def add_to_cart(request):
    """Add an item to cart"""
    import sys
    
    try:
        print("=" * 50, file=sys.stderr)
        print("[DEBUG] add_to_cart called", file=sys.stderr)
        print(f"[DEBUG] Authorization: {request.headers.get('Authorization', 'NONE')[:50]}", file=sys.stderr)
        print(f"[DEBUG] Data: {dict(request.data)}", file=sys.stderr)
        print("=" * 50, file=sys.stderr)
        
        user       = get_user_from_token(request)
        session_id = request.headers.get('X-Session-ID', '')
        user_id    = user.user_id if user else None
        
        print(f"[DEBUG] user: {user}, user_id: {user_id}, session_id: '{session_id}'")
        
        cart       = get_or_create_cart(user_id=user_id, session_id=session_id)
        print(f"[DEBUG] cart created/retrieved: {cart.cart_id}, user_id: {cart.user_id}, session_id: {cart.session_id}")

        product_id_raw = request.data.get('product_id')
        variant_id_raw = request.data.get('variant_id')

        if not product_id_raw:
            return Response({'error': 'product_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        # ── Validate product_id ───────────────────────────────────────────────────
        product_id = parse_uuid(product_id_raw)
        if not product_id:
            return Response(
                {'error': f'Invalid product_id format: {product_id_raw}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        variant_id = parse_uuid(variant_id_raw)

# ── Fetch product from database to get name/price ────────────────────────
        product_name  = request.data.get('product_name', '')
        product_image = request.data.get('product_image', '')
        product_slug  = request.data.get('product_slug', '')
        unit_price    = request.data.get('unit_price')

        if not unit_price or not product_name:
            try:
                from products.models import Product
                products = list(Product.objects.filter(product_id=product_id))
                if products:
                    p             = products[0]
                    product_name  = product_name  or p.name
                    product_image = product_image or p.main_image or ''
                    product_slug  = product_slug  or p.slug or ''
                    unit_price    = unit_price    or float(p.price)
                else:
                    return Response(
                        {'error': 'Product not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            except Exception as e:
                return Response(
                    {'error': f'Could not fetch product details: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        unit_price = float(unit_price)
        quantity   = int(request.data.get('quantity', 1))

    # ── Check if item already exists in cart ──────────────────────────────────
    existing_items = list(CartItem.objects.filter(
        cart_id    = cart.cart_id,
        product_id = product_id,
    ))

    existing = None
    if variant_id:
        existing = next((i for i in existing_items if str(i.variant_id) == str(variant_id)), None)
    else:
        existing = existing_items[0] if existing_items else None

    if existing:
        existing.quantity    += quantity
        existing.total_price  = existing.unit_price * existing.quantity
        existing.updated_at   = timezone.now()
        existing.save()
    else:
        # Convert UUIDs to strings for serializer, omit None values
        item_data = {
            'cart_id':       str(cart.cart_id),
            'product_id':    str(product_id),
            'product_name':  product_name,
            'product_image': product_image or '',
            'product_slug':  product_slug or '',
            'variant_name':  request.data.get('variant_name', ''),
            'unit_price':    str(unit_price),
            'quantity':      quantity,
        }
        # Only include variant_id if it exists
        if variant_id:
            item_data['variant_id'] = str(variant_id)

        serializer = CartItemSerializer(data=item_data)
        if not serializer.is_valid():
            # Return detailed errors to help debug
            return Response(
                {'error': 'Validation failed', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()

    recalculate_cart(cart)

    cart_items = list(CartItem.objects.filter(cart_id=cart.cart_id))
    cart_data  = CartSerializer(cart).data
    cart_data['cart_items'] = CartItemSerializer(cart_items, many=True).data
    
    print(f"[DEBUG] add_to_cart - cart_id: {cart.cart_id}, user_id: {cart.user_id}, session_id: {cart.session_id}, items_count: {len(cart_items)}")

    return Response(cart_data, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([permissions.AllowAny])
def update_cart_item(request, item_id):
    """Update quantity of a cart item"""
    try:
        item = CartItem.objects.get(item_id=item_id)
    except CartItem.DoesNotExist:
        return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

    quantity = request.data.get('quantity')
    if quantity is None:
        return Response({'error': 'quantity is required'}, status=status.HTTP_400_BAD_REQUEST)

    quantity = int(quantity)
    if quantity < 1:
        return Response({'error': 'Quantity must be at least 1'}, status=status.HTTP_400_BAD_REQUEST)

    item.quantity    = quantity
    item.total_price = item.unit_price * quantity
    item.updated_at  = timezone.now()
    item.save()

    try:
        cart       = Cart.objects.get(cart_id=item.cart_id)
        recalculate_cart(cart)
        cart_items = list(CartItem.objects.filter(cart_id=cart.cart_id))
        cart_data  = CartSerializer(cart).data
        cart_data['cart_items'] = CartItemSerializer(cart_items, many=True).data
        return Response(cart_data)
    except Cart.DoesNotExist:
        return Response(CartItemSerializer(item).data)


@api_view(['DELETE'])
@permission_classes([permissions.AllowAny])
def remove_from_cart(request, item_id):
    """Remove an item from cart"""
    try:
        item = CartItem.objects.get(item_id=item_id)
    except CartItem.DoesNotExist:
        return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

    cart_id = item.cart_id
    item.delete()

    try:
        cart       = Cart.objects.get(cart_id=cart_id)
        recalculate_cart(cart)
        cart_items = list(CartItem.objects.filter(cart_id=cart.cart_id))
        cart_data  = CartSerializer(cart).data
        cart_data['cart_items'] = CartItemSerializer(cart_items, many=True).data
        return Response(cart_data)
    except Cart.DoesNotExist:
        return Response({'message': 'Item removed'})


@api_view(['DELETE'])
@permission_classes([permissions.AllowAny])
def clear_cart(request, cart_id):
    """Clear all items from cart"""
    try:
        cart = Cart.objects.get(cart_id=cart_id)
    except Cart.DoesNotExist:
        return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)

    for item in list(CartItem.objects.filter(cart_id=cart_id)):
        item.delete()

    cart.item_count = 0
    cart.subtotal   = 0
    cart.updated_at = timezone.now()
    cart.save()

    return Response({'message': 'Cart cleared', 'cart_id': str(cart_id)})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def merge_cart(request):
    """Merge guest cart into user cart on login"""
    user = get_user_from_token(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    session_id = request.data.get('session_id')
    if not session_id:
        return Response({'error': 'session_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    guest_carts = list(Cart.objects.filter(session_id=session_id))
    if not guest_carts:
        return Response({'message': 'No guest cart found'})

    guest_cart = guest_carts[0]
    user_cart  = get_or_create_cart(user_id=user.user_id)

    for item in list(CartItem.objects.filter(cart_id=guest_cart.cart_id)):
        item.cart_id = user_cart.cart_id
        item.save()

    guest_cart.delete()
    recalculate_cart(user_cart)

    cart_items = list(CartItem.objects.filter(cart_id=user_cart.cart_id))
    cart_data  = CartSerializer(user_cart).data
    cart_data['cart_items'] = CartItemSerializer(cart_items, many=True).data

    return Response(cart_data)