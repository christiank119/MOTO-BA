from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from main_app.models import Group, Pedagogical_specialist

@login_required(redirect_field_name="login")
def representation_view(request):
    user = request.user
    if user.is_superuser:
        if request.method == "POST":
            if "change_button_representation" in request.POST:
                gruppe_name = request.POST.get("change_button_representation")
                neue_vertretung = request.POST.get("representation_"+gruppe_name)
                if Pedagogical_specialist.objects.filter(user__username=neue_vertretung).exists():
                    p_neu = Pedagogical_specialist.objects.get(user__username=neue_vertretung)
                    if Group.objects.filter(representative=p_neu).exists():
                        gruppe = Group.objects.get(representative=p_neu)
                        gruppe.representative = None
                        gruppe.save()
                    # gruppe_name = request.POST.get("group")
                    if Group.objects.filter(name=gruppe_name).exists():
                        gruppe = Group.objects.get(name=gruppe_name)
                        gruppe.representative = p_neu
                        gruppe.save()
        users = Pedagogical_specialist.objects.all()
        # raum_belegung_ids = Raum_Belegung.objects.filter(aufsichtspersonen__in=users).values_list('id', flat=True)
        # users = users.exclude(raum_belegung__id__in=raum_belegung_ids)
        groups = Group.objects.all().order_by('name')
        return render(request, 'representation/representation.html', {"groups": groups,"users":users})
    return redirect("master_web")