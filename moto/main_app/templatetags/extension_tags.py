# main_app/templatetags/extension_tags.py
from django import template
from main_app.registry import get_extensions

register = template.Library()

@register.simple_tag(takes_context=True)
def render_extensions(context, extension_point):
    """
    Render all extensions for a specific extension point.
    
    Example:
        {% render_extensions 'pupil_navigation_buttons' %}
    """
    return get_extensions(extension_point, context)