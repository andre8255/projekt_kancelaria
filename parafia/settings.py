# parafia/settings.py

from pathlib import Path

from decouple import config
from django.contrib.messages import constants as messages


# ======================================
#  ŚCIEŻKI BAZOWE
# ======================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ======================================
#  BEZPIECZEŃSTWO / ŚRODOWISKO
# ======================================

# Klucz trzymamy w .env
SECRET_KEY = config("SECRET_KEY")

# DEBUG pobierany z .env (True/False jako tekst → bool)
DEBUG = config("DEBUG", default=False, cast=bool)

# W środowisku produkcyjnym warto to też przerzucić do .env
ALLOWED_HOSTS: list[str] = []


# ======================================
#  APLIKACJE
# ======================================

INSTALLED_APPS = [
    # --- Django core ---
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # --- Aplikacje domenowe projektu ---
    "konta.apps.KontaConfig",
    "osoby.apps.OsobyConfig",
    "rodziny.apps.RodzinyConfig",
    "msze.apps.MszeConfig",
    "sakramenty.apps.SakramentyConfig",
    "slowniki.apps.SlownikiConfig",
    "konfiguracja.apps.KonfiguracjaConfig",
    "cmentarz.apps.CmentarzConfig",
]


# ======================================
#  MIDDLEWARE
# ======================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ======================================
#  URL / WSGI / ASGI
# ======================================

ROOT_URLCONF = "parafia.urls"

WSGI_APPLICATION = "parafia.wsgi.application"
ASGI_APPLICATION = "parafia.asgi.application"


# ======================================
#  SZABLONY
# ======================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # globalny katalog templates/
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # dane ustawień parafii dostępne globalnie w szablonach
                "konfiguracja.context_processors.dane_parafii",
            ],
        },
    },
]


# ======================================
#  BAZA DANYCH
# ======================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ======================================
#  LOKALIZACJA / CZAS
# ======================================

LANGUAGE_CODE = "pl"
TIME_ZONE = "Europe/Warsaw"

USE_I18N = True
USE_TZ = True


# ======================================
#  STATIC / MEDIA
# ======================================

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ======================================
#  LOGOWANIE / UWIERZYTELNIANIE
# ======================================

LOGIN_URL = "konta:logowanie"
# wspólny dashboard po zalogowaniu
LOGIN_REDIRECT_URL = "panel_start"
LOGOUT_REDIRECT_URL = "konta:logowanie"


# ======================================
#  E-MAIL
# ======================================

# W trybie developerskim nic nie wysyłamy, tylko „połykamy” maile.
EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"


# ======================================
#  KOMUNIKATY (django.contrib.messages)
# ======================================

MESSAGE_TAGS = {
    messages.ERROR: "danger",
}


# ======================================
#  INNE
# ======================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


