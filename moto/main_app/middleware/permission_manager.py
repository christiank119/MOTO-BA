from django.http import HttpResponseForbidden
from main_app.registry import user_functions_registry, check_conditions

class PermissionMiddleware:
    """
    Diese Middleware prüft, ob der angeforderte Pfad in einer der
    registrierten Navigationsfunktionen enthalten ist und ob der User
    die dafür definierten Bedingungen erfüllt.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        
        for reg_func in user_functions_registry:           
            navigation_items = reg_func(request)
            for item in navigation_items:
                if item.get("url") == request.path:
                    conditions = item.get("conditions", [])
                    if conditions and not check_conditions(request, conditions):
                        return HttpResponseForbidden("You do not have permission to access this page.")
        response = self.get_response(request)
        return response
