from django.shortcuts import redirect, render
from main_app.models import Group, Custom_user, Pedagogical_specialist, Room
def group_change_view(request, id):
    if request.user.is_authenticated:
        user = request.user
        if user.is_superuser:

            pasfree, pasoccupied = Pedagogical_specialist.get_free_and_occupied
            roomsfree, roomsoccupied = Room.get_free_and_occupied
            group = Group.get_by_id(id=id)

            if not group:
                if id == 0:
                    if request.method == "POST":
                        name = request.POST.get('name')
                        supervisor_id = request.POST.get('supervisor')
                        room_id = request.POST.get('room')
                        error = ""
                        ps = Pedagogical_specialist.get_by_id(supervisor_id)
                        room = Room.get_by_id(room_id)
                        group = Group.get_by_name(name=name)

                        if ps:
                            if Group.objects.filter(gruppen_leiter = ps).exists():
                                error += "Fehler bei der Pädagogische Fachkraft\n"
                        else:
                                    error += "Fehler bei der Pädagogische Fachkraft\n"
                        if room:
                                if Group.objects.filter(room = room).exists():
                                        error += "Fehler bei dem Raum\n"
                        else:
                                    error += "Fehler bei dem Raum\n"
                        if not group:
                                    error += "Fehler beim Namen\n"
                        if error == "":
                            student = None
                            g = Group.objects.create(name=name, supervisor = ps, room = room)
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
                    room_id = request.POST.get('room')
                    room = Room.get_by_id(id=room_id)
                    error = ""
                    if supervisor and supervisor.strip() and not supervisor == "0" and Pedagogical_specialist.objects.filter(id=supervisor).exists():
                                current_supervisors = list(group.supervisor.all())
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
                                        group.supervisor.remove(pa)

                                # Neuen Gruppenleiter hinzufügen, falls ausgewählt und gültig
                                new_supervisor_id = request.POST.get("supervisor")

                                if new_supervisor_id and new_supervisor_id != "0" and new_supervisor_id != "occupied" and Personal.objects.filter(id=new_supervisor_id).exists():
                                    new_supervisor = Pedagogical_specialist.objects.get(id=new_supervisor_id)
                                    group.supervisor.add(new_supervisor)
                                else:
                                    error += "Fehler bei der Pädagogische Fachkraft\n"
                    if room:
                        if not Group.objects.filter(raum = room).exists():
                            group.room = room
                            group.save()
                    else:
                                error += "Fehler bei dem Raum\n"
                    if name and name.strip() and not Group.objects.filter(name=name).exists():
                                group.name = name
                                group.save()
                elif 'delete_object' in request.POST:
                    group.delete()
                    return redirect('choose_data_group')
            return render(request, 'change_data_db/change_group.html',{"group":group,"pasfree":pasfree,"pasoccupied":pasoccupied,"roomsfree":roomsfree,"roomsoccupied":roomsoccupied})
        return redirect("master_web")
    return redirect("login")