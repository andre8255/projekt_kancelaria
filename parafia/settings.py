# parafia/settings.py
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY")
# cast=bool sprawia, że napis "True"/"False" z pliku .env zostanie zamieniony na poprawną wartość logiczną w Pythonie
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # nasze appki – dodamy za chwilę
    "konta.apps.KontaConfig",
    "osoby.apps.OsobyConfig",
    "rodziny.apps.RodzinyConfig",
    "msze.apps.MszeConfig",
    "sakramenty.apps.SakramentyConfig",
    "slowniki",
    "konfiguracja",
    "cmentarz",


]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "parafia.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # nasze globalne szablony
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",

                "konfiguracja.context_processors.dane_parafii",
            ],
        },
    },
]

WSGI_APPLICATION = "parafia.wsgi.application"
ASGI_APPLICATION = "parafia.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "pl"
TIME_ZONE = "Europe/Warsaw"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# LOGOWANIE
LOGIN_URL = "konta:logowanie"
LOGIN_REDIRECT_URL = "panel_start"     # wspólny dashboard po zalogowaniu
LOGOUT_REDIRECT_URL = "konta:logowanie"

# E-maile w trybie offline (nic nie wysyła)
EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"

# Szablony pokażą komunikaty (messages)
from django.contrib.messages import constants as messages
MESSAGE_TAGS = { messages.ERROR: "danger" }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
handler403 = "parafia.views.permission_denied_view"