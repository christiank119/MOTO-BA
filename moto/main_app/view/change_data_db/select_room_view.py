from django.shortcuts import redirect, render
from main_app.models import Room
def select_room_change_view(request):
    if request.user.is_authenticated:
        user = request.user
        if user.is_superuser:
            raeume = Room.objects.order_by('room_name')
            return render(request, 'change_data_db/select_room.html',{"raeume" : raeume})
        return redirect("master_web")
    return redirect("login")