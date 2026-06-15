from django.apps import AppConfig


class AgentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # Register the app module path where models live, but keep the
    # historical app label 'agents' so existing migrations/DB stay valid.
    name = 'libraries'
    label = 'agents'
