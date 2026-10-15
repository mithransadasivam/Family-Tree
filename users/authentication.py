from urllib.parse import urlparse

from django.conf import settings
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication

SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')


class CookieJWTAuthentication(JWTAuthentication):
    """
    JWT auth that also accepts the access token from an httpOnly cookie (web client).

    An Authorization header still wins, so the Android app is unaffected. Browsers attach
    cookies automatically, so cookie-authenticated writes must come from an allowed origin
    (CSRF defence).
    """

    def authenticate(self, request):
        if request.META.get('HTTP_AUTHORIZATION'):
            return super().authenticate(request)

        raw_token = request.COOKIES.get(settings.AUTH_COOKIE_ACCESS)
        if not raw_token:
            return None

        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)

        if request.method not in SAFE_METHODS:
            origin = request.META.get('HTTP_ORIGIN')
            # The site served by this very backend counts as an allowed origin, as do the
            # separately hosted origins listed in WEB_ORIGINS.
            same_site = bool(origin) and urlparse(origin).netloc == request.get_host()
            if not same_site and origin not in settings.WEB_ORIGINS:
                raise PermissionDenied('Origin not allowed')

        return user, validated_token
