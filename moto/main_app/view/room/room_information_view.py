from django.shortcuts import redirect, render
from main_app.models import Room, Room_occupancy, Group, Visit
from django.contrib.auth.decorators import login_required

@login_required(redirect_field_name="login")
def room_information_view(request, raum):
    if(Room.objects.filter(room_name=raum).exists()):
        raum = Room.objects.get(room_name=raum)
        raum_belegung = 'Keine'
        ogs_group, nutzungstyp, aufsichtsperson, aktuelle_kinderanzahl, is_room_active, r_b = [None, None, None, None, False, None]
        if(Room_occupancy.objects.filter(room=raum).exists()):
            is_room_active = True
            r_b = Room_occupancy.objects.get(room=raum)
            if not(r_b.ag == None):
                raum_belegung = r_b.ag.name
                nutzungstyp = r_b.ag.ag_category.name
                aufsichtsperson = r_b.ag.supervisor.custom_user.first_name + " " + r_b.ag.supervisor.custom_user.second_name
            elif not (r_b.group==None):
                gruppe = Group.objects.get(raum=raum)
                ogs_group = gruppe.name
                raum_belegung = "Gruppenraum"
                aufsichtsperson = gruppe.supervisor.custom_user.first_name + " " + gruppe.supervisor.custom_user.second_name
        if(Group.objects.filter(room=raum).exists()):
            gruppe = Group.objects.get(room=raum)
            ogs_group = gruppe.name
        kinder_in_raum = Visit.objects.filter(room = raum, timespan__endtime__isnull=True)
        
        aktuelle_kinderanzahl = len(kinder_in_raum)
        #print(raum_belegung)

        return render(request, 'room_information/room_information.html', {"raum":raum,
                                        "aktuelle_kinderanzahl":aktuelle_kinderanzahl,
                                        "aufsichtsperson":aufsichtsperson,
                                        "ogs_gruppe":ogs_group,
                                        "nutzungstyp":nutzungstyp,
                                        "raum_belegung":raum_belegung,
                                        "is_room_active":is_room_active,
                                        "r_b":r_b,
                                        })
    return redirect('master_web')