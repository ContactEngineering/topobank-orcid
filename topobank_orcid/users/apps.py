from django.apps import AppConfig


class UsersAppConfig(AppConfig):
    name = "topobank_orcid.users"
    label = "users"

    def ready(self):
        pass
