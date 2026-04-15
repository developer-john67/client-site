# products/views.py

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
import uuid
from datetime import datetime
from .models import Category, Product, ProductVariant, ProductReview
from .serializers import (
    CategorySerializer, ProductSerializer,
    ProductVariantSerializer, ProductReviewSerializer
)


def is_admin(user_id):
    # Handle Django auth user object passed directly
    try:
        if user_id.is_staff or user_id.is_superuser:
            return True
    except AttributeError:
        pass
    # Handle user_id UUID
    try:
        from users.models import User
        user = User.objects.get(user_id=user_id)
        return user.user_type == "admin" or user.is_staff
    except Exception:
        return False


def resolve_category_id(category_param):
    """
    Accept either a UUID string or a slug like 'electronics'.
    Returns a UUID or None.
    """
    if not category_param:
        return None

    # Try parsing as UUID first
    try:
        return uuid.UUID(category_param)
    except (ValueError, AttributeError):
        pass

    # Try finding category by slug
    try:
        cats = list(Category.objects.filter(slug=category_param))
        if cats:
            return cats[0].category_id
    except Exception:
        pass

    # Try finding by name (case-insensitive)
    try:
        all_cats = list(Category.objects.all())
        for cat in all_cats:
            if cat.name.lower() == category_param.lower():
                return cat.category_id
    except Exception:
        pass

    return None


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def product_list(request):
    queryset = list(Product.objects.filter(is_available=True))

    # ─── Category filter (accepts UUID or slug) ───────────────────────────
    category_param = request.query_params.get('category')
    if category_param:
        category_id = resolve_category_id(category_param)
        if category_id:
            queryset = [p for p in queryset if p.category_id == category_id]
        else:
            # Category not found — return empty rather than 404
            return Response({
                'count': 0, 'next': None, 'previous': None, 'results': []
            })

    # ─── Featured filter ──────────────────────────────────────────────────
    featured = request.query_params.get('featured')
    if featured and featured.lower() == 'true':
        queryset = [p for p in queryset if p.is_featured]

    # ─── Search filter ────────────────────────────────────────────────────
    search = request.query_params.get('search')
    if search:
        search_lower = search.lower()
        queryset = [p for p in queryset if
                    search_lower in (p.name or '').lower() or
                    search_lower in (p.description or '').lower()]

    # ─── Price filters ────────────────────────────────────────────────────
    min_price = request.query_params.get('min_price')
    max_price = request.query_params.get('max_price')
    if min_price:
        queryset = [p for p in queryset if float(p.price) >= float(min_price)]
    if max_price:
        queryset = [p for p in queryset if float(p.price) <= float(max_price)]

    paginator = PageNumberPagination()
    paginator.page_size = 20
    result_page = paginator.paginate_queryset(queryset, request)

    serializer = ProductSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def product_detail(request, slug):
    try:
        product = Product.objects.get(slug=slug)

        variants = ProductVariant.objects.filter(product_id=product.product_id)
        reviews  = ProductReview.objects.filter(product_id=product.product_id, is_approved=True)

        try:
            from .models import ProductView
            ProductView.objects.create(
                view_id    = uuid.uuid4(),
                product_id = product.product_id,
                user_id    = getattr(request.user, 'user_id', None),
                session_id = request.session.session_key,
                ip_address = request.META.get('REMOTE_ADDR'),
                viewed_at  = datetime.now()
            )
        except Exception:
            pass

        serializer = ProductSerializer(product)
        data = serializer.data
        data['variants'] = ProductVariantSerializer(variants, many=True).data
        data['reviews']  = ProductReviewSerializer(reviews, many=True).data

        return Response(data)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def category_list(request):
    categories = Category.objects.filter(is_active=True)
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def category_detail(request, slug):
    # Accept slug or UUID
    category = None
    try:
        category = Category.objects.get(slug=slug)
    except Category.DoesNotExist:
        # Try by UUID
        try:
            category = Category.objects.get(category_id=uuid.UUID(slug))
        except (Category.DoesNotExist, ValueError):
            pass

    if not category:
        return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

    products = [p for p in Product.objects.all()
                if p.category_id == category.category_id and p.is_available]

    data = CategorySerializer(category).data
    data['products'] = ProductSerializer(products, many=True).data
    return Response(data)


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def admin_products(request):
    if not is_admin(request.user):
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save()
            try:
                category = Category.objects.get(category_id=product.category_id)
                category.product_count += 1
                category.save()
            except Exception:
                pass
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.AllowAny])
def admin_product_detail(request, product_id):
    if not is_admin(request.user):
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

    try:
        product = Product.objects.get(product_id=uuid.UUID(str(product_id)))
    except (Product.DoesNotExist, ValueError):
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(ProductSerializer(product).data)

    elif request.method == 'PUT':
        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        try:
            category = Category.objects.get(category_id=product.category_id)
            category.product_count -= 1
            category.save()
        except Exception:
            pass
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def admin_create_category(request):
    if not is_admin(request.user):
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

    serializer = CategorySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_product_review(request, product_id):
    try:
        product = Product.objects.get(product_id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    existing = list(ProductReview.objects.filter(
        product_id=product_id,
        user_id=request.user.user_id
    ))
    if existing:
        return Response({'error': 'You have already reviewed this product'},
                        status=status.HTTP_400_BAD_REQUEST)

    data = {
        'review_id':  uuid.uuid4(),
        'product_id': product_id,
        'user_id':    request.user.user_id,
        'rating':     request.data.get('rating'),
        'title':      request.data.get('title', ''),
        'comment':    request.data.get('body', ''),
        'is_approved': False,
        'created_at': datetime.utcnow(),
    }

    serializer = ProductReviewSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)