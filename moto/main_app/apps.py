from django.apps import AppConfig
from datetime import datetime
from main_app.utils.permission_management import is_mobile, user_has_ogs, user_is_superuser
import importlib
import logging
from main_app.registry import register_view
from main_app import registry
# from django.contrib.auth.models import Group

logger = logging.getLogger(__name__)

class LogsystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main_app'
    def ready(self):

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
            if not models.AGKategorie.objects.filter(name='Sport').exists():
                models.AGKategorie.objects.create(name='Sport')
            if not models.AGKategorie.objects.filter(name='Lernen').exists():
                models.AGKategorie.objects.create(name='Lernen')
            if not models.AGKategorie.objects.filter(name='Kreativ').exists():
                models.AGKategorie.objects.create(name='Kreativ')
            if not models.AGKategorie.objects.filter(name='Ernährung').exists():
                models.AGKategorie.objects.create(name='Ernährung')
            if not models.AGKategorie.objects.filter(name='Natur').exists():
                models.AGKategorie.objects.create(name='Natur')
            if not models.AGKategorie.objects.filter(name='Gruppenraum').exists():
                models.AGKategorie.objects.create(name='Gruppenraum')
            if not models.AGKategorie.objects.filter(name='Ruhe').exists():
                models.AGKategorie.objects.create(name='Ruhe')
            if not models.AGKategorie.objects.filter(name='Sonstiges').exists():
                models.AGKategorie.objects.create(name='Sonstiges')
        except:
            pass
        try:
            models = importlib.import_module('main_app.models')
            r_bs = models.Raum_Belegung.objects.all()
            for raum_belegung in r_bs:
                raum = raum_belegung.raum
                if(models.Aufenthalt.objects.filter(raum_id=raum, zeitraum__endzeit=None).exists):
                    aufenthalte = models.Aufenthalt.objects.filter(raum_id=raum, zeitraum__endzeit=None)
                    for aufenthalt in aufenthalte:
                        zeitraum1 = aufenthalt.zeitraum
                        zeitraum1.endzeit = datetime.now().time()
                        zeitraum1.save()
                zeitraum = raum_belegung.zeitraum
                zeitraum.endzeit = datetime.now().time()
                zeitraum.save()
                raum_historie = models.Raum_Historie.objects.create(zeitraum=zeitraum,raum=raum,tag=datetime.now().date(),ag_name=raum_belegung.ag.name,ag_kategorie=raum_belegung.ag.ag_kategorie,leiter=raum_belegung.ag.leiter, max_anzahl=raum_belegung.ag.max_anzahl)
                raum_belegung.save()
                raum_belegung.delete()
            models.AG.objects.all().delete()
            aufenthalte = models.Aufenthalt.objects.all()
            for aufenthalt in aufenthalte:
                if aufenthalt.zeitraum.endzeit == None:
                    aufenthalt.delete()
            for schueler in models.Schueler.objects.all():
                schueler.angemeldet = False
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
            groups = models.Gruppe.objects.all()
            for group in groups:
                group.vertreter = None
                group.save()
        except:
            pass


        # registrierung funktionen mit berechtigungen

        main_app_functions()


