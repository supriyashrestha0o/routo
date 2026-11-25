from django.conf import settings

def send_push(user, title, body, data=None):
    """Best-effort FCM delivery. The event is retained in MySQL domain state."""
    tokens = list(user.device_tokens.filter(active=True).values_list("token", flat=True))
    if not tokens:
        return 0
    try:
        from firebase_admin import credentials, get_app, initialize_app, messaging
        try:
            app = get_app()
        except ValueError:
            if not settings.FIREBASE_CREDENTIALS:
                return 0
            app = initialize_app(credentials.Certificate(settings.FIREBASE_CREDENTIALS))
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body), data={str(k): str(v) for k, v in (data or {}).items()}, tokens=tokens)
        result = messaging.send_each_for_multicast(message, app=app)
        for token, response in zip(tokens, result.responses):
            if not response.success and getattr(response.exception, "code", "") in ("registration-token-not-registered", "invalid-argument"):
                user.device_tokens.filter(token=token).update(active=False)
        return result.success_count
    except Exception:
        # Push transport issues must not roll back an accepted ride or request.
        return 0
