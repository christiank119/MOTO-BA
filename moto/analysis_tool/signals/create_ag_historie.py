from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime, date, timedelta
from main_app.models import Raum_Belegung, Aufenthalt
from analysis_tool.models import AGHistorie

@receiver(pre_delete, sender=Raum_Belegung)
def archive_ag_utilization(sender, instance, **kwargs):
    if instance.zeitraum.endzeit is not None:
        print("AG Historie wird erstellt")
        ag = instance.ag
        
        # Kombiniere die Zeiten mit einem Datum, um datetime-Objekte zu erhalten.
        start_dt = datetime.combine(date.today(), instance.zeitraum.startzeit)
        end_dt = datetime.combine(date.today(), instance.zeitraum.endzeit)
        total_duration_hours = (end_dt - start_dt).total_seconds() / 3600.0
        
        total_available_time = ag.max_anzahl * total_duration_hours

        actual_usage_time = 0.0
        attendances = Aufenthalt.objects.filter(
            raum_id=instance.raum,
            zeitraum__startzeit__lt=instance.zeitraum.endzeit,
            zeitraum__endzeit__gt=instance.zeitraum.startzeit,
        )
        
        events = []
        for att in attendances:
            att_start = att.zeitraum.startzeit
            att_end = att.zeitraum.endzeit if att.zeitraum.endzeit is not None else instance.zeitraum.endzeit
            events.append((att_start, 1))
            events.append((att_end, -1))
            
            att_start_dt = datetime.combine(date.today(), att_start)
            att_end_dt = datetime.combine(date.today(), att_end)
            att_duration = (att_end_dt - att_start_dt).total_seconds() / 3600.0
            actual_usage_time += att_duration
        
        events.sort(key=lambda x: datetime.combine(date.today(), x[0]))
        
        current_active = 0
        peak_participants = 0
        for event in events:
            current_active += event[1]
            if current_active > peak_participants:
                peak_participants = current_active
        
        last_time = instance.zeitraum.startzeit
        full_duration = 0.0  # in Stunden
        current_active = 0  # Zähler zurücksetzen
        for event_time, delta in events:
            dt_last = datetime.combine(date.today(), last_time)
            dt_event = datetime.combine(date.today(), event_time)
            if dt_event < dt_last:
                dt_event += timedelta(days=1)
            interval = (dt_event - dt_last).total_seconds() / 3600.0
            if current_active == ag.max_anzahl:
                full_duration += interval
            current_active += delta
            last_time = event_time

        fully_utilized_percentage = (full_duration / total_duration_hours * 100) if total_duration_hours > 0 else 0
        utilization_percentage = (actual_usage_time / total_available_time * 100) if total_available_time > 0 else 0

        AGHistorie.objects.create(
            ag_name=ag.name,
            max_anzahl=ag.max_anzahl,
            total_available_time=total_available_time,
            actual_usage_time=actual_usage_time,
            utilization_percentage=utilization_percentage,
            peak_participants=peak_participants,
            fully_utilized_percentage=fully_utilized_percentage,
            zeitraum_start=start_dt,   # jetzt ein datetime
            zeitraum_end=end_dt,       # jetzt ein datetime
            ag_kategorie=ag.ag_kategorie,
            raum=instance.raum
        )


def get_duration(start_time, end_time):
    """
    Konvertiert zwei datetime.time-Objekte in datetime-Objekte anhand eines gemeinsamen Datums
    und berechnet die Dauer. Falls end_time vor start_time liegt, wird angenommen, dass der Zeitraum
    über Mitternacht geht.
    """
    today = date.today()  # oder ein anderes Referenzdatum, falls vorhanden
    start_dt = datetime.combine(today, start_time)
    end_dt = datetime.combine(today, end_time)
    if end_dt < start_dt:
        end_dt += timedelta(days=1)
    return end_dt - start_dt
