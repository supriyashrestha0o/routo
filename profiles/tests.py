from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test import override_settings
from PIL import Image
from rest_framework.test import APIClient

from accounts.models import RouteUser
from profiles.models import Profile


def valid_png(name="profile.png"):
    data = BytesIO()
    Image.new("RGB", (16, 16), color="blue").save(data, format="PNG")
    return SimpleUploadedFile(name, data.getvalue(), content_type="image/png")


def unsupported_gif():
    data = BytesIO()
    Image.new("RGB", (16, 16), color="green").save(data, format="GIF")
    return SimpleUploadedFile("profile.gif", data.getvalue(), content_type="image/png")


class ProfileApiTests(TestCase):
    def setUp(self):
        self.user = RouteUser.objects.create(firebase_uid="profile-user")
        self.client = APIClient(); self.client.force_authenticate(self.user)
    def test_profile_create_and_update(self):
        response = self.client.put("/api/profiles/me/", {
            "full_name": "Student", "university": "Route U", "is_driver": True,
            "profile_image_url": "https://attacker.invalid/image.png",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.university, "Route U")
        self.assertEqual(profile.profile_image_url, "")


class ProfileImageUploadTests(TestCase):
    endpoint = "/api/profiles/me/image/"
    cloudinary_result = {
        "secure_url": "https://res.cloudinary.com/route/image/upload/profile/new.png",
        "public_id": "route/profile_images/new",
    }

    def setUp(self):
        self.user = RouteUser.objects.create(firebase_uid="image-owner", email="owner@example.com")
        self.other = RouteUser.objects.create(firebase_uid="image-other")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    @patch("profiles.services.uploader.upload")
    def test_successful_upload_saves_and_returns_secure_url(self, upload):
        upload.return_value = self.cloudinary_result
        response = self.client.post(self.endpoint, {"image": valid_png()}, format="multipart")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["data"]["profile_image"], self.cloudinary_result["secure_url"])
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.profile_image_url, self.cloudinary_result["secure_url"])
        self.assertEqual(profile.profile_image_public_id, self.cloudinary_result["public_id"])

    @patch("profiles.services.uploader.upload")
    def test_rejects_invalid_file_content(self, upload):
        invalid = SimpleUploadedFile("photo.jpg", b"not an image", content_type="image/jpeg")
        response = self.client.post(self.endpoint, {"image": invalid}, format="multipart")
        self.assertEqual(response.status_code, 400)
        upload.assert_not_called()

    @patch("profiles.services.uploader.upload")
    def test_rejects_unsupported_but_well_formed_image(self, upload):
        response = self.client.post(self.endpoint, {"image": unsupported_gif()}, format="multipart")
        self.assertEqual(response.status_code, 400)
        upload.assert_not_called()

    @override_settings(PROFILE_IMAGE_MAX_BYTES=64)
    @patch("profiles.services.uploader.upload")
    def test_rejects_file_over_configured_size_limit(self, upload):
        response = self.client.post(self.endpoint, {"image": valid_png()}, format="multipart")
        self.assertEqual(response.status_code, 400)
        upload.assert_not_called()

    def test_unauthenticated_upload_is_rejected(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.endpoint, {"image": valid_png()}, format="multipart")
        self.assertEqual(response.status_code, 401)

    @patch("profiles.services.uploader.upload", side_effect=RuntimeError("provider failure"))
    def test_cloudinary_failure_does_not_change_profile(self, upload):
        profile = Profile.objects.create(
            user=self.user, full_name="Owner", profile_image_url="https://res.cloudinary.com/route/old.png",
            profile_image_public_id="route/profile_images/old",
        )
        response = self.client.post(self.endpoint, {"image": valid_png()}, format="multipart")
        self.assertEqual(response.status_code, 502)
        profile.refresh_from_db()
        self.assertEqual(profile.profile_image_url, "https://res.cloudinary.com/route/old.png")
        self.assertEqual(profile.profile_image_public_id, "route/profile_images/old")

    @patch("profiles.services.uploader.destroy")
    @patch("profiles.services.uploader.upload")
    def test_replacing_image_updates_record_and_deletes_old_asset(self, upload, destroy):
        profile = Profile.objects.create(
            user=self.user, full_name="Owner", profile_image_url="https://res.cloudinary.com/route/old.png",
            profile_image_public_id="route/profile_images/old",
        )
        upload.return_value = self.cloudinary_result
        response = self.client.post(self.endpoint, {"image": valid_png()}, format="multipart")
        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertEqual(profile.profile_image_public_id, self.cloudinary_result["public_id"])
        destroy.assert_called_once_with("route/profile_images/old", resource_type="image", invalidate=True)

    @patch("profiles.services.uploader.destroy", side_effect=RuntimeError("cleanup failure"))
    @patch("profiles.services.uploader.upload")
    def test_old_image_deletion_failure_keeps_new_database_reference(self, upload, destroy):
        profile = Profile.objects.create(user=self.user, full_name="Owner", profile_image_public_id="route/old")
        upload.return_value = self.cloudinary_result
        response = self.client.post(self.endpoint, {"image": valid_png()}, format="multipart")
        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertEqual(profile.profile_image_public_id, self.cloudinary_result["public_id"])

    @patch("profiles.services.uploader.upload")
    def test_cannot_upload_to_another_users_profile(self, upload):
        response = self.client.post(f"/api/profiles/{self.other.pk}/image/", {"image": valid_png()}, format="multipart")
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Profile.objects.filter(user=self.other).exists())
        upload.assert_not_called()
