from django.shortcuts import redirect, render
from main_app.models import Room
def room_change_view(request, id):
    if request.user.is_authenticated:
        user = request.user
        if user.is_superuser:
            room = Room.get_by_id(id=id)
            if not room:
                if id == 0:
                    if request.method == "POST":
                        name = request.POST.get('name')
                        building = request.POST.get('building')
                        capazity = request.POST.get('capazity')
                        category = request.POST.get('category')
                        error = ""
                        if not(name and name.strip()) or Room.objects.filter(room_name=name).exists():
                                    error += "Fehler beim Namen\n"
                        if not(building and building.strip()):
                                    error += "Fehler beim Geschoss / Gebäude\n"
                        if not(category and category.strip()):
                                    error += "Fehler beim Namen der Kategorie\n"
                        try:
                            capa = int(capazity)
                        except ValueError:
                            error += "Fehler beim Kapazität\n"
                        if error == "":
                            new_room = Room.objects.create(room_name=name, building = building, capacity = capa, category=category)
                            new_room.save()
                            return redirect("/choose_data/room/"+str(room.id))
                        else:
                                print("Error: "+ error)
                    return render(request, 'change_data_db/create_room.html')
                return redirect("choose_data_room")

            if request.method == "POST":
                name = request.POST.get('name')
                building = request.POST.get('building')
                capazity = request.POST.get('capazity')
                category = request.POST.get('category')
                error = ""
                if name and name.strip() and not Room.objects.filter(room_name=name).exists():
                            room.room_name = name
                            room.save()
                if building and building.strip():
                            room.building = building
                            room.save()
                if category and category.strip():
                            room.category = category
                            room.save()
                if capazity and capazity.strip():
                    try:
                                capa = int(capazity)
                                room.capacity = capa
                                room.save()
                    except ValueError:
                        print()
                
            return render(request, 'change_data_db/change_room.html',{"room" : room})
        return redirect("master_web")
    return redirect("login")