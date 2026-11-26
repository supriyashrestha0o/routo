"""Request-level safeguards for the API."""

from django.conf import settings
from django.http import JsonResponse


class MaxRequestBodySizeMiddleware:
    """Reject oversized request bodies before Django parses multipart data."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        maximum = getattr(settings, "MAX_REQUEST_BODY_BYTES", 0)
        content_length = request.META.get("CONTENT_LENGTH")
        if maximum and content_length:
            try:
                request_size = int(content_length)
            except (TypeError, ValueError):
                request_size = 0
            if request_size > maximum:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {
                            "detail": f"Request body must be no larger than {maximum} bytes."
                        },
                        "status": 413,
                    },
                    status=413,
                )
        return self.get_response(request)
