"""Security middleware for request sanitization and protection."""

import re
import json
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.core.exceptions import SuspiciousOperation


class CSRFExemptMiddleware:
    """Exempt API endpoints from CSRF."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.path.startswith('/api/'):
            request.csrf_exempt = True
        return self.get_response(request)


class RequestSanitizationMiddleware(MiddlewareMixin):
    """Middleware to sanitize incoming requests and prevent injection attacks."""
    
    def process_request(self, request):
        """Sanitize request data before processing."""
        if request.method in ('POST', 'PUT', 'PATCH'):
            content_type = request.content_type or ''
            
            if 'application/json' in content_type:
                try:
                    data = json.loads(request.body)
                    sanitized_data = self._sanitize_data(data)
                    request._sanitized_post = sanitized_data
                except json.JSONDecodeError:
                    pass
            
            elif 'application/x-www-form-urlencoded' in content_type or 'multipart/form-data' in content_type:
                sanitized_data = {}
                for key, value in request.POST.items():
                    sanitized_data[key] = self._sanitize_value(value)
                request._sanitized_post = sanitized_data
        
        if request.GET:
            sanitized_query = {}
            for key, value in request.GET.items():
                sanitized_query[key] = self._sanitize_value(value)
            request._sanitized_get = sanitized_query
        
        return None
    
    def _sanitize_data(self, data):
        """Recursively sanitize data structures."""
        if isinstance(data, dict):
            return {k: self._sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        elif isinstance(data, str):
            return self._sanitize_value(data)
        else:
            return data
    
    def _sanitize_value(self, value):
        """Sanitize a single value."""
        if not isinstance(value, str):
            return value
        
        value = value.strip()
        
        value = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', value)
        
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>',
        ]
        
        for pattern in dangerous_patterns:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE | re.DOTALL)
        
        return value[:10000]
    
    def process_response(self, request, response):
        """Add security headers to response."""
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response


class SQLInjectionProtectionMiddleware(MiddlewareMixin):
    """Additional layer of protection against SQL injection."""
    
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b.*\b(FROM|INTO|TABLE|DATABASE)\b)",
        r"(--|#|\/\*|\*\/)",
        r"(\bOR\b.*=.*\bOR\b)",
        r"(\bAND\b.*=.*\bAND\b)",
        r"('\s*(OR|AND)\s*')",
        r"(;\s*(SELECT|INSERT|UPDATE|DELETE|DROP))",
        r"(EXEC\s*\()",
        r"(0x[0-9a-fA-F]+)",
    ]
    
    def process_request(self, request):
        """Check for potential SQL injection in request."""
        # Skip SQL injection check for certain paths
        if request.path in ['/admin-login/', '/admin-logout/', '/upload/', '/api/orders/create/', '/api/users/login/', '/api/users/register/']:
            return None
            
        for key in list(request.GET.keys()) + list(request.POST.keys()):
            value = request.GET.get(key) or request.POST.get(key)
            
            if value and isinstance(value, str):
                for pattern in self.SQL_INJECTION_PATTERNS:
                    if re.search(pattern, value, re.IGNORECASE):
                        raise SuspiciousOperation('Potential SQL injection detected')
        
        return None


class RateLimitMiddleware(MiddlewareMixin):
    """Simple rate limiting middleware."""
    
    request_counts = {}
    rate_limit = 100
    window_seconds = 60
    
    def process_request(self, request):
        """Check rate limit before processing request."""
        if request.path.startswith('/api/'):
            client_ip = self._get_client_ip(request)
            
            if not client_ip:
                return None
            
            import time
            current_time = time.time()
            
            if client_ip not in self.request_counts:
                self.request_counts[client_ip] = []
            
            self.request_counts[client_ip] = [
                t for t in self.request_counts[client_ip]
                if current_time - t < self.window_seconds
            ]
            
            if len(self.request_counts[client_ip]) >= self.rate_limit:
                return JsonResponse({
                    'error': 'Rate limit exceeded. Please try again later.'
                }, status=429)
            
            self.request_counts[client_ip].append(current_time)
        
        return None
    
    def _get_client_ip(self, request):
        """Get client IP from request, handling proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')