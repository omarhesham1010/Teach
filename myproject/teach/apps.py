from django.apps import AppConfig


class TeachConfig(AppConfig):
    name = 'teach'


class TeachConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "teach"

    def ready(self):
        import teach.signals
