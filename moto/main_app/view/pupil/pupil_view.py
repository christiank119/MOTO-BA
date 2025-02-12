from django.shortcuts import redirect, render
from main_app.models import Student, Custom_user, Visit, Room_occupancy, Group, Pedagogical_specialist
from django.contrib.auth.decorators import login_required

@login_required(redirect_field_name="login")
def pupil_view(request, pupil):
    user = request.user
    schueler = Student.get_student_by_custom_user_id(id=pupil)
    if schueler:
        gruppe = schueler.group
        if(Pedagogical_specialist.objects.filter(custom_user=user).exists()):
            personal = Pedagogical_specialist.objects.get(custom_user=user)
            aufenthalt = None
            if(Visit.objects.filter(student=schueler).exists()):
                        aufenthalte = Visit.objects.filter(student=schueler)
                        if(aufenthalte.filter(timespan__endtime=None).exists()):
                            aufenthalt = aufenthalte.get(timespan__endtime=None)
            # if(personal in gruppe.gruppen_leiter.all()):
            aufenthalt = "Abgemeldet"
            aktuelle_ag = "Keine"
            if schueler.in_house == True:
                aufenthalt = "Nicht bekannt"
                if(schueler.wc == True):
                    aufenthalt = "Toilette"
                if(schueler.school_yard == True):
                    aufenthalt = "Schulhof"
                if(Visit.objects.filter(student=schueler, timespan__endtime__isnull = True).exists()):
                    aufenthalt = Visit.objects.get(student=schueler, timespan__endtime__isnull = True)
                    raum = aufenthalt.room
                    aufenthalt = "Raum " + raum.room_name
                    if(Room_occupancy.objects.filter(room=raum).exists):
                        r_b = Room_occupancy.objects.get(room=raum)
                        if not (r_b.ag==None):
                            aktuelle_ag = r_b.ag.name
            klassen = []
            for schueler1 in Student.objects.all():
                if not (schueler1.school_class in klassen):
                    klassen.append(schueler1.school_class)
            ogs_groups = Group.objects.all()
            
            if request.method == "POST":
                if 'change_button_ogs_group' in request.POST:
                    ogs_group = request.POST.get('ogs_group')
                    if(Group.objects.filter(name=ogs_group).exists()):
                        ogs_group = Group.objects.get(name=ogs_group)
                        schueler.group = ogs_group
                        schueler.save()
                        return redirect("/pupil/"+str(pupil))
                elif 'change_button_name_eb' in request.POST:
                    name_eb = request.POST.get('name_eb')
                    if not(name_eb==''):
                        schueler.name_lg = name_eb
                        schueler.save()
                elif 'change_button_kontakt_eb' in request.POST:
                    kontakt_eb = request.POST.get('kontakt_eb')
                    if not(kontakt_eb==''):
                        schueler.contact_lg = kontakt_eb
                        schueler.save()
                elif 'change_button_klasse' in request.POST:
                    klasse = request.POST.get('klasse')
                    if(klasse in klassen):
                        schueler.school_class = klasse
                        schueler.save()
                elif 'change_button_bus_kind' in request.POST:
                    bus_kind = request.POST.get('bus_kind')
                    if(bus_kind=='1'):
                        schueler.bus=True
                    elif(bus_kind=='2'):
                        schueler.bus=False
                    schueler.save()

            if schueler.bus == True:
                bus_kind = 'Ja'
            else:
                bus_kind = 'Nein'

            is_personal_gruppenleiter  = False
            gruppen_leiter = gruppe.supervisor.all()[0]
            gruppen_raum = gruppe.room
            if(Visit.objects.filter(room=gruppen_raum).exists()):
                r_b = Room_occupancy.objects.get(room=gruppen_raum)
                gruppen_leiter = r_b.ag.supervisor
            if not gruppe == None:
                if(personal in gruppe.supervisor.all() and gruppe.representative == None):
                    is_personal_gruppenleiter = True
                elif gruppe.representative == personal:
                    is_personal_gruppenleiter = True

            return render(request, "pupil/pupil.html", {"schueler":schueler, "nutzer":schueler.custom_user, "bus_kind":bus_kind, "aufenthalt":aufenthalt, "aktuelle_ag":aktuelle_ag, "ogs_groups":ogs_groups, "klassen":klassen, "user":user, "gruppen_leiter":gruppen_leiter, "is_personal_gruppenleiter":is_personal_gruppenleiter})
        
    return redirect("master_web")