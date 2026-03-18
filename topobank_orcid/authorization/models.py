"""
Concrete permission implementation for topobank-orcid.

This module provides PermissionSet backed by User + Organization permission rows.
"""
import logging

from django.db import models
from django.db.models import Q, QuerySet
from notifications.signals import notify
from rest_framework.exceptions import NotFound, PermissionDenied

from topobank.authorization.models import (
    ACCESS_LEVELS,
    PERMISSION_CHOICES,
    AbstractPermissionSet,
    ViewEditFull,
    ViewEditFullNone,
    levels_with_access,
)

from ..organizations.models import Organization
from ..users.anonymous import get_anonymous_user

_log = logging.getLogger(__name__)


def _filter_for_user(
    queryset: QuerySet,
    user,
    permission: ViewEditFull,
    prefix: str = ""
) -> QuerySet:
    """
    Shared implementation for filtering querysets by user permission.

    Args:
        queryset: The queryset to filter
        user: The user to check permissions for
        permission: The permission level to check
        prefix: Field prefix for permission lookups (e.g., "permissions__" or "")

    Note: This implementation uses UNION queries to optimize performance.
    """
    # Cache user groups to prevent query re-evaluation
    if not hasattr(user, '_cached_group_ids'):
        user._cached_group_ids = list(user.groups.values_list('id', flat=True))
    user_group_ids = user._cached_group_ids

    # Build field names with prefix
    user_perm_user = f"{prefix}user_permissions__user"
    user_perm_allow = f"{prefix}user_permissions__allow__in"
    org_perm_group = f"{prefix}organization_permissions__organization__group_id__in"
    org_perm_allow = f"{prefix}organization_permissions__allow__in"

    if permission == "view":
        qs_anonymous = queryset.filter(**{user_perm_user: get_anonymous_user()})
        qs_user = queryset.filter(**{user_perm_user: user})

        if user_group_ids:
            qs_org = queryset.filter(**{org_perm_group: user_group_ids})
            union_qs = qs_anonymous.union(qs_user, qs_org)
        else:
            union_qs = qs_anonymous.union(qs_user)

        accessible_ids = list(union_qs.values_list('id', flat=True))
        return queryset.filter(id__in=accessible_ids)
    else:
        allowed_levels = levels_with_access(permission)

        qs_user = queryset.filter(**{user_perm_user: user, user_perm_allow: allowed_levels})

        if user_group_ids:
            qs_org = queryset.filter(
                **{org_perm_group: user_group_ids, org_perm_allow: allowed_levels}
            )
            union_qs = qs_user.union(qs_org)
        else:
            return qs_user

        accessible_ids = list(union_qs.values_list('id', flat=True))
        return queryset.filter(id__in=accessible_ids)


class PermissionSetManager(models.Manager):
    def create(self, user=None, allow: ViewEditFullNone = None, **kwargs):
        if user is not None or allow is not None:
            if user is None or allow is None:
                raise RuntimeError(
                    "You need to provide both user and permission when creating a "
                    "PermissionSet."
                )
            permission_set = super().create(**kwargs)
            permission_set.grant_for_user(user, allow)
            return permission_set
        else:
            return super().create(**kwargs)

    def for_user(self, user, permission: ViewEditFull = "view") -> QuerySet:
        """Return all PermissionSets where user has at least the given permission level"""
        return _filter_for_user(self.get_queryset(), user, permission, prefix="")


