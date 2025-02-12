from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Setting
import os

@receiver(post_save, sender=Setting)
def handle_setting_change(sender, instance, **kwargs):
    if instance.requires_restart:
        print("Einstellung erfordert einen Neustart.")
        os.system('sudo systemctl restart myservice')  # Beispiel für Server-Neustart

    if instance.requires_db_reset:
        print("Einstellung erfordert einen Datenbank-Reset.")
        os.system('python manage.py migrate --noinput')