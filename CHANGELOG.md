# Changelog for plugin *topobank-orcid*

## Deprecated

This package has moved into
[ce-ui](https://github.com/ContactEngineering/ce-ui), where the three apps it
provided live on as `ce_ui.users`, `ce_ui.authorization` and
`ce_ui.organizations`. ce-ui was its only consumer, and keeping the two apart
meant a synchronised release across two repositories for every change to
identity or authorization. See the README for the settings to update; there is
no database change to make, because the Django app labels are unchanged.

No further releases will be made here.

## 1.0.2 (2026-08-03)

- BUG: No longer stores a whitespace-only user name; added `User.display_name`

## 1.0.1 (2026-08-02)

- MAINT: Removed the `--changelog` option from the `notify_users` command. The
  changelog is no longer shipped to users; the component versions in the ce-ui
  side panel link to the repositories where the changelogs are published

## 1.0.0 (2026-07-31)

Initial release. This package contains the ORCID identity and permission
handling that was previously part of `topobank` and `ce-ui`.

- ENH: Anonymous user middleware, which substitutes the anonymous user only if
  one is configured
- BUG: Fixed a crash in `purge_user` and inconsistencies in authorization
- MAINT: Removed organization-based sharing (`OrganizationPermission`)
- MAINT: API view permissions moved to `topobank-rest-api`; removed
  django-guardian
- BUILD: Added pre-commit hooks and flake8 configuration