class PermissionSet(AbstractPermissionSet):
    """Concrete permission set backed by User + Organization permission rows."""

    objects = PermissionSetManager()

    @classmethod
    def filter_queryset(cls, queryset, user, permission):
        """Filter domain-object queryset to items accessible to user."""
        return _filter_for_user(queryset, user, permission, prefix="permissions__")

    def get_for_user(self, user):
        """Return permissions of a specific user"""
        anonymous_user = get_anonymous_user()

        if 'user_permissions' in getattr(self, '_prefetched_objects_cache', {}):
            user_permissions = [
                p for p in self.user_permissions.all()
                if p.user == user or p.user == anonymous_user
            ]
        else:
            user_permissions = list(self.user_permissions.filter(
                Q(user=user) | Q(user=anonymous_user)
            ))

        nb_user_permissions = len(user_permissions)

        if not hasattr(user, '_cached_group_ids'):
            user._cached_group_ids = list(user.groups.values_list('id', flat=True))
        user_group_ids = user._cached_group_ids

        if 'organization_permissions' in getattr(self, '_prefetched_objects_cache', {}):
            organization_permissions = [
                p for p in self.organization_permissions.all()
                if p.organization.group_id in user_group_ids
            ]
        else:
            organization_permissions = list(self.organization_permissions.filter(
                organization__group_id__in=user_group_ids
            ))

        nb_organization_permissions = len(organization_permissions)

        if nb_user_permissions > 1:
            raise RuntimeError(
                f"More than one user permission found for user {user}. "
                "This should not happen."
            )

        max_access_level = 0
        if nb_user_permissions > 0:
            max_access_level = max(
                max_access_level,
                max(ACCESS_LEVELS[perm.allow] for perm in user_permissions),
            )
        if nb_organization_permissions > 0:
            max_access_level = max(
                max_access_level,
                max(ACCESS_LEVELS[perm.allow] for perm in organization_permissions),
            )
        if max_access_level == 0:
            return None
        else:
            return PERMISSION_CHOICES[max_access_level - 1][0]

    def grant_for_user(self, user, allow: ViewEditFull):
        """Grant permission to user"""
        UserPermission.objects.update_or_create(
            parent=self, user=user,
            defaults={"allow": allow},
        )

    def revoke_from_user(self, user):
        """Revoke all permissions from user"""
        self.user_permissions.filter(user=user).delete()

    def grant_for_organization(self, organization: Organization, allow: ViewEditFull):
        """Grant permission to an organization"""
        OrganizationPermission.objects.update_or_create(
            parent=self, organization=organization,
            defaults={"allow": allow},
        )

    def revoke_from_organization(self, organization: Organization):
        """Revoke all permissions from an organization"""
        self.organization_permissions.filter(organization=organization).delete()

    def grant(self, principal, allow: ViewEditFull):
        """Grant permission"""
        if isinstance(principal, Organization):
            return self.grant_for_organization(principal, allow)
        else:
            return self.grant_for_user(principal, allow)

    def revoke(self, principal):
        """Revoke permission"""
        if isinstance(principal, Organization):
            return self.revoke_from_organization(principal)
        else:
            return self.revoke_from_user(principal)

    def user_has_permission(self, user, access_level: ViewEditFull) -> bool:
        """Check if user has permission for access level given by `allow`"""
        perm = self.get_for_user(user)
        if perm:
            return ACCESS_LEVELS[perm] >= ACCESS_LEVELS[access_level]
        else:
            return False

    def authorize_user(self, user, access_level: ViewEditFull):
        """Authorize user; raise PermissionDenied or NotFound if insufficient."""
        perm = self.get_for_user(user)
        if perm is None:
            raise NotFound()
        elif ACCESS_LEVELS[perm] < ACCESS_LEVELS[access_level]:
            raise PermissionDenied(
                f"User '{user}' has permission '{perm}', cannot elevate to "
                f"permission '{access_level}'."
            )

    def notify_users(self, sender, verb, description):
        """Notify all users with permissions except sender"""
        anonymous_user = get_anonymous_user()
        for permission in self.user_permissions.exclude(
            Q(user=sender) | Q(user=anonymous_user)
        ):
            notify.send(
                sender=sender,
                recipient=permission.user,
                verb=verb,
                description=description,
            )

    def get_users(self):
        """Return all users with their permissions"""
        return [(perm.user, perm.allow) for perm in self.user_permissions.all()]


class UserPermission(models.Model):
    """Single permission for a specific user"""

    class Meta:
        unique_together = ("parent", "user")
        indexes = [
            models.Index(fields=['user', 'parent'], name='userperm_user_parent_idx'),
            models.Index(fields=['parent'], name='userperm_parent_idx'),
        ]

    parent = models.ForeignKey(
        PermissionSet, on_delete=models.CASCADE, related_name="user_permissions"
    )

    user = models.ForeignKey(
        'users.User', on_delete=models.CASCADE
    )

    allow = models.CharField(max_length=4, choices=PERMISSION_CHOICES)


class OrganizationPermission(models.Model):
    """Permission applying to all members of an organization"""

    class Meta:
        unique_together = ("parent", "organization")
        indexes = [
            models.Index(fields=['organization', 'parent'], name='orgperm_org_parent_idx'),
            models.Index(fields=['parent'], name='orgperm_parent_idx'),
        ]

    parent = models.ForeignKey(
        PermissionSet, on_delete=models.CASCADE, related_name="organization_permissions"
    )

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    allow = models.CharField(max_length=4, choices=PERMISSION_CHOICES)
