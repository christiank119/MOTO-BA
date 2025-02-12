from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from main_app.models import Visit, Pedagogical_specialist, Room_occupancy, Student
from django.db.models import Q

@login_required(login_url="login")
def search_pupil_view(request):
    schueler = Student.objects.all()
    len_sa = 0
    for s in schueler:
        if s.in_house:
            len_sa = len_sa + 1
    if request.method == 'POST':
        search = request.POST.get('search')
        if 'button_search' in request.POST:
            schueler2 = []
            for schueler1 in schueler:
                name = schueler1.custom_user.first_name + " " + schueler1.custom_user.second_name
                if(search.lower() in name.lower()):
                    schueler2.append(schueler1)
            schueler = schueler2
    schueler_active = []
    for s in schueler:
        if s.in_house:
            schueler_active.append(s)
    schueler_active = sorted(schueler_active, key=lambda schueler: (schueler.custom_user.firts_name, schueler.custom_user.second_name))
    return render(request, "search_pupil/search_pupil.html", {"schueler":schueler, "schueler_active":schueler_active, "len_sa":len_sa, "len_ss":len(schueler_active)})