import json
from django.shortcuts import render, redirect, get_object_or_404
from analysis_tool.models import RaumPolygon, RaumPlan, Raum

def raumplan_edit(request, raumplan_id=1):
    """
    Zeigt den Raumplan mit Bild-Overlay und vorhandenen Polygonen an.
    """
    raumplan = get_object_or_404(RaumPlan, id=raumplan_id)
    # Alle Polygone zu diesem Raumplan laden
    raum_polygone = RaumPolygon.objects.filter(raumplan=raumplan)
    polygon_data = []
    for rp in raum_polygone:
        polygon_data.append({
            "raum_id": rp.raum.id,
            "raum_nr": rp.raum.raum_nr,
            "polygon": rp.polygon,
        })
    
    context = {
        "raumplan": raumplan,
        "polygon_json": json.dumps(polygon_data)
    }
    return render(request, 'heatmap/edit.html', context)