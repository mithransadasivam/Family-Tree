"""
Settings for Groot's browser tests: a real Kinship server on this computer only, with a throwaway
database file, a fresh build of the website, and no real email. Nothing here can reach the live site
or its data.
"""
import os
from pathlib import Path

from config.settings import *  # noqa: F401,F403

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': os.environ['GROOT_DB']}}
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
DEBUG = False
SECURE_SSL_REDIRECT = False
WEBAPP_DIR = Path(os.environ['GROOT_WEBAPP'])
WHITENOISE_ROOT = WEBAPP_DIR
AUTH_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SITE_URL = os.environ.get('GROOT_URL', 'http://127.0.0.1:8765')
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}
