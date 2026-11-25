# """Django settings for Route. Secrets and database credentials come from env."""
# import os
# from pathlib import Path

# BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "unsafe-development-key-change-me")
# DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"
# ALLOWED_HOSTS = [host.strip() for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()]

# INSTALLED_APPS = [
#     "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
#     "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
#     "rest_framework", "accounts", "profiles", "journeys", "ride_requests",
#     "matches", "notifications", "reviews", "reports",
# ]
# MIDDLEWARE = [
#     "django.middleware.security.SecurityMiddleware", "django.contrib.sessions.middleware.SessionMiddleware",
#     "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware",
#     "django.contrib.auth.middleware.AuthenticationMiddleware", "django.contrib.messages.middleware.MessageMiddleware",
#     "django.middleware.clickjacking.XFrameOptionsMiddleware",
# ]
# ROOT_URLCONF = "config.urls"
# TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": True,
#               "OPTIONS": {"context_processors": ["django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
# WSGI_APPLICATION = "config.wsgi.application"

# if os.environ.get("DB_ENGINE", "mysql").lower() == "sqlite":
#     DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": os.environ.get("DB_NAME", str(BASE_DIR / "db.sqlite3"))}}
# else:
#     DATABASES = {"default": {"ENGINE": "django.db.backends.mysql", "NAME": os.environ.get("DB_NAME", "routedb"),
#         "USER": os.environ.get("DB_USER", "root"), "PASSWORD": os.environ.get("DB_PASSWORD", "shreya"),
#         "HOST": os.environ.get("DB_HOST", "127.0.0.1"), "PORT": os.environ.get("DB_PORT", "3306"),
#         "OPTIONS": {"charset": "utf8mb4"}}}

# AUTH_PASSWORD_VALIDATORS = []
# LANGUAGE_CODE = "en-us"
# TIME_ZONE = "Asia/Kathmandu"
# USE_I18N = True
# USE_TZ = True
# STATIC_URL = "static/"
# DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST_FRAMEWORK = {
#     "DEFAULT_AUTHENTICATION_CLASSES": ["accounts.authentication.FirebaseAuthentication"],
#     "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
#     "EXCEPTION_HANDLER": "config.api.custom_exception_handler",
#     "DEFAULT_RENDERER_CLASSES": ["config.renderers.EnvelopeJSONRenderer"],
# }
# FIREBASE_CREDENTIALS = os.environ.get("FIREBASE_CREDENTIALS", "")


"""Django settings for Route project."""

import os
from pathlib import Path

import cloudinary
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# Security
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "unsafe-development-key-change-me"
)

DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS",
        "localhost,127.0.0.1"
    ).split(",")
    if host.strip()
]

# Applications
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

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# URLs
ROOT_URLCONF = "config.urls"

# Templates
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

# Database
if os.environ.get("DB_ENGINE", "mysql").lower() == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.environ.get(
                "DB_NAME",
                str(BASE_DIR / "db.sqlite3")
            ),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("DB_NAME", "routedb"),
            "USER": os.environ.get("DB_USER", "root"),
            "PASSWORD": os.environ.get("DB_PASSWORD", "shreya"),
            "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
            "PORT": os.environ.get("DB_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
            },
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = []

# Language and timezone
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kathmandu"
USE_I18N = True
USE_TZ = True

# Static files configuration
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Additional static directories (if available)
STATICFILES_DIRS = [
    BASE_DIR / "static",
] if (BASE_DIR / "static").exists() else []

# Default primary key
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework
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
}

# Firebase
FIREBASE_CREDENTIALS = os.environ.get(
    "FIREBASE_CREDENTIALS",
    ""
)

# Jazzmin configuration
JAZZMIN_SETTINGS = {
    "site_title": "Route Administration",
    "site_header": "Route",
    "site_brand": "Route",
    "welcome_sign": "Welcome to Route Administration",
    "copyright": "Route",
    "show_ui_builder": True,
    "navigation_expanded": True,
}
# Cloudinary credentials stay server-side and are never included in API serializers.
cloudinary.config(
    cloud_name=os.environ.get(" rlxbctlh"),
    api_key=os.environ.get("749848564177134"),
    api_secret=os.environ.get("iwe75n55HMoZ24ehbDBAyoT8g8Y"),
    secure=True,
)

CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", " rlxbctlh")
CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY", "749848564177134")
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET", "iwe75n55HMoZ24ehbDBAyoT8g8Y")
PROFILE_IMAGE_MAX_BYTES = int(os.environ.get(
    "PROFILE_IMAGE_MAX_BYTES", str(5 * 1024 * 1024)))
