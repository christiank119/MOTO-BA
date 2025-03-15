import pandas as pd
import numpy as np
from collections import defaultdict
from datetime import datetime, timedelta
from django.db.models import Sum, Avg, Count
from main_app.models import Raum
from analysis_tool.models import AGHistorie
from django.db.models import F
# Falls du auch Raum_Belegung-Daten hast, importiere diese:
# from main_app.models import Raum_Belegung

def get_room_utilization(room_id):
    """
    Berechnet aggregierte Auslastungsmetriken für einen bestimmten Raum.
    Dabei werden AGHistorie-Einträge (falls vorhanden) verwendet.

    Rückgabe:
      dict mit:
        - total_available_time: Summe der verfügbaren Zeit (Stunden)
        - total_actual_usage: Summe der tatsächlichen Nutzung (Stunden)
        - avg_utilization_percentage: Durchschnittliche Auslastung in Prozent
    """
    qs = AGHistorie.objects.filter(raum__id=room_id)
    agg = qs.aggregate(
        total_available_time=Sum('total_available_time'),
        total_actual_usage=Sum('actual_usage_time'),
        avg_utilization=Avg('utilization_percentage')
    )
    return {
        'total_available_time': agg.get('total_available_time') or 0.0,
        'total_actual_usage': agg.get('total_actual_usage') or 0.0,
        'avg_utilization_percentage': agg.get('avg_utilization') or 0.0,
    }

def compute_room_spitzenzeiten(room_id):
    """
    Ermittelt, zu welchen Tagesstunden ein Raum (basierend auf AGHistorie-Einträgen)
    genutzt wird. Dabei wird die Startzeit (Stunde) der AGHistorie als Indikator verwendet.
   
    Rückgabe:
      pandas.Series mit den Zählungen pro Stunde (0-23)
    """
    qs = AGHistorie.objects.filter(raum__id=room_id)
    data = []
    for entry in qs:
        hour = entry.zeitraum_start.hour
        data.append(hour)
    if not data:
        # Create a Series with zeros for all 24 hours instead of empty data
        return pd.Series(data=[0] * 24, index=range(24))
    series = pd.Series(data)
    counts = series.value_counts().sort_index()
    # Fülle fehlende Stunden mit 0
    counts = counts.reindex(range(24), fill_value=0)
    return counts


def compare_rooms():
    """
    Vergleicht alle Räume anhand zentraler Metriken, die in AGHistorie gesammelt wurden.
    Liefert einen DataFrame, in dem jeder Raum als Zeile erscheint und Kennzahlen wie
    durchschnittliche Auslastung, Gesamtnutzung und Anzahl der AG-Events dargestellt werden.

    Rückgabe:
      pandas.DataFrame
    """
    qs = AGHistorie.objects.values('raum__id', 'raum__raum_nr').annotate(
        total_available=Sum('total_available_time'),
        total_actual_usage=Sum('actual_usage_time'),
        avg_utilization=Avg('utilization_percentage'),
        events=Count('id')
    )
    df = pd.DataFrame(list(qs))
    if df.empty:
        return df
    df.rename(columns={'raum__id': 'room_id', 'raum__raum_nr': 'room_number'}, inplace=True)
    return df

def compute_room_historical_trend(room_id):
    """
    Erstellt eine Zeitreihe (DataFrame), die den Verlauf der Nutzung eines Raumes
    über die Zeit (auf Tagesbasis) darstellt. Grundlage sind AGHistorie-Einträge.
    
    Rückgabe:
      pandas.DataFrame mit Index als Datum und Spalten:
        - total_available_time (Stunden)
        - total_actual_usage (Stunden)
        - avg_utilization_percentage
        - event_count
    """
    qs = AGHistorie.objects.filter(raum__id=room_id)
    # Gruppiere nach Datum (hier: zeitraum_start Datum)
    trends = qs.extra(select={'date': "DATE(zeitraum_start)"}).values('date').annotate(
        total_available=Sum('total_available_time'),
        total_usage=Sum('actual_usage_time'),
        avg_utilization=Avg('utilization_percentage'),
        events=Count('id')
    ).order_by('date')
    df = pd.DataFrame(list(trends))
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
    return df

def compute_room_capacity_analysis(room_id):
    """
    Berechnet, wie oft ein Raum an seiner Kapazitätsgrenze betrieben wurde.
    Hierzu wird aus AGHistorie ermittelt, bei wie vielen Einträgen die
    peak_participants gleich der max_anzahl war.
    
    Rückgabe:
      dict mit:
        - total_events: Anzahl der AGHistorie-Einträge
        - full_capacity_events: Anzahl der Einträge, bei denen peak_participants == max_anzahl
        - full_capacity_percentage: Prozentualer Anteil
    """
    qs = AGHistorie.objects.filter(raum__id=room_id)
    total_events = qs.count()
    full_events = qs.filter(peak_participants=F('max_anzahl')).count()
    percentage = (full_events / total_events * 100.0) if total_events > 0 else 0.0
    return {
        'total_events': total_events,
        'full_capacity_events': full_events,
        'full_capacity_percentage': percentage,
    }

def compute_room_capacity_time_analysis(room_id):
    """
    Berechnet, wie lange ein Raum voll ausgelastet war im Verhältnis zur gesamten
    Nutzungsdauer der AGs in diesem Raum.
    
    Für jeden AGHistorie-Eintrag wird die Dauer (in Stunden) ermittelt anhand der 
    Differenz zwischen zeitraum_end und zeitraum_start. Die voll ausgelastete Zeit 
    wird als (Dauer * fully_utilized_percentage / 100) berechnet.
    
    Rückgabe:
      dict mit:
        - total_time: Gesamtdauer der AGs in Stunden
        - full_time: Summe der Zeit in Stunden, in der die AG voll ausgelastet war
        - full_percentage: Prozentualer Anteil der voll ausgelasteten Zeit an der 
                           Gesamtdauer
    """
    qs = AGHistorie.objects.filter(raum__id=room_id)
    total_time = 0.0
    full_time = 0.0
    for event in qs:
        # Berechne die Dauer in Stunden
        duration = (event.zeitraum_end - event.zeitraum_start).total_seconds() / 3600.0
        total_time += duration
        # Berechne, wie lange die AG voll ausgelastet war
        full_time += duration * (event.fully_utilized_percentage / 100.0)
    percentage = (full_time / total_time * 100.0) if total_time > 0 else 0.0
    return {
        'total_time': total_time,
        'full_time': full_time,
        'full_percentage': percentage,
    }

# Weitere Funktionen für Nutzerprofile und Raumpräferenzen:
def compute_room_nutzer_profile(room_id):
    """
    Ermittelt, welche AG-Kategorien in einem Raum am häufigsten genutzt werden.
    Hier wird angenommen, dass AGHistorie-Einträge genutzt werden. Es wird pro
    Raum die Gesamtzeit je AG-Kategorie aggregiert.
    
    Rückgabe:
      pandas.Series, sortiert nach verbrachter Zeit
    """
    qs = AGHistorie.objects.filter(raum__id=room_id, ag_kategorie__isnull=False)
    data = {}
    for entry in qs:
        cat = entry.ag_kategorie.name
        data[cat] = data.get(cat, 0) + entry.actual_usage_time
    series = pd.Series(data)
    return series.sort_values(ascending=False)

# Beispielaufrufe (als Testfall, falls du dies direkt ausführen möchtest):
if __name__ == "__main__":
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
