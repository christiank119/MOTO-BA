from django.shortcuts import redirect, render
from main_app.models import Pedagogical_specialist
def select_pa_change_view(request):
    if request.user.is_authenticated:
        user = request.user
        if user.is_superuser:
            pas = Pedagogical_specialist.objects.select_related('custom_user').order_by('custom_user__firstname', 'custom_user__secondname')
            return render(request, 'change_data_db/select_pa.html',{"pas" : pas})
        return redirect("master_web")
    return redirect("login")