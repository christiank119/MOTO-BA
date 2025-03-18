from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from main_app.models import Personal, Gruppe
from main_app.utils.permission_management import is_mobile, user_has_ogs, user_is_superuser
from main_app.registry import navigation_registry, check_conditions
from django.urls import reverse

def master_web_view(request):
    if request.user.is_authenticated:
        user = request.user
        return render(request, 'master_overview/master_web.html', {"user":user, "functions":get_user_functions(request)})
    else:
        return redirect("login")
    
def get_user_functions(request): # Funktion gibt an, welche Funktionen ein nutzer benutzten darf und diesem dementsprchende angezeigt werden
    functions = []
    for item in navigation_registry.values():
        if item.get("show_in_nav", True) and check_conditions(request, item.get("nav_conditions", [])):
            item_copy = item.copy()
            try:
                item_copy["url"] = reverse(item["url_name"])
                functions.append(item_copy)
            except Exception as e:
                # Log or handle URL resolution errors as needed.
                pass
    return functions
