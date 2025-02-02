from django.apps import AppConfig


class PejappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pejapp"

    def ready(self):
        import pejapp.signals 
