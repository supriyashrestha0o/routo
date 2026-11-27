"""Django settings for the Route backend.

Secrets and environment-specific settings are loaded from ``.env``. Development
fallbacks are intentionally limited to local SQLite use; production raises an
error when required integration credentials are missing.
"""

import os
from pathlib import Path

import cloudinary
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    """Read a boolean environment variable."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    """Read a comma-separated environment variable."""
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


DEVELOPMENT_SECRET_KEY = "unsafe-development-key-change-me"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "").strip() or DEVELOPMENT_SECRET_KEY
DEBUG = env_bool("DJANGO_DEBUG", False)

if not DEBUG and (
    SECRET_KEY == DEVELOPMENT_SECRET_KEY
    or SECRET_KEY.startswith("replace-with-")
):
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY must be set to a strong random value when DJANGO_DEBUG is false."
    )

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
if not DEBUG and not ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must be configured in production.")

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "cloudinary",
    "rest_framework",
    "accounts",
    "profiles",
    "journeys",
    "ride_requests",
    "matches",
    "notifications",
    "reviews",
    "reports",
]

MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "config.middleware.MaxRequestBodySizeMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DB_ENGINE = os.environ.get("DB_ENGINE", "sqlite").strip().lower()
if DB_ENGINE == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.environ.get("DB_NAME", str(BASE_DIR / "db.sqlite3")),
        }
    }
else:
    mysql_required = ("DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST")
    mysql_missing = [name for name in mysql_required if not os.environ.get(name, "").strip()]
    if mysql_missing:
        raise ImproperlyConfigured(
            "MySQL is selected, but these environment variables are missing: "
            + ", ".join(mysql_missing)
        )

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ["DB_NAME"].strip(),
            "USER": os.environ["DB_USER"].strip(),
            "PASSWORD": os.environ["DB_PASSWORD"],
            "HOST": os.environ["DB_HOST"].strip(),
            "PORT": os.environ.get("DB_PORT", "3306"),
            "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "60")),
            "OPTIONS": {
                "charset": "utf8mb4",
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
                "ssl_mode": "REQUIRED",
            },
        }
    }

AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kathmandu"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "accounts.authentication.FirebaseAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "EXCEPTION_HANDLER": "config.api.custom_exception_handler",
    "DEFAULT_RENDERER_CLASSES": [
        "config.renderers.EnvelopeJSONRenderer",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.environ.get("API_ANON_RATE", "60/min"),
        "user": os.environ.get("API_USER_RATE", "240/min"),
    },
}

FIREBASE_CREDENTIALS = os.environ.get("FIREBASE_CREDENTIALS", "").strip()
CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "").strip()
CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY", "").strip()
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET", "").strip()

if all((CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET)):
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True,
    )

PROFILE_IMAGE_MAX_BYTES = int(
    os.environ.get("PROFILE_IMAGE_MAX_BYTES", str(5 * 1024 * 1024))
)
MAX_REQUEST_BODY_BYTES = int(
    os.environ.get(
        "MAX_REQUEST_BODY_BYTES",
        str(PROFILE_IMAGE_MAX_BYTES + (1024 * 1024)),
    )
)

if not DEBUG:
    missing_production_settings = []
    if (
        not FIREBASE_CREDENTIALS
        or FIREBASE_CREDENTIALS.startswith("path/to/")
        or not os.path.isfile(FIREBASE_CREDENTIALS)
    ):
        missing_production_settings.append("FIREBASE_CREDENTIALS")
    cloudinary_values = (
        CLOUDINARY_CLOUD_NAME,
        CLOUDINARY_API_KEY,
        CLOUDINARY_API_SECRET,
    )
    if not all(cloudinary_values) or any(
        value.startswith("your-") for value in cloudinary_values
    ):
        missing_production_settings.append("CLOUDINARY_* credentials")
    if missing_production_settings:
        raise ImproperlyConfigured(
            "Missing required production settings: "
            + ", ".join(missing_production_settings)
        )

# Transport security defaults are safe for direct HTTPS deployments. Set
# SECURE_HSTS_SECONDS explicitly after confirming every endpoint is HTTPS-only.
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", not DEBUG)
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", not DEBUG)
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", SECURE_HSTS_SECONDS > 0
)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)
SECURE_CONTENT_TYPE_NOSNIFF = True
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

if env_bool("DJANGO_TRUST_X_FORWARDED_PROTO", False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

JAZZMIN_SETTINGS = {
    "site_title": "Route Administration",
    "site_header": "Route",
    "site_brand": "Route",
    "welcome_sign": "Welcome to Route Administration",
    "copyright": "Route",
    "show_ui_builder": True,
    "navigation_expanded": True,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.environ.get("LOG_LEVEL", "INFO")},
}
