from analysis_tool.models import RaumPlan, RaumPolygon
import json
from django.shortcuts import render

def raumplan_show(request, raumplan_id=1):
    raumplan = RaumPlan.objects.get(id=raumplan_id)
    
    # Fetch polygons and include room number from related Raum model
    polygons = RaumPolygon.objects.filter(raumplan=raumplan).select_related('raum')
    
    # Create the JSON structure manually
    polygon_json = []
    for polygon in polygons:
        polygon_json.append({
            'raum_id': polygon.raum_id,
            'raum_nr': polygon.raum.raum_nr,  # Get raum_nr from the related Raum object
            'polygon': polygon.polygon
        })
    
    polygon_json = json.dumps(polygon_json)
    
    return render(request, 'heatmap/visualisation.html', {
        'raumplan': raumplan,
        'polygon_json': polygon_json
    })