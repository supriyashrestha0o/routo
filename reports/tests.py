from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import RouteUser
from reports.models import Report


class ReportDeletionTests(TestCase):
    def setUp(self):
        self.reporter = RouteUser.objects.create(
            firebase_uid="report-reporter",
            email="reporter@example.com",
        )
        self.other_reporter = RouteUser.objects.create(
            firebase_uid="other-report-reporter",
            email="other-reporter@example.com",
        )
        self.reported_user = RouteUser.objects.create(
            firebase_uid="reported-user",
            email="reported@example.com",
        )
        self.second_reported_user = RouteUser.objects.create(
            firebase_uid="second-reported-user",
            email="second-reported@example.com",
        )

    def test_deleting_reported_user_deletes_all_reports_about_that_user(self):
        Report.objects.create(
            reporter=self.reporter,
            reported_user=self.reported_user,
            description="First report",
        )
        Report.objects.create(
            reporter=self.other_reporter,
            reported_user=self.reported_user,
            description="Second report",
        )

        reported_user_id = self.reported_user.pk
        self.reported_user.delete()

        self.assertFalse(
            Report.objects.filter(reported_user_id=reported_user_id).exists()
        )

    def test_admin_can_delete_multiple_reported_users_in_one_action(self):
        first_report = Report.objects.create(
            reporter=self.reporter,
            reported_user=self.reported_user,
            description="First report",
        )
        duplicate_report = Report.objects.create(
            reporter=self.other_reporter,
            reported_user=self.reported_user,
            description="Another report about the same user",
        )
        second_report = Report.objects.create(
            reporter=self.reporter,
            reported_user=self.second_reported_user,
            description="Second reported user",
        )

        admin_user = get_user_model().objects.create_superuser(
            username="report-admin",
            email="admin@example.com",
            password="test-password",
        )
        self.client.force_login(admin_user)

        response = self.client.post(
            reverse("admin:reports_report_changelist"),
            {
                "action": "delete_reported_users",
                "_selected_action": [
                    str(first_report.pk),
                    str(duplicate_report.pk),
                    str(second_report.pk),
                ],
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(RouteUser.objects.filter(pk=self.reported_user.pk).exists())
        self.assertFalse(
            RouteUser.objects.filter(pk=self.second_reported_user.pk).exists()
        )
        self.assertFalse(
            Report.objects.filter(
                reported_user_id__in=[self.reported_user.pk, self.second_reported_user.pk]
            ).exists()
        )
