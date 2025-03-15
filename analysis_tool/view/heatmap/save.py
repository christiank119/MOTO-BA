import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from analysis_tool.models import RaumPolygon, RaumPlan, Raum
from analysis_tool.forms import RaumPlanForm

def save_polygon(request):
    """
    Nimmt eine AJAX-POST-Anfrage entgegen und speichert die Polygonkoordinaten.
    Erwartet JSON-Daten mit:
      - raum_nr: die Raumnummer
      - raumplan_id: ID des Raumplans
      - polygon: Liste von Koordinaten (z. B. [{'x': 10, 'y': 20}, ...])
    """
    if request.method == "POST":
        data = json.loads(request.body)
        raum_nr = data.get('raum_nr')
        raumplan_id = data.get('raumplan_id')
        polygon = data.get('polygon')
        
        # Raum anhand der Raumnummer suchen
        try:
            raum = Raum.objects.get(raum_nr=raum_nr)
        except Raum.DoesNotExist:
            return JsonResponse({"success": False, "error": "Raum nicht gefunden."})
        
        # Raumplan laden
        try:
            raumplan = RaumPlan.objects.get(id=raumplan_id)
        except RaumPlan.DoesNotExist:
            return JsonResponse({"success": False, "error": "Raumplan nicht gefunden."})
        
        # Erstelle oder aktualisiere das Polygon
        RaumPolygon.objects.update_or_create(
            raum=raum,
            raumplan=raumplan,
            defaults={'polygon': polygon}
        )
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"success": False, "error": "Invalid request method."})
