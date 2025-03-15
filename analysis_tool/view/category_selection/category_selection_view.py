from django.shortcuts import redirect, render
from main_app.models import AGKategorie
from django.contrib.auth.decorators import login_required

@login_required(redirect_field_name="login")
def category_selection_view(request):
    category = AGKategorie.objects.all()
    tup_list_cat = []
    for i in range(0, len(category), 2):
        if i + 1 < len(category):
            room1 = category[i]
            room2 = category[i + 1]
            tup = Tup(room1,room2)
            tup_list_cat.append(tup)
    if len(category) % 2 == 1:
        room = category[len(category)-1]
        tup = Tup(room,None)
        tup_list_cat.append(tup)
    return render(request, 'category_selection/category_selection.html', {'categories':tup_list_cat})

class Tup:
    def __init__(self, room1, room2):
        self.room1 = room1
        self.room2 = room2