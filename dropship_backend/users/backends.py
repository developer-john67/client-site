from django.contrib.auth.backends import ModelBackend
from users.models import User


class EmailBackend(ModelBackend):
    """Authenticate users using email instead of username."""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('username') or kwargs.get('email')
        
        if not username or not password:
            return None
            
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            return None
        
        if user.check_password(password):
            return user
        return None
    
    def user_can_authenticate(self, user):
        return user.is_active