from django.apps import AppConfig


class AuthorizationAppConfig(AppConfig):
    name = 'topobank_orcid.authorization'
    label = 'authorization'

    def ready(self):
        pass
