from django.apps import AppConfig
from datetime import datetime
import importlib
# from django.contrib.auth.models import Group


class LogsystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main_app'
    def ready(self):

        # Signale beim Start der App importieren
        import main_app.signals 

        from .models import Setting
        
        default_settings = [
            {'key': 'combine_groups_all_ps', 'value': 'False', 'category': 'always'},
            {'key': 'allow_ps_assigend_multiple_groups', 'value': 'True', 'category': 'always'},
            {'key': 'allow_ps_assigend_to_groups_and_reprensentation', 'value': 'False', 'category': 'always'},
            # Examples:
            #{'key': 'site_name', 'value': 'My Website', 'category': 'always'},
            #{'key': 'max_users', 'value': '1000', 'category': 'db_reset'},
            #{'key': 'maintenance_mode', 'value': 'False', 'category': 'restart'},
        ]

        for setting in default_settings:
            Setting.objects.get_or_create(key=setting['key'], defaults=setting)

        # Erstellung der Rechte Gruppen
        try:
            models = importlib.import_module('django.contrib.auth.models')
            if not models.Group.objects.filter(name='Admin').exists():
                models.Group.objects.create(name='Admin')
            if not models.Group.objects.filter(name='Gruppenleitung').exists():
                models.Group.objects.create(name='Gruppenleitung')
            if not models.Group.objects.filter(name='Raumbetreuer').exists():
                models.Group.objects.create(name='Raumbetreuer')
            if not models.Group.objects.filter(name='Ohne Rolle').exists():
                models.Group.objects.create(name='Ohne Rolle')
        except:
            pass

        # Erstelle verschiedene AGKategorien 
        try:
            models = importlib.import_module('main_app.models')
            if not models.Ag_category.objects.filter(name='Sport').exists():
                models.Ag_category.objects.create(name='Sport')
            if not models.Ag_category.objects.filter(name='Lernen').exists():
                models.Ag_category.objects.create(name='Lernen')
            if not models.Ag_category.objects.filter(name='Kreativ').exists():
                models.Ag_category.objects.create(name='Kreativ')
            if not models.Ag_category.objects.filter(name='Ernährung').exists():
                models.Ag_category.objects.create(name='Ernährung')
            if not models.Ag_category.objects.filter(name='Natur').exists():
                models.Ag_category.objects.create(name='Natur')
            if not models.Ag_category.objects.filter(name='Gruppenraum').exists():
                models.Ag_category.objects.create(name='Gruppenraum')
            if not models.Ag_category.objects.filter(name='Ruhe').exists():
                models.Ag_category.objects.create(name='Ruhe')
            if not models.Ag_category.objects.filter(name='Sonstiges').exists():
                models.Ag_category.objects.create(name='Sonstiges')
        except:
            pass
        try:
            models = importlib.import_module('main_app.models')
            r_bs = models.Room_occupancy.objects.all()
            for raum_belegung in r_bs:
                raum = raum_belegung.room
                if(models.Visit.objects.filter(room=raum, timespan__endtime=None).exists):
                    aufenthalte = models.Visit.objects.filter(room=raum, timespan__endtime=None)
                    for aufenthalt in aufenthalte:
                        zeitraum1 = aufenthalt.timespan
                        zeitraum1.endtime = datetime.now().time()
                        zeitraum1.save()
                zeitraum = raum_belegung.timespan
                zeitraum.endtime = datetime.now().time()
                zeitraum.save()
                raum_historie = models.Room_history.objects.create(timespan=zeitraum,room=raum,day=datetime.now().date(),ag_name=raum_belegung.ag.name,ag_category=raum_belegung.ag.ag_category,supervisor=raum_belegung.ag.supervisor, max_participant=raum_belegung.ag.max_participant)
                raum_belegung.delete()
            models.AG.objects.all().delete()
            aufenthalte = models.Visit.objects.all()
            for aufenthalt in aufenthalte:
                if aufenthalt.timespan.endtime == None:
                    aufenthalt.delete()
            for schueler in models.Student.objects.all():
                schueler.in_house = False
                schueler.save()
        except:
            pass

        try:
            models = importlib.import_module('django.contrib.auth.models')
            if not models.User.objects.filter(username="root").exists():
                newuser = models.User.objects.create_user(username="root", password="root")
                newuser.is_superuser = True
                newuser.save()
        except:
            pass

        try:
            models = importlib.import_module('main_app.models')
            groups = models.Group.objects.all()
            for group in groups:
                group.represent = None
                group.save()
        except:
            pass