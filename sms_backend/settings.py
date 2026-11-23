"""Django settings for the student management backend."""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _csv(name, default=""):
    return [v.strip() for v in os.environ.get(name, default).split(",") if v.strip()]


# --- Core -----------------------------------------------------------------
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-only-insecure-key-change-me"
    else:
        raise ImproperlyConfigured(
            "Set the DJANGO_SECRET_KEY environment variable when DJANGO_DEBUG is not 1."
        )

ALLOWED_HOSTS = _csv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = _csv("DJANGO_CSRF_TRUSTED_ORIGINS")

# Origins (your React site) that may call this API from a browser.
CORS_ALLOWED_ORIGINS = _csv(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
)

# --- Apps / middleware ----------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "students",
]

MIDDLEWARE = [
    "students.middleware.SimpleCorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "sms_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "sms_backend.wsgi.application"
ASGI_APPLICATION = "sms_backend.asgi.application"

# --- Database -------------------------------------------------------------
# SQLite is fine for development and small deployments. Switch to PostgreSQL
# for production use.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- i18n -----------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# --- Static & uploaded files ---------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Maximum size of an uploaded student photo.
PHOTO_MAX_BYTES = 2 * 1024 * 1024  # 2 MB

# --- Auth tokens ----------------------------------------------------------
AUTH_TOKEN_MAX_AGE = 60 * 60 * 24 * 7  # login stays valid for 7 days

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
