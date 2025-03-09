from django.apps import AppConfig
from main_app.registry import register_user_function
from main_app.utils.permission_management import is_mobile, user_has_ogs, user_is_superuser

class AnalysisToolConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analysis_tool'

    def ready(self):
        register_user_function(define_user_function)


def define_user_function(request):
    return [{
        "label": "Test",
        "url": "/at/test/",
        "conditions": [
            lambda req: req.user.username != "root",
            lambda req: not is_mobile(req),    
        ],
        
        # "label": "Funktion",
        # "url": "/feature/",
        # "conditions": [
        #     lambda req: req.user.username != "root",
        #     lambda req: is_mobile(req),
        #     lambda req: req.user.has_perm('at.use_feature'),
        #     lambda req: user_has_ogs(req),
        #     lambda req: user_is_superuser(req)
        # ],
        
    }]