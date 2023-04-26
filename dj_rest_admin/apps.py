from django.apps import AppConfig


class DjRestAdminAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dj_rest_admin"

    def ready(self) -> None:
        super().ready()
        self.module.autodiscover()
