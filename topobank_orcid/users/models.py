from urllib.parse import urlparse

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.utils import ProgrammingError
from django.urls import resolve
from django.utils.translation import gettext_lazy as _

from .anonymous import get_anonymous_user


class ORCIDException(Exception):
    pass


class User(AbstractUser):
    # First name and last name (of the default `AbstractUser` model) do not cover name
    # patterns around the globe.
    name = models.CharField(_("Name of User"), max_length=255)

    # Load anonymous user once and cache to avoid further database hits
    anonymous_user = None

    def __str__(self):
        orcid_id = self.orcid_id
        if orcid_id:
            return "{} ({})".format(self.name, orcid_id)
        else:
            return self.name

    def save(self, *args, **kwargs):
        # ensure the full name field is set
        if not self.name:
            self.name = f"{self.first_name} {self.last_name}"
        super().save(*args, **kwargs)

    def _get_anonymous_user(self):
        if self.anonymous_user is None:
            self.anonymous_user = get_anonymous_user()
        return self.anonymous_user

    def _orcid_info(self):  # TODO use local cache
        try:
            from allauth.socialaccount.models import SocialAccount
        except:  # noqa: E722
            raise ORCIDException("ORCID authentication not configured.")

        try:
            social_account = SocialAccount.objects.get(user_id=self.id)
        except SocialAccount.DoesNotExist as exc:
            raise ORCIDException("No ORCID account existing for this user.") from exc
        except SocialAccount.MultipleObjectsReturned as exc:
            raise ORCIDException(
                "Cannot retrieve ORCID: Multiple social accounts returned."
            ) from exc

        try:
            orcid_info = social_account.extra_data["orcid-identifier"]
        except Exception as exc:
            raise ORCIDException(
                "Cannot retrieve ORCID info from local database."
            ) from exc

        return orcid_info

    @property
    def orcid_id(self) -> str:
        """
        Return ORCID iD, a unique 16-digit identifier for researchers.
        """
        try:
            return self._orcid_info()["path"]
        except ORCIDException:
            return None

    def orcid_uri(self):
        """
        Return the URI to the user's ORCID account, if available.
        """
        try:
            return self._orcid_info()["uri"]
        except ORCIDException:  # noqa: E722
            return None

    @property
    def is_anonymous(self):
        """
        Return whether user is anonymous.
        """
        try:
            return self.id == self._get_anonymous_user().id
        except (ProgrammingError, self.DoesNotExist):
            return super().is_anonymous

    @property
    def is_authenticated(self):
        """Return whether user is authenticated (not anonymous)."""
        try:
            return self.id != self._get_anonymous_user().id
        except (ProgrammingError, self.DoesNotExist):
            return super().is_anonymous

    class Meta:
        permissions = (
            ("can_skip_terms", "Can skip all checkings for terms and conditions."),
        )

    @classmethod
    def resolve(cls, url):
        """Resolve a user from a URL or integer ID."""
        try:
            pk = int(url)
            return cls.objects.get(pk=pk)
        except ValueError:
            match = resolve(urlparse(url).path)
            if match.view_name != "users:user-v1-detail":
                raise ValueError("URL does not resolve to a User instance")
            return cls.objects.get(**match.kwargs)


def resolve_user(url):
    """Resolve user from URL or ID. Prefer User.resolve(url)."""
    return User.resolve(url)
