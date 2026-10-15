from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'users',
    'family_trees',
    'family_members',
    'relationships',
    'family_codes',
    'edit_history',
    'join_requests',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('MYSQLDATABASE', os.getenv('DB_NAME')),
        'USER': os.getenv('MYSQLUSER', os.getenv('DB_USER')),
        'PASSWORD': os.getenv('MYSQLPASSWORD', os.getenv('DB_PASSWORD')),
        'HOST': os.getenv('MYSQLHOST', os.getenv('DB_HOST', 'localhost')),
        'PORT': os.getenv('MYSQLPORT', os.getenv('DB_PORT', '3306')),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'users.authentication.CookieJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # Per-account cap on family-code attempts (redeeming / sending join requests).
    'DEFAULT_THROTTLE_RATES': {
        'code_attempts': '30/hour',
    },
}

from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
}

# Web client origins (comma-separated), e.g. https://kinship.vercel.app. The Android app is
# not a browser, so it is unaffected by CORS.
WEB_ORIGINS = [
    o.strip()
    for o in os.getenv('WEB_ORIGINS', 'http://localhost:5173' if DEBUG else '').split(',')
    if o.strip()
]
CORS_ALLOWED_ORIGINS = WEB_ORIGINS
CORS_ALLOW_CREDENTIALS = True  # lets the browser send the auth cookies

# httpOnly auth cookies for the web client. If the web app and API are on different sites,
# set AUTH_COOKIE_SAMESITE=None (requires HTTPS); a same-origin proxy avoids that.
AUTH_COOKIE_ACCESS = 'kinship_access'
AUTH_COOKIE_REFRESH = 'kinship_refresh'
AUTH_COOKIE_SECURE = not DEBUG
AUTH_COOKIE_SAMESITE = os.getenv('AUTH_COOKIE_SAMESITE', 'Lax')
AUTH_COOKIE_DOMAIN = os.getenv('AUTH_COOKIE_DOMAIN') or None

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []

# The built Kinship website (Vite output) lives in webapp/ and is served from the site root by
# WhiteNoise; unknown non-API paths fall through to webapp/index.html (see config/urls.py).
WEBAPP_DIR = BASE_DIR / 'webapp'
WHITENOISE_ROOT = WEBAPP_DIR
# Vite names everything in assets/ with a content hash, so browsers may cache it forever.
WHITENOISE_IMMUTABLE_FILE_TEST = lambda path, url: url.startswith('/assets/')  # noqa: E731

# Google Sign-In's popup needs to talk back to this page; Django's default
# ('same-origin') severs that link and breaks the web sign-in button.
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin-allow-popups'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
# GOOGLE_CLIENT_ID may hold several comma-separated client IDs (e.g. Android web-client + web app).
GOOGLE_CLIENT_IDS = [c.strip() for c in (GOOGLE_CLIENT_ID or '').split(',') if c.strip()]

AUTH_USER_MODEL = 'users.User'
