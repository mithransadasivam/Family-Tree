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
    'axes',
    'users',
    'family_trees',
    'family_members',
    'relationships',
    'family_codes',
    'edit_history',
    'join_requests',
    'communities',
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
    'axes.middleware.AxesMiddleware',  # must be last: answers locked-out logins with a 429
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
        'community_search': '120/hour',
        'community_find': '60/hour',
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

# Where links in emails point. Set SITE_URL to the public address (e.g. https://kinship-family.netlify.app).
SITE_URL = os.getenv('SITE_URL', '').rstrip('/') or (WEB_ORIGINS[0] if WEB_ORIGINS else '')

# Join-request emails go out over SMTP once EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are set
# (for Gmail, an "app password"). Until then nothing is sent; in development they print to the console.
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', f'Kinship <{EMAIL_HOST_USER}>' if EMAIL_HOST_USER else 'Kinship <no-reply@localhost>')
if EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'utils.mail_backend.IPv4EmailBackend'
elif DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

# httpOnly auth cookies for the web client. If the web app and API are on different sites,
# set AUTH_COOKIE_SAMESITE=None (requires HTTPS); a same-origin proxy avoids that.
# Railway terminates HTTPS and forwards plain HTTP, saying so in X-Forwarded-Proto. Without this
# Django thinks every request is insecure, and the admin login form (a POST from an https origin)
# is rejected by the CSRF check.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# The admin uses a normal Django session: keep its cookies off plain HTTP in production.
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

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

# --- Admin login lockout (django-axes) -------------------------------------------------------
# The app itself signs people in with Google tokens and the API never calls authenticate(), so the
# only password login is the Django admin. This stops it being brute-forced.
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',  # first: refuses locked-out logins before any password check
    'django.contrib.auth.backends.ModelBackend',
]
AXES_ONLY_ADMIN_SITE = True        # nothing outside /admin/ is ever counted or locked
AXES_FAILURE_LIMIT = 5             # failed attempts before the account is locked
AXES_COOLOFF_TIME = timedelta(minutes=30)
AXES_RESET_ON_SUCCESS = True       # a good login clears the failure count
# Lock per account, not per IP: behind Railway's proxy every request seems to come from the proxy,
# and a client-supplied forwarded address can be spoofed to dodge a per-IP limit.
AXES_LOCKOUT_PARAMETERS = ['username']
AXES_USERNAME_CALLABLE = 'config.axes_helpers.normalized_username'  # Boss@x.com == boss@x.com
# To unlock early:  python manage.py axes_reset
# axes.W006 asks for 'ip_address' in AXES_LOCKOUT_PARAMETERS. Deliberately not done: behind Railway
# the app only sees the proxy's address (so an IP rule would lock everyone out together or do
# nothing), and a forwarded-for header is attacker-controlled. The lock is per account instead.
SILENCED_SYSTEM_CHECKS = ['axes.W006']
