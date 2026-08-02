# Changelog for plugin *topobank-orcid*

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
