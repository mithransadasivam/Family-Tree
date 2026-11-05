"""Settings for running the test suite.

    python manage.py test --settings=config.test_settings                  # SQLite, no server needed
    TEST_DB=mysql python manage.py test --settings=config.test_settings    # the MySQL from .env
                                                                           # (a throwaway test_ database)
"""
import os

os.environ.setdefault('SECRET_KEY', 'test-secret-key')

from .settings import *  # noqa: E402,F401,F403

if os.environ.get("TEST_DB") != "mysql":
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
# Throttle counters live in the cache; keep them out of the way of unrelated tests.
REST_FRAMEWORK = {**REST_FRAMEWORK, 'DEFAULT_THROTTLE_RATES': {
    'code_attempts': '1000/hour', 'community_search': '1000/hour', 'community_find': '1000/hour',
}}

# Real password hashing is deliberately slow; tests make many users.
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# django-axes needs a real request to authenticate(), which Client.login() doesn't provide, and most
# tests have nothing to do with lockouts. The axes tests switch the real backends back on themselves.
AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']