def main_app_functions():
    from main_app import views

    condition_no_root = registry.condition_no_root
    condition_only_root = registry.condition_only_root
    condition_only_su = registry.condition_only_su
    condition_root_and_su = registry.condition_root_and_su
    condition_ogs_group_needed = registry.condition_ogs_group_needed


    try:
        register_view(
            view_func=views.dashboard_view,
            url_name="dashboard",
            label="Dashboard",
            conditions=[lambda req: req.user.username != "root"],
            show_in_nav=True
        )
        register_view(
            view_func=views.ogs_group_view,
            url_name="ogs_group",
            label="OGS-Gruppe",
            conditions=condition_ogs_group_needed,
            show_in_nav=True
        )
        register_view(
            view_func=views.search_pupil_view,
            url_name="search_pupil",
            label="Suche Kind",
            conditions=[lambda req: req.user.username != "root"],
            show_in_nav=True
        )

        # Für Superuser (nicht root):
        # Statt separater Registrierungen für mobile und Desktop wird hier eine einzige Registrierung verwendet.
        register_view(
            view_func=views.superuser,
            url_name="superuser",
            label="Passwörter Zurücksetzen",
            conditions=[lambda req: req.user.is_superuser or req.user.username == "root"],
            show_in_nav=True
        )
        register_view(
            view_func=views.preferences_view,
            url_name="preferences",
            label="Persönliche Einstellungen",
            conditions=[lambda req: req.user.username != "root"],
            show_in_nav=True
        )
        register_view(
            view_func=views.select_room,
            url_name="select_room",
            label="Raumübersicht",
            conditions=[lambda req: req.user.username != "root"],
            show_in_nav=True
        )
        register_view(
            view_func=views.representation_view,
            url_name="representation",
            label="Vertretungen",
            conditions=[lambda req: req.user.is_superuser and req.user.username != "root"],
            show_in_nav=True
        )
        register_view(
            view_func=views.csv_import_view,
            url_name="csv_import",
            label="CSV-Import",
            conditions=[lambda req: req.user.is_superuser or req.user.username == "root"],
            show_in_nav=True
        )
        register_view(
            view_func=views.choose_data,
            url_name="choose_data",
            label="Datenbank Bearbeiten",
            conditions=[lambda req: req.user.is_superuser or req.user.username == "root"],
            show_in_nav=True
        )

        # Für den Root-Benutzer:
        # Statt separater Registrierungen (z.B. password_reset_root) werden diese in dieselbe URL integriert.
        register_view(
            view_func=views.set_new_pw,
            url_name="set_new_pw",
            label="Passwort Ändern",
            conditions=[],
            nav_conditions=condition_only_root,
            show_in_nav=True
        )

        register_view(views.master_web, "master_web", "Master Web", conditions=[], show_in_nav=False)
        register_view(views.login, "login", "Login", conditions=[], show_in_nav=False)
        register_view(views.logout, "logout", "Logout", conditions=[], show_in_nav=False)
        register_view(views.reset_pw_confirmation, "reset_pw_confirmation", "Reset PW Confirmation", conditions=[], show_in_nav=False)
        register_view(views.pupil, "pupil", "Pupil", conditions=condition_no_root, show_in_nav=False)
        register_view(views.room_selection, "room_selection", "Room Selection", conditions=condition_no_root, show_in_nav=False)
        register_view(views.room_information, "room_information", "Room Information", conditions=condition_no_root, show_in_nav=False)
        register_view(views.room_usage_history, "room_usage_history", "Room Usage History", conditions=condition_no_root, show_in_nav=False)
        register_view(views.room_history, "room_history", "Room History", conditions=condition_no_root, show_in_nav=False)
        register_view(views.feedback_history, "feedback_history", "Feedback History", conditions=condition_ogs_group_needed, show_in_nav=False)
        register_view(views.food_history, "food_history", "Food History", conditions=condition_ogs_group_needed, show_in_nav=False)
        register_view(views.select_student_change_view, "choose_data_student", "Choose Data Student", conditions=condition_root_and_su, show_in_nav=False)
        register_view(views.select_room_change, "choose_data_room", "Choose Data Room", conditions=condition_root_and_su, show_in_nav=False)
        register_view(views.select_pa_change, "choose_data_pa", "Choose Data PA", conditions=condition_root_and_su, show_in_nav=False)
        register_view(views.select_group_change, "choose_data_group", "Choose Data Group", conditions=condition_root_and_su, show_in_nav=False)
        register_view(views.change_student, "change_student_data", "Change Student Data", conditions=condition_root_and_su, show_in_nav=False)
        register_view(views.change_room, "change_room_data", "Change Room Data", conditions=condition_root_and_su, show_in_nav=False)
        register_view(views.change_group, "change_group_data", "Change Group Data", conditions=condition_root_and_su, show_in_nav=False)
        register_view(views.change_student, "change_pa_data", "Change PA Data", conditions=condition_root_and_su, show_in_nav=False)

        
    except Exception as e:
        logger.error("Error registering views: %s", e)