from django.apps import AppConfig
from main_app.utils.permission_management import is_mobile, user_has_ogs, user_is_superuser
from main_app.registry import register_view
from main_app import registry
import logging

logger = logging.getLogger(__name__)

class AnalysisToolConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analysis_tool'

    def ready(self):

        register_functions()
        #signals registrieren
        from analysis_tool.signals import create_ag_historie, create_student_buffer
        import analysis_tool.extensions

def register_functions():
    from analysis_tool import views
    register_view(
            view_func=views.raumplan_edit,
            url_name="heatmap_edit",
            label="Raumplan Bearbeiten",
            conditions=[],
            nav_conditions=[],
            show_in_nav=True
        )
    register_view(
            view_func=views.upload_raumplan,
            url_name="heatmap_upload",
            label="Raumplan Hochladen",
            conditions=[],
            nav_conditions=[],
            show_in_nav=True
        )
    register_view(
            view_func=views.raumplan_show,
            url_name="heatmap_show",
            label="Raumplan Anzeigen",
            conditions=[],
            nav_conditions=[],
            show_in_nav=True
        )

    register_view(
        view_func=views.student_analysis_view,
        url_name="student_analysis",
        label="Schüleranalyse",
        conditions=[],
        nav_conditions=[],
        show_in_nav=False
    )

    register_view(
        view_func=views.category_analysis_view,
        url_name="category_analysis_list",
        label="AG-Kategorien Analyse",
        conditions=[],  
        show_in_nav=False
    )
    register_view(
        view_func=views.category_comparison_view,
        url_name="category_comparison",
        label="AG-Kategorien Vergleichsanalyse",
        conditions=[],
        show_in_nav=True
    )

    register_view(
        view_func=views.ogs_optimization_view,
        url_name="ogs_optimization",
        label="OGS Optimierung",
        conditions=[],
        show_in_nav=True
    )

    register_view(
        view_func=views.category_selection_view,
        url_name="category_selection",
        label="AG Kategorie Analyse Auswahl",
        conditions=[],
        show_in_nav=True
    )

    register_view(views.save_polygon, "heatmap_save", "Save", conditions=[], show_in_nav=False)
    register_view(views.get_room_data, "heatmap_get_room_data", "Save", conditions=[], show_in_nav=False)
