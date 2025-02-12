from django.shortcuts import redirect, render
from main_app.models import Student, Group, Custom_user
def student_change_view(request, id):
    if request.user.is_authenticated:
        user = request.user
        if user.is_superuser:

            klassen = []
            for all_students in Student.objects.all():
                if not (all_students.klasse in klassen):
                    klassen.append(all_students.klasse)

            if Student.objects.filter(id=id).exists():
                student = Student.objects.get(id=id)
            else:
                if id == 0:
                    if request.method == "POST":
                        group_name = request.POST.get('ogs_group')
                        firstname = request.POST.get('firstname')
                        lastname = request.POST.get('lastname')
                        name_eb = request.POST.get('name_eb')
                        kontakt_eb = request.POST.get('kontakt_eb')
                        klasse = request.POST.get('klasse')
                        buskind = request.POST.get('bus_kind')
                        tag_id = request.POST.get('tag_id')
                        error = ""
                        group = Group.get_by_name(name=group_name)
                        if not group:
                                    error += "Fehler bei der OGS-Gruppe\n"
                        if not(firstname and firstname.strip()):
                                    error += "Fehler beim Vornamen\n"
                        if not(lastname and lastname.strip()):
                                    error += "Fehler beim Nachname\n"
                        if not(name_eb and name_eb.strip()):
                                    error += "Fehler beim Namen der Kontaktperson\n"
                        if not(kontakt_eb and kontakt_eb.strip()):
                                    error = "Fehler beim der Kontaktnummer\n"
                        if (buskind=='1'):
                                    bus_kind = True
                        elif (buskind=='2'):
                                    bus_kind = False
                        else:
                                    error = "Fehler bei der Angabe zum Bus\n"
                        b_tag_id = False
                        if(tag_id and tag_id.strip()):
                                    b_tag_id = True
                        if not(klasse in klassen):
                                    error = "Fehler beim der Klasse\n"
                        if error == "":
                            student = None
                            if b_tag_id == True:
                                new_nutzer = Custom_user.objects.create(first_name=firstname,second_name=lastname, tag_id=tag_id)
                                student = Student.objects.create(school_class=klasse, bus=bus_kind, name_lg=name_eb, contact_lg=kontakt_eb, custom_user=new_nutzer,group=group)
                                student.save()
                            else:
                                new_nutzer = Custom_user.objects.create(first_name=firstname,second_name=lastname)
                                student = Student.objects.create(school_class=klasse, bus=bus_kind, name_lg=name_eb, contact_lg=kontakt_eb, custom_user=new_nutzer,group=group)
                                student.save()
                            return redirect("/choose_data/student/"+str(student.id))
                        else:
                                print("Error: "+ error)
                    return render(request, 'change_data_db/create_student.html',{"ogs_groups":Group.objects.all(),"klassen":klassen})
                return redirect("choose_data_student")

            if request.method == "POST":
                ogs_group = request.POST.get('ogs_group')
                firstname = request.POST.get('firstname')
                lastname = request.POST.get('lastname')
                name_eb = request.POST.get('name_eb')
                kontakt_eb = request.POST.get('kontakt_eb')
                klasse = request.POST.get('klasse')
                buskind = request.POST.get('bus_kind')
                tag_id = request.POST.get('tag_id')
                if(ogs_group and ogs_group.strip() and not ogs_group == "0" and Group.objects.filter(name=ogs_group).exists()):
                            ogs_group = Group.objects.get(name=ogs_group)
                            student.group = ogs_group
                            student.save()
                if(firstname and firstname.strip()):
                            student.custom_user.first_name = firstname
                            student.custom_user.save()
                if(lastname and lastname.strip()):
                            student.custom_user.second_name = lastname
                            student.custom_user.save()
                if(name_eb and name_eb.strip()):
                            student.name_lg = name_eb
                            student.save()
                if(kontakt_eb and kontakt_eb.strip()):
                            student.contact_lg = kontakt_eb
                            student.save()
                if(buskind=='1'):
                            student.bus=True
                            student.save()
                elif(buskind=='2'):
                            student.bus=False
                            student.save()
                if(tag_id and tag_id.strip()):
                            student.custom_user.tag_id = tag_id
                            student.custom_user.save()
                if(klasse in klassen):
                            student.school_class = klasse
                            student.save()
                            #return redirect("/choose_data/student/"+str(student.id))
            bus_kind = "Nein"
            if student.bus == True:
                bus_kind = "Ja"
            return render(request, 'change_data_db/change_student.html',{"student" : student, "ogs_groups":Group.objects.all(),"klassen":klassen, "bus_kind":bus_kind})
        return redirect("master_web")
    return redirect("login")