from django.urls import resolve, reverse
from django.shortcuts import redirect
from main_app.registry import navigation_registry, check_conditions
import logging

logger = logging.getLogger(__name__)

class PermissionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.path.startswith('/api/'):
            return self.get_response(request)

        login_url = reverse("login")
        if not request.user.is_authenticated and request.path != login_url:
            return redirect(login_url)
        try:
            resolved = resolve(request.path)
            url_name = resolved.url_name
            if url_name in navigation_registry:
                conditions = navigation_registry[url_name]["conditions"]
                if conditions and not check_conditions(request, conditions):
                    return redirect(reverse("master_web"))
        except Exception as e:
            logger.error("Error in PermissionMiddleware: %s", e)
        return self.get_response(request)
