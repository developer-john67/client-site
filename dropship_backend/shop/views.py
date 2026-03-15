import os
import uuid
from datetime import datetime

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect
from django.conf import settings

from .forms import ProductUploadForm
from products.models import Product, Category


def is_admin(user):
    return user.is_active and (user.is_staff or user.is_superuser)


@login_required(login_url='/admin-login/')
@user_passes_test(is_admin, login_url='/admin-login/')
def product_upload(request):
    if request.method == 'POST':
        form = ProductUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # ─── Handle image upload ───────────────────────────────────────
            image_url = ''
            if 'image' in request.FILES:
                image_file = request.FILES['image']
                ext      = os.path.splitext(image_file.name)[1].lower()
                filename = f"products/{uuid.uuid4()}{ext}"
                filepath = os.path.join(settings.MEDIA_ROOT, filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'wb+') as destination:
                    for chunk in image_file.chunks():
                        destination.write(chunk)
                image_url = filename

            # ─── Map form fields → products.Product fields ─────────────────
            name         = form.cleaned_data['name']
            description  = form.cleaned_data.get('description', '')
            price        = form.cleaned_data['price']
            stock        = form.cleaned_data.get('stock_quantity', 0)
            is_active    = form.cleaned_data.get('is_active', True)
            category_raw = form.cleaned_data.get('category', '')

            slug = name.lower().strip().replace(' ', '-')
            sku  = f"SKU-{uuid.uuid4().hex[:8].upper()}"

            # ─── Resolve category ──────────────────────────────────────────
            category_id   = None
            category_name = str(category_raw)

            # Try direct UUID
            try:
                category_id = uuid.UUID(str(category_raw))
            except (ValueError, AttributeError):
                pass

            # Try by name
            if not category_id:
                try:
                    cats = list(Category.objects.filter(name=str(category_raw)))
                    if cats:
                        category_id   = cats[0].category_id
                        category_name = cats[0].name
                except Exception:
                    pass

            # Try by slug
            if not category_id:
                try:
                    slug_try = str(category_raw).lower().strip().replace(' ', '-')
                    cats = list(Category.objects.filter(slug=slug_try))
                    if cats:
                        category_id   = cats[0].category_id
                        category_name = cats[0].name
                except Exception:
                    pass

            if not category_id:
                category_id = uuid.uuid4()  # fallback — uncategorised

            # ─── Save to Cassandra ─────────────────────────────────────────
            Product.create(
                product_id    = uuid.uuid4(),
                name          = name,
                slug          = slug,
                sku           = sku,
                description   = description,
                price         = price,
                category_id   = category_id,
                category_name = category_name,
                main_image    = image_url,
                stock         = stock,
                is_available  = is_active,
                is_featured   = False,
                created_at    = datetime.utcnow(),
                updated_at    = datetime.utcnow(),
            )

            messages.success(request, f"✅ Product '{name}' uploaded successfully!")
            return redirect('product_upload')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProductUploadForm()

    # Show ALL recent products (active + inactive) so admin sees everything
    try:
        recent_products = list(Product.objects.all().limit(10))
    except Exception:
        recent_products = []

    return render(request, 'shop/product_upload.html', {
        'form':            form,
        'recent_products': recent_products,
        'admin_user':      request.user,
    })


@login_required(login_url='/admin-login/')
@user_passes_test(is_admin, login_url='/admin-login/')
def product_list(request):
    try:
        products = list(Product.objects.all().limit(50))
    except Exception:
        products = []

    return render(request, 'shop/product_list.html', {
        'products':   products,
        'admin_user': request.user,
    })


def admin_login(request):
    if request.user.is_authenticated and is_admin(request.user):
        return redirect('product_upload')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user and is_admin(user):
            login(request, user)
            return redirect('product_upload')
        else:
            error = 'Invalid credentials or insufficient permissions.'

    return render(request, 'shop/admin_login.html', {'error': error})


def admin_logout(request):
    logout(request)
    return redirect('admin_login')