from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from main_app.models import Pedagogical_specialist, Group, Student
from django.contrib.auth.models import User

@login_required(redirect_field_name="login")
def ogs_group_view(request):

    user = request.user
    search = ''
    personal = Pedagogical_specialist.get_ps_by_custom_user_id(user)
    if personal:
        gruppe = None
        schueler = None
        if(Group.objects.filter(supervisor=personal).exists()):
            gruppe = Group.objects.filter(supervisor=personal)[0]
            if gruppe.representative == None:
                gruppe = None
        if(Group.objects.filter(represenative=personal).exists()):
            gruppe = Group.objects.get(representative=personal) 
        if not gruppe == None:
            schueler = Student.objects.filter(group=gruppe)
            if request.method == 'POST':
                search = request.POST.get('search')
                if 'button_search' in request.POST:
                    schueler2 = []
                    for schueler1 in schueler:
                        name = schueler1.custom_user.first_name + " " + schueler1.custom_user.second_name
                        if(search.lower() in name.lower()):
                            schueler2.append(schueler1)
                    schueler = schueler2
        else:
            #fehler Nachricht?
            return redirect("master_web")  
    else:
        #fehler Nachricht?
        return redirect("master_web")
    schueler_active = []
    schueler_passiv = []
    for s in schueler:
        if s.in_house:
            schueler_active.append(s)
        else:
            schueler_passiv.append(s)
    schueler_active = sorted(schueler_active, key=lambda schueler: (schueler.custom_user.first_name, schueler.custom_user.second_name))
    schueler_passiv = sorted(schueler_passiv, key=lambda schueler: (schueler.custom_user.first_name, schueler.custom_user.second_name))

    return render(request, "ogs_group/ogs_group.html",{"schueler_active":schueler_active, "schueler_passiv":schueler_passiv, "search":search, "group_name":gruppe.name})