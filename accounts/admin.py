from django.contrib import admin

from accounts.models import BlockedFirebaseIdentity, RouteUser


admin.site.register(RouteUser)


@admin.register(BlockedFirebaseIdentity)
class BlockedFirebaseIdentityAdmin(admin.ModelAdmin):
    list_display = (
        "firebase_uid",
        "email",
        "reason",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = (
        "firebase_uid",
        "email",
        "reason",
    )
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
