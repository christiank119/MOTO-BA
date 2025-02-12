from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from main_app.models import Pedagogical_specialist, Group

def master_web_view(request):
    if request.user.is_authenticated:
        user = request.user
        has_ogs = False
        personal = Pedagogical_specialist.get_ps_by_custom_user_id(id=user)
        if personal:
            if(Group.objects.filter(supervisor=personal).exists()):
                gruppe = Group.objects.get(supervisor=personal)
                if gruppe.representative == None:
                    has_ogs = True    
            if Group.objects.filter(representative=personal).exists():
                has_ogs = True
        return render(request, 'master_overview/master_web.html', {"user":user, "has_ogs":has_ogs})
    else:
        return redirect("login")