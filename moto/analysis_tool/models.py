from django.db import models
from main_app.models import AGKategorie, Raum, Schueler, AG
from datetime import timedelta
from django.db.models import F, ExpressionWrapper, Sum, FloatField

class AGHistorie(models.Model):
    ag_name = models.CharField(max_length=50)
    max_anzahl = models.PositiveIntegerField()
    total_available_time = models.FloatField(help_text="Verfügbare Zeit in Stunden (Kapazität * AG-Dauer)")
    actual_usage_time = models.FloatField(help_text="Summe der tatsächlichen Anwesenheitszeit aller Schüler in Stunden")
    utilization_percentage = models.FloatField(help_text="Auslastung in Prozent")
    peak_participants = models.PositiveIntegerField(default=0, help_text="Maximal gleichzeitig teilnehmende Schüler")
    fully_utilized_percentage = models.FloatField(help_text="Prozentualer Anteil der AG-Zeit, in der sie voll ausgelastet war")
    zeitraum_start = models.DateTimeField()
    zeitraum_end = models.DateTimeField()
    ag_kategorie = models.ForeignKey(AGKategorie, on_delete=models.SET_NULL, null=True)
    raum = models.ForeignKey(Raum, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.ag_name} in Raum {self.raum} ({self.zeitraum_start.strftime('%Y-%m-%d %H:%M')} - {self.zeitraum_end.strftime('%Y-%m-%d %H:%M')})"

class ExtendedAGKategorie(AGKategorie):
    """
    Proxy-Modell, das zusätzliche Analyse-Methoden zur AGKategorie bietet.
    """
    class Meta:
        proxy = True

    def get_utilization_stats(self):

        qs = AGHistorie.objects.filter(ag_kategorie=self)
        
        # Aggregiere die Gesamtwerte aus den Feldern total_available_time und actual_usage_time
        agg_data = qs.aggregate(
            total_available=Sum('total_available_time'),
            actual_usage=Sum('actual_usage_time')
        )
        total_available = agg_data.get('total_available') or 0.0
        actual_usage = agg_data.get('actual_usage') or 0.0
        
        # Für jeden Eintrag: Berechne die voll ausgelastete Zeit = total_available_time * (fully_utilized_percentage / 100)
        qs = qs.annotate(
            fully_utilized_time=ExpressionWrapper(
                F('total_available_time') * F('fully_utilized_percentage') / 100.0,
                output_field=FloatField()
            )
        )
        fully_data = qs.aggregate(total_fully_utilized=Sum('fully_utilized_time'))
        total_fully_utilized_time = fully_data.get('total_fully_utilized') or 0.0
        
        # Berechne die prozentualen Anteile
        utilization_percentage = (actual_usage / total_available * 100) if total_available > 0 else 0
        fully_utilized_overall_percentage = (total_fully_utilized_time / total_available * 100) if total_available > 0 else 0
        
        # Zähle, in wie vielen AGHistorie-Einträgen die AG voll ausgelastet war (fully_utilized_percentage == 100)
        fully_utilized_count = qs.filter(fully_utilized_percentage=100).count()
        
        return {
            'total_available_time': total_available,
            'actual_usage_time': actual_usage,
            'utilization_percentage': utilization_percentage,
            'total_fully_utilized_time': total_fully_utilized_time,
            'fully_utilized_overall_percentage': fully_utilized_overall_percentage,
            'fully_utilized_count': fully_utilized_count,
        }

class StudentSessionBuffer(models.Model):

    student = models.ForeignKey(Schueler, on_delete=models.CASCADE)
    session_date = models.DateField()
    session_start = models.DateTimeField()
    session_end = models.DateTimeField()
    duration = models.FloatField(help_text="Dauer in Stunden")
    ag = models.ForeignKey(AG, on_delete=models.SET_NULL, null=True, blank=True)
    ag_kategorie = models.ForeignKey(AGKategorie, on_delete=models.SET_NULL, null=True, blank=True)
    is_offered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session for {self.student.name_eb} on {self.session_date}: {self.duration:.2f}h"


