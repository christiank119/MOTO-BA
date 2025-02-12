from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from main_app.models import Pedagogical_specialist
from django.contrib.auth.models import User

@login_required(redirect_field_name="login")
def preferences_view(request):
    user = request.user
    personal = Pedagogical_specialist.objects.get(user=user)
    if request.method == "POST":
        if 'change_button_username' in request.POST:
            username = request.POST.get("username")
            if not username == '':
                if not User.objects.filter(username=username).exists():
                    user.first_name = username
                    user.save()
        elif 'change_button_vorname' in request.POST:
            firstname = request.POST.get("firstname")
            if not firstname == '':
                personal.custom_user.first_name = firstname
                personal.custom_user.save()
        elif 'change_button_nachname' in request.POST:
            surname = request.POST.get("surname")
            if not surname == '':
                personal.custom_user.second_name = surname
                personal.custom_user.save()
    return render(request, 'preferences/preferences.html', {"user":user, "nutzer":personal.custom_user})