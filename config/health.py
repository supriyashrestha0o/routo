"""Readiness checks used by deployment platforms and monitoring tools."""

import os

from django.conf import settings
from django.db import connection
from django.http import JsonResponse


def health(request):
    """Return service readiness, including database and integration checks."""
    checks = {
        "database": "unavailable",
        "firebase": "not_configured",
        "cloudinary": "not_configured",
    }

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks["database"] = "ok"
    except Exception:
        # Do not expose database details to unauthenticated health requests.
        pass

    if settings.FIREBASE_CREDENTIALS and os.path.isfile(
        settings.FIREBASE_CREDENTIALS
    ):
        checks["firebase"] = "ok"
    if all(
        (
            settings.CLOUDINARY_CLOUD_NAME,
            settings.CLOUDINARY_API_KEY,
            settings.CLOUDINARY_API_SECRET,
        )
    ):
        checks["cloudinary"] = "ok"

    ready = all(value == "ok" for value in checks.values())
    payload = {
        "status": "ok" if ready else "degraded",
        "checks": checks,
    }
    return JsonResponse(payload, status=200 if ready else 503)
