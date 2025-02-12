from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from main_app.models import Pedagogical_specialist, Group, Student, Visit, Room_occupancy

@login_required(redirect_field_name="login")
def dashboard_view(request):
    user = request.user
    personal = Pedagogical_specialist.objects.get(user=user)

    schuelers_in_room = {}
    schuelers_at_home = {}
    schuelers_in_movement = {}

    try:
        if Group.objects.filter(supervisor=personal).exists():
            ogs_gruppen = Group.objects.filter(supervisor=personal)
            ogs_group = ogs_gruppen[0]
        elif Group.objects.filter(representative=personal).exists():
            ogs_group = Group.objects.get(representative=personal)
        ogs_group_room = ogs_group.room
        schuelers = Student.objects.filter(group=ogs_group)
        schuelers_in_room = Visit.objects.filter(timespan__endtime__isnull=True, student__in=schuelers, room=ogs_group_room)
        schuelers_at_home = schuelers.filter(in_house = False)
        schuelers_in_movement = schuelers.filter(in_house=True)
        schuelers_in_movement = schuelers_in_movement.exclude(id__in=schuelers_in_room.values('student'))
    except:
        ogs_group = None

    

    rooms_group_room = Room_occupancy.objects.filter(ag__ag_category__name="Gruppenraum")
    rooms_learn = Room_occupancy.objects.filter(ag__ag_category__name="Lernen")
    rooms_sport = Room_occupancy.objects.filter(ag__ag_category__name="Sport")
    rooms_pause = Room_occupancy.objects.filter(ag__ag_category__name="Ruhe")
    rooms_creative = Room_occupancy.objects.filter(ag__ag_category__name="Kreativ")
    rooms_nature = Room_occupancy.objects.filter(ag__ag_category__name="Natur")
    rooms_food = Room_occupancy.objects.filter(ag__ag_category__name="Ernährung")
    rooms_other = Room_occupancy.objects.filter(ag__ag_category__name="Sonstige")

    return render(request, "dashboard/dashboard.html",
                  {"students_in_room":len(schuelers_in_room),
                   "students_at_home":len(schuelers_at_home),
                   "students_in_movement":len(schuelers_in_movement),
                   "rooms_group":len(rooms_group_room),
                   "rooms_sport":len(rooms_sport),
                   "rooms_learn":len(rooms_learn),
                   "rooms_food":len(rooms_food),
                   "rooms_creative":len(rooms_creative),
                   "rooms_nature":len(rooms_nature),
                   "rooms_break":len(rooms_pause),
                   "rooms_other":len(rooms_other),
                   "ogs_group":ogs_group,
                   })