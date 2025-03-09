

def is_mobile(request):
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    mobile_keywords = ['mobile', 'android', 'iphone', 'ipad']
    return any(keyword in user_agent for keyword in mobile_keywords)

def user_has_ogs(request):
    if not request.user.is_authenticated:
        return False
    has_ogs = False
    from main_app.models import Personal, Gruppe
    try:
        personal = Personal.objects.get(user=request.user)
        if Gruppe.objects.filter(gruppen_leiter=personal, vertreter__isnull=True).exists() or \
           Gruppe.objects.filter(vertreter=personal).exists():
            has_ogs = True
    except Personal.DoesNotExist:
        pass
    return has_ogs

def user_is_superuser(request):
    return request.user.is_superuser