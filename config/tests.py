import json

from django.conf import settings
from django.http import JsonResponse
from django.test import Client, RequestFactory, TestCase, override_settings

from config.api import custom_exception_handler
from config.middleware import MaxRequestBodySizeMiddleware


class HealthApiTests(TestCase):
    @override_settings(
        FIREBASE_CREDENTIALS=str(settings.BASE_DIR / "manage.py"),
        CLOUDINARY_CLOUD_NAME="cloud",
        CLOUDINARY_API_KEY="key",
        CLOUDINARY_API_SECRET="secret",
    )
    def test_health_is_ready_when_database_and_integrations_are_configured(self):
        response = Client().get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    @override_settings(
        FIREBASE_CREDENTIALS="",
        CLOUDINARY_CLOUD_NAME="",
        CLOUDINARY_API_KEY="",
        CLOUDINARY_API_SECRET="",
    )
    def test_health_reports_degraded_when_integrations_are_missing(self):
        response = Client().get("/health")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "degraded")
        self.assertEqual(response.json()["checks"]["database"], "ok")

    @override_settings(MAX_REQUEST_BODY_BYTES=10)
    def test_oversized_request_is_rejected_before_parsing(self):
        request = RequestFactory().post("/health", data=b"x" * 20, content_type="text/plain")
        request.META["CONTENT_LENGTH"] = "20"
        middleware = MaxRequestBodySizeMiddleware(
            lambda _request: JsonResponse({"success": True})
        )

        response = middleware(request)

        self.assertEqual(response.status_code, 413)
        self.assertFalse(json.loads(response.content)["success"])


class ErrorHandlerTests(TestCase):
    def test_unexpected_exception_uses_json_error_contract(self):
        with self.assertLogs("config.api", level="ERROR"):
            response = custom_exception_handler(
                RuntimeError("sensitive internal detail"), {"view": None}
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data["success"], False)
        self.assertEqual(response.data["error"], "Internal server error.")
        self.assertNotIn("sensitive", str(response.data))
