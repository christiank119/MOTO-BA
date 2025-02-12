from django.shortcuts import redirect, render
from main_app.models import Room
from django.contrib.auth.decorators import login_required

@login_required(redirect_field_name="login")
def room_selection_view(request, raum):
    if(Room.objects.filter(room_name=raum).exists()):
        raum = Room.objects.get(room_name=raum)
        return render(request, 'room_selection/room_selection.html', {"raum":raum})
    return redirect('master_web')