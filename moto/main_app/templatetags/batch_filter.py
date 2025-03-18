from django import template

register = template.Library()

@register.filter
def batch(value, n):
    n = int(n)
    result = []
    temp = []
    for index, item in enumerate(value, 1):
        temp.append(item)
        if index % n == 0:
            result.append(temp)
            temp = []
    if temp:
        result.append(temp)
    return result