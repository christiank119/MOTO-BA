from django.shortcuts import render, redirect

def test(request):

    from main_app.models import AGKategorie, Schueler
    from analysis_tool.models import ExtendedAGKategorie

    eagk = ExtendedAGKategorie.objects.get(name = "Ernährung")
    stats = eagk.get_utilization_stats()
    print(stats)

    from analysis_tool.utils.compute_student_metrics import compute_metrics_for_student
    student = Schueler.objects.get(id=23)
    stats = compute_metrics_for_student(student=student)
    print(stats)
    print("Gesamt-OGS-Zeit: {:.2f} Stunden".format(stats.total_ogs_time))
    print("Durchschnittliche AG-Besuche pro Tag: {:.2f}".format(stats.avg_ag_per_day))
    
    # Ermitteln der Lieblings‑AGKategorie aus der Gesamtanalyse.
    if stats.favourite_ag_kategorie:
        favourite_category = stats.favourite_ag_kategorie
        print("Lieblings‑AGKategorie (nach verbrachter Zeit):", favourite_category.name)

    return redirect("master_web")