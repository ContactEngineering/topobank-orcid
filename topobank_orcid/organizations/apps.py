from django.apps import AppConfig


class OrganizationsAppConfig(AppConfig):
    """This app handles organizations."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'topobank_orcid.organizations'
    label = 'organizations'

    def ready(self):
        pass
