# Changelog for plugin *topobank-orcid*

## 1.1.0 (not yet released)

- ENH: Users can connect more than one identity to their account. ORCID is no
  longer the only way in: a deployment can also offer Google and local
  email/password accounts, and an account registered with an email address can
  gain an ORCID iD later
- ENH: `User.has_orcid` and `User.connected_identities` describe which
  identities an account carries; `topobank_orcid.users.identity` holds the
  policy that publishing a dataset requires a connected ORCID iD, and
  `topobank_orcid.users.decorators` enforces it on the publication routes
- ENH: Social accounts can be disconnected, as long as at least one way to sign
  back in (another connected account or a password) remains
- ENH: `ACCOUNT_ALLOW_SIGNUP` switches local registration on or off without
  also closing social sign-in
- BUG: `AccountAdapter.save_user` returns the saved user, as django-allauth
  expects, and no longer overwrites a name derived from first and last name

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
