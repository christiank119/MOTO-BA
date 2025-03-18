import json
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from analysis_tool.models import RaumPolygon, RaumPlan, AGHistorie
from main_app.models import Raum
from datetime import datetime, timedelta

@require_GET
def get_room_data(request):
    """
    Liefert alle Raumdaten für die Heatmap-Visualisierung als JSON.
    Enthält:
    - Raum-Metriken (Auslastung, Nutzung, etc.)
    - Stündliche Nutzungsdaten (für Spitzenzeiten)
    - Trend-Daten (für historische Entwicklung)
    """
    from analysis_tool.utils.compute_room_metrics import (
        get_room_utilization, 
        compute_room_spitzenzeiten,
        compute_room_historical_trend,
        compute_room_capacity_time_analysis,
        compute_room_capacity_analysis
        )
    
    # Räume mit Polygonen für diesen Raumplan
    rooms = Raum.objects.all()
    
    # Initialisiere Ergebnisstrukturen
    rooms_data = {}
    hourly_data = {}
    trend_data = {}
    
    # Sammle Daten für jeden Raum
    for room in rooms:
        # Überlaufdaten
        room_id = room.id
        room_metrics = get_room_utilization(room_id)
        capacity_metrics = compute_room_capacity_analysis(room_id)
        capacity_metrics2 = compute_room_capacity_time_analysis(room_id)
        
        # Stündliche Nutzungsdaten
        spitzenzeiten = compute_room_spitzenzeiten(room_id)
        hourly_counts = {}
        for hour in range(24):
            hourly_counts[hour] = int(spitzenzeiten.get(hour, 0))
        
        # Trend-Daten
        trend_df = compute_room_historical_trend(room_id)
        trend_info = {"dates": [], "utilization": []}
        
        if not trend_df.empty:
            # Konvertiere Datumsindex zu Stringliste
            dates = trend_df.index.strftime('%Y-%m-%d').tolist()
            trend_info["dates"] = dates
            trend_info["utilization"] = trend_df['avg_utilization'].tolist()
        
        # Zusammenführen aller Metriken
        rooms_data[room_id] = {
            "avg_utilization_percentage": room_metrics['avg_utilization_percentage'],
            "total_actual_usage": room_metrics['total_actual_usage'],
            "full_capacity_percentage": capacity_metrics2['full_percentage'],
            "events": capacity_metrics['total_events']
        }
        
        hourly_data[room_id] = hourly_counts
        trend_data[room_id] = trend_info
    
    # Alle Daten zurückgeben
    return JsonResponse({
        "rooms": rooms_data,
        "hourly": hourly_data,
        "trends": trend_data
    })