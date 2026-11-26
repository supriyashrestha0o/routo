from django.contrib import admin
from django.contrib.messages import constants as message_constants

from accounts.models import BlockedFirebaseIdentity, RouteUser
from reports.models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "reporter",
        "reported_user",
        "journey",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "reporter__firebase_uid",
        "reporter__email",
        "reported_user__firebase_uid",
        "reported_user__email",
        "description",
    )
    actions = ("delete_reported_users",)

    def has_delete_reported_users_permission(self, request):
        """Require both report deletion and Firebase-user deletion rights."""
        return request.user.has_perm(
            "reports.delete_report"
        ) and request.user.has_perm("accounts.delete_routeuser")

    @admin.action(
        description="Delete selected reported users and all of their reports",
        permissions=("delete_reported_users",),
    )
    def delete_reported_users(self, request, queryset):
        """Delete each distinct reported user selected in the report list.

        Deleting a RouteUser cascades to every report where that account is
        either the reporter or the reported user. This intentionally removes
        additional reports about the user that were not part of the initial
        selection. A Firebase identity tombstone is retained so the deleted
        account cannot be automatically recreated by its next valid token.
        """
        reported_user_ids = set(
            queryset.values_list("reported_user_id", flat=True).distinct()
        )
        if not reported_user_ids:
            self.message_user(
                request,
                "No reported users were selected.",
                level=message_constants.WARNING,
            )
            return

        blocked_users = list(
            RouteUser.objects.filter(pk__in=reported_user_ids).values(
                "firebase_uid", "email"
            )
        )
        BlockedFirebaseIdentity.objects.bulk_create(
            [
                BlockedFirebaseIdentity(
                    firebase_uid=user["firebase_uid"],
                    email=user["email"],
                    reason="Deleted through report moderation",
                )
                for user in blocked_users
            ],
            ignore_conflicts=True,
        )
        RouteUser.objects.filter(pk__in=reported_user_ids).delete()
        self.message_user(
            request,
            f"Deleted {len(reported_user_ids)} reported user(s) and all related reports.",
            level=message_constants.SUCCESS,
        )
