from django.conf import settings
from django.shortcuts import reverse
from django.urls import NoReverseMatch

from .anonymous import get_anonymous_user

HEADLESS_ONLY = hasattr(settings, "HEADLESS_ONLY") and settings.HEADLESS_ONLY

# Default to headful mode, but allow to switch to headless mode
_no_anonymous_substitution_urls = []
if not HEADLESS_ONLY:
    # some abbreviations in order to save time on every request
    try:
        _no_anonymous_substitution_urls += [reverse("account_signup")]
    except NoReverseMatch:
        pass
    try:
        _no_anonymous_substitution_urls += [reverse("account_login")]
    except NoReverseMatch:
        pass


def anonymous_user_middleware(get_response):
    """Modify user of each request if not authenticated.

    Parameters
    ----------
    get_response
        Function which returns response giving a request.

    Returns
    -------
    Middleware function. Can be used in configuration of MIDDLEWARE.
    """

    def middleware(request):
        if HEADLESS_ONLY:
            if not request.user.is_authenticated:
                request.user = get_anonymous_user()
        else:
            if not (
                request.user.is_authenticated
                or request.path in _no_anonymous_substitution_urls
            ):
                request.user = get_anonymous_user()

        response = get_response(request)
        return response

    return middleware
