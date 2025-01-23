from django.shortcuts import redirect, render
from main_app.models import Gruppe, Nutzer, Personal, Raum
def group_change_view(request, id):
    if request.user.is_authenticated:
        user = request.user
        if user.is_superuser:

            pasfree = []
            pasoccupied = []
            for pa in Personal.objects.all():
                if Gruppe.objects.filter(gruppen_leiter = pa).exists():
                    pasoccupied.append(pa)
                else:
                    pasfree.append(pa)

            roomsfree = []
            roomsoccupied = []
            for room in Raum.objects.all():
                if Gruppe.objects.filter(raum = room).exists():
                    roomsoccupied.append(room)
                else:
                    roomsfree.append(room)

            if Gruppe.objects.filter(id=id).exists():
                group = Gruppe.objects.get(id=id)
            else:
                if id == 0:
                    if request.method == "POST":
                        name = request.POST.get('name')
                        supervisor = request.POST.get('supervisor')
                        room = request.POST.get('room')
                        error = ""
                        if supervisor and supervisor.strip() and not supervisor == "0" and Personal.objects.filter(id=supervisor).exists():
                                    pa = Gruppe.objects.get(id=supervisor)
                                    if Gruppe.objects.filter(gruppen_leiter = pa).exists():
                                           error += "Fehler bei der Pädagogische Fachkraft\n"
                        else:
                                    error += "Fehler bei der Pädagogische Fachkraft\n"
                        if room and room.strip() and not room == "0" and Raum.objects.filter(id=room).exists():
                                    r = Gruppe.objects.get(id=room)
                                    if Gruppe.objects.filter(raum = r).exists():
                                           error += "Fehler bei dem Raum\n"
                        else:
                                    error += "Fehler bei dem Raum\n"
                        if not(name and name.strip()) or Gruppe.objects.filter(name=name).exists():
                                    error += "Fehler beim Namen\n"
                        if error == "":
                            student = None
                            g = Gruppe.objects.create(name=name, gruppen_leiter = pa, raum = r)
                            g.save()
                            return redirect("/choose_data/group/"+str(g.id))
                        else:
                                print("Error: "+ error)
                    return render(request, 'change_data_db/create_group.html',{"pasfree":pasfree,"pasoccupied":pasoccupied,"roomsfree":roomsfree,"roomsoccupied":roomsoccupied})
                return redirect("choose_data_group")

            if request.method == "POST":
                if 'change_object' in request.POST:
                    name = request.POST.get('name')
                    supervisor = request.POST.get('supervisor')
                    room = request.POST.get('room')
                    error = ""
                    if supervisor and supervisor.strip() and not supervisor == "0" and Personal.objects.filter(id=supervisor).exists():
                                current_supervisors = list(group.gruppen_leiter.all())
                                remaining_supervisors = []

                                # Überprüfen, welche Gruppenleiter entfernt werden sollen
                                for pa in current_supervisors:
                                    supervisor_choice = request.POST.get(f"supervisor_{pa.id}")

                                    if supervisor_choice == "1":
                                        continue  # Nicht hinzufügen zu den verbleibenden Supervisoren
                                    else:
                                        remaining_supervisors.append(pa)

                                # Sicherstellen, dass mindestens ein Gruppenleiter übrig bleibt
                                if len(remaining_supervisors) == 0:
                                    error += "Mindestens ein Gruppenleiter muss verbleiben.\n"
                                    return redirect('change_group_data', id=group.id)

                                # Änderungen anwenden: Entfernen der PAs, die ausgewählt wurden
                                for pa in current_supervisors:
                                    if pa not in remaining_supervisors:
                                        group.gruppen_leiter.remove(pa)

                                # Neuen Gruppenleiter hinzufügen, falls ausgewählt und gültig
                                new_supervisor_id = request.POST.get("supervisor")

                                if new_supervisor_id and new_supervisor_id != "0" and new_supervisor_id != "occupied" and Personal.objects.filter(id=new_supervisor_id).exists():
                                    new_supervisor = Personal.objects.get(id=new_supervisor_id)
                                    group.gruppen_leiter.add(new_supervisor)
                                else:
                                    error += "Fehler bei der Pädagogische Fachkraft\n"
                    if room and room.strip() and not room == "0" and Raum.objects.filter(id=room).exists():
                                r = Raum.objects.get(id=room)
                                if not Gruppe.objects.filter(raum = r).exists():
                                    group.raum = r
                                    group.save()
                    else:
                                error += "Fehler bei dem Raum\n"
                    if name and name.strip() and not Gruppe.objects.filter(name=name).exists():
                                group.name = name
                                group.save()
                elif 'delete_object' in request.POST:
                    group.delete()
                    return redirect('choose_data_group')
            return render(request, 'change_data_db/change_group.html',{"group":group,"pasfree":pasfree,"pasoccupied":pasoccupied,"roomsfree":roomsfree,"roomsoccupied":roomsoccupied})
        return redirect("master_web")
    return redirect("login")