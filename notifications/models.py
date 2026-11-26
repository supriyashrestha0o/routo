import hashlib

from django.db import models


class DeviceToken(models.Model):
    user = models.ForeignKey(
        "accounts.RouteUser",
        on_delete=models.CASCADE,
        related_name="device_tokens",
    )
    token = models.CharField(max_length=512)
    token_hash = models.CharField(max_length=64, unique=True, editable=False)
    platform = models.CharField(max_length=16, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def hash_token(token):
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def save(self, *args, **kwargs):
        self.token_hash = self.hash_token(self.token)
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            kwargs["update_fields"] = set(update_fields) | {"token_hash"}
        super().save(*args, **kwargs)
