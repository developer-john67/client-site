from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('shop.urls')),
    path('api/products/', include('products.urls')),
    path('api/users/', include('users.urls')),
    path('api/cart/', include('cart.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/verification/', include('verification.urls')),
    path('favicon.ico', lambda r: __import__('django.http', fromlist=['HttpResponse']).HttpResponse(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">📦</text></svg>',
        content_type='image/svg+xml'
    )),
]

# Serve media files in production too
if not settings.DEBUG:
    from django.views.static import serve
    from django.urls import re_path
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    ]
else:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    import os
    from django.http import FileResponse

    frontend_path = os.path.join(settings.BASE_DIR, '..', 'frontend')

    def serve_manifest(request):
        return FileResponse(
            open(os.path.join(frontend_path, 'manifest.json'), 'rb'),
            content_type='application/json'
        )

    urlpatterns += static('/html/', document_root=os.path.join(frontend_path, 'html'))
    urlpatterns += static('/css/', document_root=os.path.join(frontend_path, 'css'))
    urlpatterns += static('/js/', document_root=os.path.join(frontend_path, 'js'))
    urlpatterns += static('/images/', document_root=os.path.join(frontend_path, 'images'))
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=frontend_path)
    urlpatterns += [path('manifest.json', serve_manifest)]
  