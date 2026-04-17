import os
import uuid

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect
from django.conf import settings

from .forms import ProductUploadForm
from products.models import Product, Category


def is_admin(user):
    return user.is_active and (user.is_staff or user.is_superuser)


def generate_unique_slug(base_name):
    """Generate a slug that doesn't already exist in the DB."""
    base_slug = base_name.lower().strip().replace(' ', '-')
    slug = base_slug
    counter = 1
    while Product.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


def resolve_category(category_raw):
    """Return (category_id, category_name) from form input, or (None, 'Uncategorised')."""
    category_name = str(category_raw)

    # Try direct UUID
    try:
        cat = Category.objects.get(category_id=uuid.UUID(str(category_raw)))
        return cat.category_id, cat.name
    except (ValueError, AttributeError, Category.DoesNotExist):
        pass

    # Try by name
    cat = Category.objects.filter(name__iexact=category_name).first()
    if cat:
        return cat.category_id, cat.name

    # Try by slug
    slug_try = category_name.lower().strip().replace(' ', '-')
    cat = Category.objects.filter(slug=slug_try).first()
    if cat:
        return cat.category_id, cat.name

    return None, 'Uncategorised'


def save_uploaded_image(image_file):
    """Write image to MEDIA_ROOT and return the relative path, or '' on failure."""
    try:
        ext      = os.path.splitext(image_file.name)[1].lower()
        filename = f"products/{uuid.uuid4()}{ext}"
        filepath = os.path.join(settings.MEDIA_ROOT, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb+') as dest:
            for chunk in image_file.chunks():
                dest.write(chunk)
        return filename
    except Exception as e:
        # Log and continue — don't crash the whole upload for a bad image
        print(f"[image upload error] {e}")
        return ''


@login_required(login_url='/admin-login/')
@user_passes_test(is_admin, login_url='/admin-login/')
def product_upload(request):
    if request.method == 'POST':
        form = ProductUploadForm(request.POST, request.FILES)
        if form.is_valid():
            name         = form.cleaned_data['name']
            description  = form.cleaned_data.get('description', '')
            price        = form.cleaned_data['price']
            stock        = form.cleaned_data.get('stock_quantity', 0)
            is_active    = form.cleaned_data.get('is_active', True)
            category_raw = form.cleaned_data.get('category', '')

            slug         = generate_unique_slug(name)            # ← fixed
            sku          = f"SKU-{uuid.uuid4().hex[:8].upper()}"
            image_url    = save_uploaded_image(request.FILES['image']) \
                           if 'image' in request.FILES else ''
            category_id, category_name = resolve_category(category_raw)  # ← fixed

            Product.objects.create(
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
            )

            messages.success(request, f"✅ Product '{name}' uploaded successfully!")
            return redirect('product_upload')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProductUploadForm()

    try:
        recent_products = list(Product.objects.all()[:10])
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
        products = list(Product.objects.all()[:50])
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
        
        from users.models import User
        
        # Try username first, then email
        user = User.objects.filter(username=username).first()
        if not user:
            user = User.objects.filter(email=username).first()
        
        if user and user.check_password(password) and is_admin(user):
            login(request, user)
            return redirect('product_upload')
        else:
            error = 'Invalid credentials or insufficient permissions.'

    return render(request, 'shop/admin_login.html', {'error': error})


def admin_logout(request):
    logout(request)
    return redirect('admin_login')

