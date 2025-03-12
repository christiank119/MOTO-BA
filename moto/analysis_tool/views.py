from django.shortcuts import render, redirect
from analysis_tool.view.heatmap.edit import raumplan_edit
from analysis_tool.view.heatmap.save import save_polygon
from analysis_tool.view.heatmap.upload import upload_raumplan
from analysis_tool.view.heatmap.visualtisation import get_room_data
from analysis_tool.view.heatmap.show import raumplan_show

def test(request):

    from main_app.models import AGKategorie, Schueler, Nutzer, Raum
    from analysis_tool.models import ExtendedAGKategorie

    eagk = ExtendedAGKategorie.objects.get(name = "Ernährung")
    stats = eagk.get_utilization_stats()
    print(stats)

    from analysis_tool.utils.compute_student_metrics import compute_metrics_for_student
    student = Schueler.objects.get(user_id__id=23)
    stats = compute_metrics_for_student(student=student)
    print(stats)
    print("Gesamt-OGS-Zeit: {:.2f} Stunden".format(stats.total_ogs_time))
    print("Durchschnittliche AG-Besuche pro Tag: {:.2f}".format(stats.avg_ag_per_day))
    print(stats.favourite_ag_kategorie.name)

    # Ermitteln der Lieblings‑AGKategorie aus der Gesamtanalyse.
    if stats.favourite_ag_kategorie:
        favourite_category = stats.favourite_ag_kategorie
        print("Lieblings‑AGKategorie (nach verbrachter Zeit):", favourite_category.name)

    from analysis_tool.utils.compute_ag_category_metrics import compute_relative_time_ratios, compute_correlation_matrix, compute_association_rules, perform_cluster_analysis, perform_regression_analysis

    corr = compute_correlation_matrix()
    print(corr)


    ratios = compute_relative_time_ratios("Ernährung")
    for cat, ratio in ratios.items():
        print(f"{cat}: {ratio * 60:.1f} Minuten")

    reg_results = perform_regression_analysis("Sport", "Ernährung")
    if reg_results:
        print("\nRegressionsanalyse (Ernährung als Funktion von Sport):")
        print(f"Koeffizient: {reg_results['coefficient']:.2f}")
        print(f"Intercept: {reg_results['intercept']:.2f}")
        print(f"R^2: {reg_results['score']:.2f}")

    clustered_df = perform_cluster_analysis(n_clusters=3)
    print("\nClusteranalyse (erste 5 Zeilen):")
    print(clustered_df.head())
    
    # Assoziationsregeln (Platzhalter)
    assoc_rules = compute_association_rules()
    print("\nAssoziationsregeln:")
    print(assoc_rules)

    from analysis_tool.utils.compute_room_metrics import get_room_utilization, compute_room_spitzenzeiten, compare_rooms,compute_room_historical_trend, compute_room_capacity_analysis, compute_room_nutzer_profile

    # Wähle eine Beispielraum-ID (anpassen an deine Daten)
    r = Raum.objects.get(raum_nr = "10") 
    room_id = r.id
    util = get_room_utilization(room_id)
    print("Room Utilization Metrics:")
    print(util)
    
    spitzen = compute_room_spitzenzeiten(room_id)
    print("\nRoom Spitzenzeiten (Nutzung nach Stunde):")
    print(spitzen)
    
    comp_df = compare_rooms()
    print("\nVergleich der Räume:")
    print(comp_df)
    
    trend_df = compute_room_historical_trend(room_id)
    print("\nHistorischer Trend für Raum:", room_id)
    print(trend_df)
    
    cap_analysis = compute_room_capacity_analysis(room_id)
    print("\nKapazitätsanalyse für Raum:")
    print(cap_analysis)
    
    profile = compute_room_nutzer_profile(room_id)
    print("\nAG-Kategorien-Nutzerprofil (basierend auf Zeit) für Raum:")
    print(profile)


    return redirect("master_web")
