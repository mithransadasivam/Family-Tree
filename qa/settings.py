"""Settings for the QA checks: a throwaway in-memory database, so nothing real is ever touched."""
from config.settings import *  # noqa: F401,F403

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
ALLOWED_HOSTS = ['*']
SECURE_SSL_REDIRECT = False
SITE_URL = 'https://kinship.test'
# No real mail, and no rate limits (the fuzzer sends far more requests than a person would).
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}
