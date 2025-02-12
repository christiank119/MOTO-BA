from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from main_app.models import Room_occupancy, Visit, Custom_user, Student, Room_history
from datetime import datetime

@login_required(redirect_field_name="login")
def room_history_view(request, pupil):
    schueler = Student.get_student_by_custom_user_id(id=pupil)
    if schueler:
        aufenthalte = Visit.objects.filter(student = schueler)
        hist = []
        for aufenthalt in aufenthalte:
            zeitraum = aufenthalt.timespan
            startzeit = zeitraum.starttime
            endzeit = zeitraum.endtime
            raum = aufenthalt.room
            kategorie = "Gruppenraum"
            raum_historie = None
            if not endzeit == None:
                #endzeit = endzeit.strftime("%H:%M")
                if(Room_history.objects.filter(room=raum,timespan__starttime__lte=startzeit,timespan__endtime__gte=endzeit).exists()):
                    if(len(Room_history.objects.filter(room=raum,timespan__starttime__lte=startzeit,timespan__endtime__gte=endzeit))>1):
                        raum_historie = Room_history.objects.filter(room=raum,timespan__starttime__lte=startzeit,timespan__endtime__gte=endzeit)[0]
                    else:
                        raum_historie = Room_history.objects.get(room=raum,timespan__starttime__lte=startzeit,timespan__endtime__gte=endzeit)
                    if not raum_historie.ag_category == None:
                        kategorie = raum_historie.ag_category.name
                if(Room_occupancy.objects.filter(room=raum,timespan__starttime__lte=startzeit,timespan__endtime__isnull=True).exists()):
                    r_b = Room_occupancy.objects.get(room=raum,timespan__starttime__lte=startzeit,timespan__endtime__isnull=True)
                    if not r_b.ag.ag_category == None:
                        kategorie = r_b.ag.ag_category.name
                endzeit = endzeit.strftime("%H:%M")
            elif(Room_occupancy.objects.filter(room=raum).exists()):
                r_b = Room_occupancy.objects.get(room=raum)
                endzeit = "In Benutzung"
                if not r_b.ag.ag_category == None:
                    kategorie = r_b.ag.ag_category.name
            
            
            history = History(date=aufenthalt.day.strftime("%d.%m.%y"),start_time=startzeit.strftime("%H:%M"),end_time=endzeit,kategorie=kategorie,raum=raum)
            hist.append(history)
        hist = sorted(hist, key=custom_sort_key)
        return render(request, 'history_pages/room_history.html', {"historys":hist,"user":schueler.custom_user, 'pupil':pupil})
    return redirect("master_web")

class History:
    def __init__(self, date, start_time, end_time, kategorie, raum):
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.kategorie = kategorie
        self.raum = raum

def custom_sort_key(history):
    now = datetime.now()
    date_time_str = history.date + ' ' + history.start_time
    history_time = datetime.strptime(date_time_str, "%d.%m.%y %H:%M")
    return abs((history_time - now).total_seconds())
