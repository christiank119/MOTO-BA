from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from main_app.models import Room, Room_history, Visit, Room_occupancy
from datetime import datetime, timedelta

@login_required(login_url="login")
def room_usage_history_view(request, raum):
    if(Room.objects.filter(room_name=raum).exists):
        raum = Room.objects.get(room_name=raum)
        raum_historien = Room_history.objects.filter(room=raum)
        list_histories = []
        for raum_historie in raum_historien:
            date = raum_historie.day.strftime("%d-%m-%y")
            start_time = raum_historie.timespan.starttime.strftime("%H:%M")
            time = start_time + " - " + raum_historie.timespan.endtime.strftime("%H:%M")
            number=0
            alle_schueler_im_raum = Visit.objects.filter(room=raum)
            auf = Visit.objects.filter(room=raum,timespan__starttime__gt=raum_historie.timespan.starttime,timespan__endtime__lte=raum_historie.timespan.endtime)
            # for schueler_in_raum in alle_schueler_im_raum:
            #     if raum_historie.zeitraum.startzeit < schueler_in_raum.zeitraum.startzeit:
            #         if schueler_in_raum.zeitraum.endzeit == None or schueler_in_raum.zeitraum.endzeit <= raum_historie.zeitraum.endzeit:
            #             number += 1
            schueler_ids = auf.values_list('schueler_id', flat=True)
            number = len(list(set(schueler_ids)))
            ag_kategorie = raum_historie.ag_category.name

            history = History(date, time, number, start_time, ag_kategorie)
            list_histories.append(history)
        if(Room_occupancy.objects.filter(room=raum).exists()):
            r_b = Room_occupancy.objects.get(room=raum)
            date = datetime.now().date().strftime("%d-%m-%y")
            start_time =  r_b.timespan.starttime.strftime("%H:%M")
            time = "Start - " + start_time
            kinder_in_raum = Visit.objects.filter(room = raum, timespan__endtime__isnull=True)      
            number = len(kinder_in_raum)
            ag_kategorie = r_b.ag.ag_category.name
            history = History(date, time, number, start_time, ag_kategorie)
            list_histories.append(history)

        list_histories = sorted(list_histories, key=custom_sort_key)
        return render(request, 'history_pages/room_usage_history.html', {"historien":list_histories,"raum":raum})
    return redirect('master_web')

class History:
    def __init__(self, date, time, number, start_time, kategorie):
        self.date = date
        self.time = time
        self.number = number
        self.start_time = start_time
        self.kategorie = kategorie

def custom_sort_key(history):
    now = datetime.now()
    date_time_str = history.date + ' ' + history.start_time
    history_time = datetime.strptime(date_time_str, "%d-%m-%y %H:%M")
    return abs((history_time - now).total_seconds())
