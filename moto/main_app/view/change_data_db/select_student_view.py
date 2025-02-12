from django.shortcuts import redirect, render
from main_app.models import Student
def select_student_change_view(request):
    if request.user.is_authenticated:
        user = request.user
        if user.is_superuser:
            students = Student.objects.select_related('custom_user').order_by('custom_user__firstname', 'custom_user__secondname')
            return render(request, 'change_data_db/select_student.html',{"students" : students})
        return redirect("master_web")
    return redirect("login")