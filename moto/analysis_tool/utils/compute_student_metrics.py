from django.db.models import Min, Max
from main_app.models import Schueler, Aufenthalt, Raum_Belegung, AG, Zeitraum
from analysis_tool.models import (
    StudentOverallAnalysis,
    StudentAGCategoryAnalysis,
    StudentSessionBuffer
)
from datetime import datetime, timedelta
from collections import defaultdict

# Hilfsfunktionen
def combine_datetime(date, time_obj):
    return datetime.combine(date, time_obj)

def compute_overlap(start1, end1, start2, end2):
    latest_start = max(start1, start2)
    earliest_end = min(end1, end2)
    delta = (earliest_end - latest_start).total_seconds()
    return max(0, delta) / 3600.0

def merge_intervals(intervals, gap_threshold=timedelta(minutes=15)):
    if not intervals:
        return []
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    for current in intervals[1:]:
        last = merged[-1]
        if current[0] - last[1] <= gap_threshold:
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)
    return merged

def update_session_buffer_for_student(student):
    """
    Aktualisiert den Zwischenspeicher für einen Schüler inkrementell.
    Es werden nur neue oder geänderte Sitzungen hinzugefügt bzw. aktualisiert,
    anstatt alle bisherigen Einträge zu löschen.
    """
    # Bestehende Buffer-Einträge anhand eines eindeutigen Schlüssels ermitteln.
    existing_entries = {}
    for entry in StudentSessionBuffer.objects.filter(student=student):
        key = (entry.session_date, entry.session_start, entry.session_end)
        existing_entries[key] = entry

    attendances = Aufenthalt.objects.filter(schueler_id=student)
    for a in attendances:
        try:
            att_start = combine_datetime(a.tag, a.zeitraum.startzeit)
            att_end = combine_datetime(a.tag, a.zeitraum.endzeit)
        except Exception:
            continue  # Ungültige Daten überspringen.
        sessions = Raum_Belegung.objects.filter(raum=a.raum_id)
        for session in sessions:
            try:
                session_start = combine_datetime(a.tag, session.zeitraum.startzeit)
                # Wichtige Anpassung: Falls die Endzeit in der Raum_Belegung fehlt,
                # wird als Fallback der Endzeitpunkt des Aufenthalts genutzt.
                if session.zeitraum.endzeit:
                    session_end = combine_datetime(a.tag, session.zeitraum.endzeit)
                else:
                    session_end = att_end
            except Exception:
                continue
            overlap = compute_overlap(att_start, att_end, session_start, session_end)
            if overlap > 0:
                interval_start = max(att_start, session_start)
                interval_end = min(att_end, session_end)
                duration = (interval_end - interval_start).total_seconds() / 3600.0
                key = (a.tag, interval_start, interval_end)
                if key in existing_entries:
                    entry = existing_entries[key]
                    entry.duration = duration
                    entry.ag = session.ag if hasattr(session, 'ag') else None
                    entry.ag_kategorie = session.ag.ag_kategorie if session.ag and hasattr(session.ag, 'ag_kategorie') else None
                    entry.is_offered = session.ag.offene_AG if session.ag and hasattr(session.ag, 'offene_AG') else False
                    entry.save()
                else:
                    StudentSessionBuffer.objects.create(
                        student=student,
                        session_date=a.tag,
                        session_start=interval_start,
                        session_end=interval_end,
                        duration=duration,
                        ag=session.ag if hasattr(session, 'ag') else None,
                        ag_kategorie=session.ag.ag_kategorie if session.ag and hasattr(session.ag, 'ag_kategorie') else None,
                        is_offered=session.ag.offene_AG if session.ag and hasattr(session.ag, 'offene_AG') else False
                    )



