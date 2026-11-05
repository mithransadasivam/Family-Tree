"""Settings for running the test suite without a MySQL server:
    python manage.py test --settings=config.test_settings
"""
import os

os.environ.setdefault('SECRET_KEY', 'test-secret-key')

from .settings import *  # noqa: E402,F401,F403

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
# Throttle counters live in the cache; keep them out of the way of unrelated tests.
REST_FRAMEWORK = {**REST_FRAMEWORK, 'DEFAULT_THROTTLE_RATES': {
    'code_attempts': '1000/hour', 'community_search': '1000/hour', 'community_find': '1000/hour',
}}

# Real password hashing is deliberately slow; tests make many users.
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
