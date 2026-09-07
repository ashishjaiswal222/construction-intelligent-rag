from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)

class DevAuthMiddleware(MiddlewareMixin):
    """
    Development middleware that automatically logs in requests as a default admin user.
    This bypasses the need for JWT tokens from the Next.js frontend during local dev.
    """
    def process_request(self, request):
        User = get_user_model()
        
        # Check if user is already authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            return
            
        try:
            # Try to get or create a default admin user
            user, created = User.objects.get_or_create(
                username='dev_admin',
                defaults={
                    'email': 'admin@construction.ai',
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            
            if created:
                user.set_password('admin123')
                user.save()
                logger.info("Created default dev_admin user.")
                
            request.user = user
        except Exception as e:
            logger.error(f"DevAuthMiddleware failed: {e}")

from rest_framework.authentication import SessionAuthentication

class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    Bypass CSRF checks for development when using DevAuthMiddleware.
    """
    def enforce_csrf(self, request):
        return  # Bypass CSRF check
