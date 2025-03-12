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



# main_app/extensions.py
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

# Extension registry
_EXTENSION_REGISTRY = {
    # UI extension points (for template fragments)
    'pupil_navigation_buttons': [],     # Buttons in pupil view navigation
    'pupil_information_sections': [],   # Additional info sections in pupil view
    
    # Data extension points (for context modification)
    'pupil_context': [],                # Modify context in pupil view
                                        # Modify context in room view
}

def register_extension(extension_point):
    """
    Decorator to register an extension function to a specific extension point.
    
    Example:
        @register_extension('pupil_navigation_buttons')
        def add_analysis_button(context):
            return '<button>...</button>'
    """
    def decorator(func):
        if extension_point in _EXTENSION_REGISTRY:
            _EXTENSION_REGISTRY[extension_point].append(func)
        else:
            raise ValueError(f"Unknown extension point: {extension_point}")
        return func
    return decorator

def register_template_extension(extension_point, template_name):
    """
    Decorator to register a template as an extension.
    
    Example:
        @register_template_extension('pupil_information_sections', 'analysis/pupil_info.html')
        def add_pupil_info_section(context):
            # Modify context if needed before template rendering
            return context
    """
    def decorator(func):
        @register_extension(extension_point)
        def wrapper(context):
            # Call the original function to allow context modification
            new_context = func(context) if func else context
            # Render the template with the modified context
            rendered = render_to_string(template_name, new_context)
            return mark_safe(rendered)
        return wrapper
    return decorator

def get_extensions(extension_point, context=None):

    extensions = []
    for extension_func in _EXTENSION_REGISTRY.get(extension_point, []):
        if context is not None:
            # Make a copy of the context to avoid modifications affecting other extensions
            context_copy = context.copy() if hasattr(context, 'copy') else dict(context)
            result = extension_func(context_copy)
            extensions.append(result)
        else:
            extensions.append(extension_func())
    return extensions

def extension_processor(request):
    """
    Context processor that adds extensions to all templates.
    
    Add this to your TEMPLATES context_processors in settings.py:
    'main_app.extensions.extension_processor',
    """
    return {
        'get_extensions': get_extensions,
    }