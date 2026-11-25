from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

class FirebaseAuthentication(BaseAuthentication):
    """Verify Firebase ID tokens; SDK imports and credential setup are lazy."""
    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts:
            return None
        if parts[0].lower() != b"bearer" or len(parts) != 2:
            raise AuthenticationFailed("Use Authorization: Bearer <Firebase ID token>.")
        try:
            from firebase_admin import auth, credentials, get_app, initialize_app
            try:
                app = get_app()
            except ValueError:
                if not settings.FIREBASE_CREDENTIALS:
                    raise AuthenticationFailed("Firebase Admin credentials are not configured.")
                app = initialize_app(credentials.Certificate(settings.FIREBASE_CREDENTIALS))
            claims = auth.verify_id_token(parts[1].decode("ascii"), app=app, check_revoked=True)
        except AuthenticationFailed:
            raise
        except Exception as exc:
            raise AuthenticationFailed("Invalid or expired Firebase ID token.") from exc
        from routo.accounts.models import RouteUser
        user, _ = RouteUser.objects.update_or_create(
            firebase_uid=claims["uid"], defaults={"email": claims.get("email", "")})
        return user, claims

    def authenticate_header(self, request):
        return "Bearer"