class StudentAGCategoryAnalysis(models.Model):

    student = models.ForeignKey(Schueler, on_delete=models.CASCADE)
    ag_kategorie = models.ForeignKey(AGKategorie, on_delete=models.SET_NULL, null=True)
    time_spent = models.FloatField(
        default=0.0,
        help_text="Gesamte Zeit in Stunden, die der Schüler in dieser AGKategorie verbracht hat"
    )
    frequency = models.PositiveIntegerField(
        default=0,
        help_text="Anzahl der Besuche (Sitzungen) in dieser AGKategorie"
    )
    average_session_duration = models.FloatField(
        default=0.0,
        help_text="Durchschnittliche Dauer eines zusammenhängenden Besuchs in Stunden"
    )
    offered_ag_time_percentage = models.FloatField(
        default=0.0,
        help_text="Prozentsatz der in AGs dieser Kategorie verbrachten Zeit, bei denen ein Angebot vorlag"
    )
    # relative Zeit zur gesamt verbrachten zeit in der Schule

    class Meta:
        unique_together = ('student', 'ag_kategorie')

    def __str__(self):
        return f"{self.student.name_eb} – {self.ag_kategorie.name if self.ag_kategorie else 'Ohne Kategorie'}"


class StudentOverallAnalysis(models.Model):
    student = models.OneToOneField(Schueler, on_delete=models.CASCADE, primary_key=True)
    total_ogs_time = models.FloatField(
        default=0.0,
        help_text="Gesamte OGS-Zeit in Stunden (von der ersten Anmeldung bis zur letzten Abmeldung pro Tag aufsummiert)"
    )
    avg_ag_per_day = models.FloatField(
        default=0.0,
        help_text="Durchschnittliche Anzahl der AG-Besuche pro Tag"
    )
    avg_continuous_ag_duration = models.FloatField(
        default=0.0,
        help_text="Durchschnittliche Dauer zusammenhängender AG-Besuche in Stunden (über alle AGs)"
    )
    avg_continuous_ag_kategorie_duration = models.FloatField(
        default=0.0,
        help_text="Durchschnittliche Dauer eines kontinuierlichen Besuchs pro AGKategorie in Stunden"
    )
    offered_ag_time_percentage = models.FloatField(
        default=0.0,
        help_text="Prozentsatz der insgesamt in AGs verbrachten Zeit, die in angebotenen Sessions lag"
    )
    favourite_ag_kategorie = models.ForeignKey(
        AGKategorie,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Die AGKategorie, in der der Schüler insgesamt die meiste Zeit verbracht hat"
    )
    frequent_ag = models.ForeignKey(
        AG,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Die AG, die der Schüler am häufigsten besucht hat"
    )
    favourite_time = models.FloatField(
        default=0.0,
        help_text="Zeit in Stunden, die in der Lieblings-AGKategorie verbracht wurde"
    )
    favourite_frequency = models.PositiveIntegerField(
        default=0,
        help_text="Anzahl der Besuche in der Lieblings-AGKategorie"
    )
    favourite_time_percentage = models.FloatField(
        default=0.0,
        help_text="Prozentsatz der Gesamt-OGS-Zeit, die in der Lieblings-AGKategorie verbracht wurde"
    )

    def __str__(self):
        return f"Analyse für {self.student.name_eb}"
    

class RaumPlan(models.Model):
    """
    Modell zum Speichern eines Raumplans als Bild.
    """
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='raumplaene/')
    width = models.PositiveIntegerField(help_text="Breite des Bildes in Pixel")
    height = models.PositiveIntegerField(help_text="Höhe des Bildes in Pixel")

    def __str__(self):
        return self.title

class RaumPolygon(models.Model):
    """
    Modell zur Speicherung der Polygon-Koordinaten, verknüpft mit einem Raum und Raumplan.
    """
    raum = models.OneToOneField(Raum, on_delete=models.CASCADE)
    raumplan = models.ForeignKey(RaumPlan, on_delete=models.CASCADE)
    # Speichert eine Liste von Koordinaten z. B. [{'x': 10, 'y': 20}, {'x': 150, 'y': 20}, ...]
    polygon = models.JSONField(help_text="Liste von Koordinaten z. B. [{'x': 10, 'y': 20}, ...]")

    def __str__(self):
        return f"Polygon für Raum {self.raum.raum_nr} im Plan {self.raumplan.title}"