def compute_metrics_for_student(student):
    update_session_buffer_for_student(student)

    attendances = Aufenthalt.objects.filter(schueler_id=student)
    days = defaultdict(list)
    for a in attendances:
        days[a.tag].append(a)
    total_ogs_time = 0.0
    for tag, tag_attendances in days.items():
        day_start = None
        day_end = None
        for a in tag_attendances:
            try:
                start_dt = combine_datetime(tag, a.zeitraum.startzeit)
                if a.zeitraum.endzeit is None:
                    continue
                end_dt = combine_datetime(tag, a.zeitraum.endzeit)
            except Exception:
                continue
            if day_start is None or start_dt < day_start:
                day_start = start_dt
            if day_end is None or end_dt > day_end:
                day_end = end_dt
        if day_start and day_end:
            total_ogs_time += (day_end - day_start).total_seconds() / 3600.0

    buffer_sessions = StudentSessionBuffer.objects.filter(student=student)
    category_data = defaultdict(lambda: {'total_duration': 0.0, 'frequency': 0, 'durations': [], 'offered_duration': 0.0})
    ag_frequency = defaultdict(int)
    all_session_durations = []

    for sess in buffer_sessions:
        duration = sess.duration
        all_session_durations.append(duration)
        cat = sess.ag_kategorie
        category_data[cat]['total_duration'] += duration
        category_data[cat]['frequency'] += 1
        category_data[cat]['durations'].append(duration)
        if sess.is_offered:
            category_data[cat]['offered_duration'] += duration
        if sess.ag:
            ag_frequency[sess.ag.id] += 1

    avg_continuous = sum(all_session_durations) / len(all_session_durations) if all_session_durations else 0.0
    num_days = len(days) if days else 1
    total_session_count = sum(cat['frequency'] for cat in category_data.values())
    avg_ag_per_day = total_session_count / num_days if num_days > 0 else 0.0
    total_ag_time = sum(cat['total_duration'] for cat in category_data.values())
    total_offered_time = sum(cat['offered_duration'] for cat in category_data.values())
    overall_offered_percentage = (total_offered_time / total_ag_time * 100.0) if total_ag_time > 0 else 0.0

    for cat, data in category_data.items():
        if data['frequency'] > 0:
            data['avg_duration'] = sum(data['durations']) / data['frequency']
        else:
            data['avg_duration'] = 0.0

    favourite_category = None
    max_cat_duration = 0.0
    for cat, data in category_data.items():
        if cat and data['total_duration'] > max_cat_duration:
            max_cat_duration = data['total_duration']
            favourite_category = cat

    if ag_frequency:
        frequent_ag_id = max(ag_frequency, key=ag_frequency.get)
        try:
            from main_app.models import AG
            frequent_ag = AG.objects.get(id=frequent_ag_id)
        except AG.DoesNotExist:
            frequent_ag = None
    else:
        frequent_ag = None

    if favourite_category:
        fav_data = category_data[favourite_category]
        favourite_time = fav_data['total_duration']
        favourite_frequency = fav_data['frequency']
        favourite_time_percentage = (favourite_time / total_ogs_time * 100.0) if total_ogs_time > 0 else 0.0
    else:
        favourite_time = 0.0
        favourite_frequency = 0
        favourite_time_percentage = 0.0

    overall_obj, created = StudentOverallAnalysis.objects.get_or_create(student=student)
    overall_obj.total_ogs_time = total_ogs_time
    overall_obj.avg_ag_per_day = avg_ag_per_day
    overall_obj.avg_continuous_ag_duration = avg_continuous
    overall_obj.avg_continuous_ag_kategorie_duration = (
        sum(data['avg_duration'] for data in category_data.values()) / len(category_data)
        if category_data else 0.0
    )
    overall_obj.offered_ag_time_percentage = overall_offered_percentage
    overall_obj.favourite_ag_kategorie = favourite_category
    overall_obj.frequent_ag = frequent_ag
    overall_obj.favourite_time = favourite_time
    overall_obj.favourite_frequency = favourite_frequency
    overall_obj.favourite_time_percentage = favourite_time_percentage
    overall_obj.save()

    for cat, data in category_data.items():
        if not cat:
            continue
        obj, created = StudentAGCategoryAnalysis.objects.get_or_create(student=student, ag_kategorie=cat)
        obj.time_spent = data['total_duration']
        obj.frequency = data['frequency']
        obj.average_session_duration = data['avg_duration']
        offered_pct = (data['offered_duration'] / data['total_duration'] * 100.0) if data['total_duration'] > 0 else 0.0
        obj.offered_ag_time_percentage = offered_pct
        obj.save()

    return overall_obj
