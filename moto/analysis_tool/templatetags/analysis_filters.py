from django import template
import builtins  # Import built-in functions to avoid name conflicts

register = template.Library()

@register.filter
def get_at_index(list_obj, index):
    """
    Get an item from a list by its index
    Usage: {{ my_list|get_at_index:index }}
    """
    try:
        return list_obj[index]
    except (IndexError, TypeError):
        return ""

@register.filter
def subtract(value, arg):
    """
    Subtract the arg from the value.
    Usage: {{ value|subtract:arg }}
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide_by(value, arg):
    """
    Divide the value by the arg.
    Usage: {{ value|divide_by:arg }}
    """
    try:
        return float(value) / float(arg) if float(arg) != 0 else 0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def multiply(value, arg):
    """
    Multiply the value by the arg.
    Usage: {{ value|multiply:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def minimum(value, arg):
    """
    Return the minimum of value and arg.
    Usage: {{ value|minimum:arg }}
    """
    try:
        return builtins.min(float(value), float(arg))
    except (ValueError, TypeError):
        return 0

@register.filter
def maximum(value, arg):
    """
    Return the maximum of value and arg.
    Usage: {{ value|maximum:arg }}
    """
    try:
        return builtins.max(float(value), float(arg))
    except (ValueError, TypeError):
        return 0