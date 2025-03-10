from main_app.utils.permission_management import is_mobile, user_has_ogs, user_is_superuser

navigation_registry = {}

def register_view(view_func, url_name, label, conditions=None, nav_conditions=None, show_in_nav=False):
    conditions = conditions or []
    nav_conditions = nav_conditions if nav_conditions is not None else conditions
    navigation_registry[url_name] = {
        "label": label,
        "url_name": url_name,
        "conditions": conditions,         # Bedingungen für den Zugriff
        "nav_conditions": nav_conditions, # Bedingungen für die Navigation
        "show_in_nav": show_in_nav,
        "view_func": view_func,
    }

def check_conditions(request, conditions):
    return all(condition(request) for condition in conditions)


condition_no_root = [lambda req: req.user.username != "root"]
condition_only_root = [lambda req: req.user.username == "root"]
condition_only_su = [lambda req: req.user.is_superuser and req.user.username != "root"]
condition_root_and_su = [lambda req: req.user.is_superuser or req.user.username == "root"]
condition_ogs_group_needed = [lambda req: req.user.username != "root" and user_has_ogs(req)]