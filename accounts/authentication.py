from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed


def sync_route_user(claims):
    """Create or update the local account represented by Firebase claims."""
    from accounts.models import BlockedFirebaseIdentity, RouteUser

    firebase_uid = claims.get("uid")
    if not firebase_uid:
        raise AuthenticationFailed("Firebase token is missing a user ID.")

    if BlockedFirebaseIdentity.objects.filter(firebase_uid=firebase_uid).exists():
        raise AuthenticationFailed("This Firebase account has been blocked.")

    claimed_email = claims.get("email") or ""
    user, created = RouteUser.objects.get_or_create(
        firebase_uid=firebase_uid,
        defaults={"email": claimed_email},
    )

    if not created and claimed_email and user.email != claimed_email:
        user.email = claimed_email
        user.save(update_fields=["email", "updated_at"])

    return user


class FirebaseAuthentication(BaseAuthentication):
    """Verify Firebase ID tokens; SDK imports and credential setup are lazy."""
    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts:
            return None
        if parts[0].lower() != b"bearer" or len(parts) != 2:
            raise AuthenticationFailed("Use Authorization: Bearer <Firebase ID token>.")
        try:
            from firebase_admin import auth, credentials, get_app, initialize_app  # type: ignore[import-not-found]
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
        user = sync_route_user(claims)
        return user, claims

    def authenticate_header(self, request):
        return "Bearer"
