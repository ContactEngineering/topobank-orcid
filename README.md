# topobank-orcid

> **Deprecated — this package has moved into
> [ce-ui](https://github.com/ContactEngineering/ce-ui).**
>
> The three Django apps it provided now live there as `ce_ui.users`,
> `ce_ui.authorization` and `ce_ui.organizations`, and that is where changes
> to them are made. This repository is kept for the history and for
> deployments that have not yet moved; it receives no further releases.

ORCID identity and permission handling for Topobank: the user model, the
permission set, and organizations.

## Migrating away from this package

The Django app labels are unchanged (`users`, `authorization`,
`organizations`), so there is no database change to make: recorded migrations
are keyed on the label, not on the module path. Uninstall `topobank-orcid`,
take `ce-ui` 1.39 or later, and update the dotted paths in your settings:

| before | after |
| --- | --- |
| `topobank_orcid.users.apps.UsersAppConfig` | `ce_ui.users.apps.UsersAppConfig` |
| `topobank_orcid.authorization.apps.AuthorizationAppConfig` | `ce_ui.authorization.apps.AuthorizationAppConfig` |
| `topobank_orcid.organizations.apps.OrganizationsAppConfig` | `ce_ui.organizations.apps.OrganizationsAppConfig` |
| `topobank_orcid.users.anonymous.get_anonymous_user` | `ce_ui.users.anonymous.get_anonymous_user` |
| `topobank_orcid.users.middleware.anonymous_user_middleware` | `ce_ui.users.middleware.anonymous_user_middleware` |
| `topobank_orcid.users.adapters.AccountAdapter` | `ce_ui.users.adapters.AccountAdapter` |
| `topobank_orcid.users.adapters.SocialAccountAdapter` | `ce_ui.users.adapters.SocialAccountAdapter` |
| `topobank_orcid.users.forms.SignupFormWithName` | `ce_ui.users.forms.SignupFormWithName` |

`AUTH_USER_MODEL`, `TOPOBANK_PERMISSION_MODEL` and
`TOPOBANK_ORGANIZATION_MODEL` keep their values, since those name app labels.

A deployment that brings its own user and authorization models is unaffected
either way: those settings are topobank's extension points, and this package
was only one implementation of them.
