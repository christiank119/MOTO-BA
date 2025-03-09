# Registerien aller möglicher Funktionen, etc. Nur modulare Apps. Sollte später erwitert werden

user_functions_registry = []

def register_user_function(user_func):   # Hier werden Function registriert, welche den Nutzer benutzen können oder nicht
    user_functions_registry.append(user_func)

def check_conditions(request, conditions):   # Hilfsfunktion zum cheken von conditions
    return all(cond(request) for cond in conditions)