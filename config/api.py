"""Consistent JSON error handling for API responses."""

import logging

from rest_framework.response import Response
from rest_framework.views import exception_handler


logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Return the documented JSON envelope for API and unexpected errors."""
    response = exception_handler(exc, context)
    if response is not None:
        if isinstance(response.data, dict):
            detail = response.data.get("detail", response.data)
        else:
            detail = response.data
        response.data = {
            "success": False,
            "error": detail,
            "status": response.status_code,
        }
        return response

    # DRF only recognizes its own exception classes. Convert anything else into
    # the same JSON contract instead of allowing Django's HTML 500 page through.
    logger.error(
        "Unhandled API exception in %s",
        context.get("view"),
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return Response(
        {"success": False, "error": "Internal server error.", "status": 500},
        status=500,
    )
