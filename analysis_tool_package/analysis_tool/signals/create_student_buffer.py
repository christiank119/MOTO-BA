# analyse_tool/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from main_app.models import Aufenthalt
from analysis_tool.utils.compute_student_metrics import compute_metrics_for_student

@receiver(post_save, sender=Aufenthalt)
def update_analysis_on_attendance_save(sender, instance, created, **kwargs):

    if instance.zeitraum and instance.zeitraum.endzeit is not None:   # Nur beim Verlassen des Raumes
        print("Buffer erstellt")
        compute_metrics_for_student(instance.schueler_id)
