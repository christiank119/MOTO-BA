from django import template

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