from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from main_app.models import Personal, Gruppe
from main_app.utils.permission_management import is_mobile, user_has_ogs, user_is_superuser
from main_app.registry import user_functions_registry, check_conditions

def master_web_view(request):
    if request.user.is_authenticated:
        user = request.user
        return render(request, 'master_overview/master_web.html', {"user":user, "functions":get_user_functions(request)})
    else:
        return redirect("login")
    
def get_user_functions(request): # Funktion gibt an, welche Funktionen ein nutzer benutzten darf und diesem dementsprchende angezeigt werden


    functions = []
    for ext_func in user_functions_registry:
        for func in ext_func(request):
            # Jede Erweiterungsfunktion kann ein "conditions"-Feld enthalten
            if "conditions" in func:
                if check_conditions(request, func["conditions"]):
                    functions.append(func)
            else:
                functions.append(func)

    return functions
