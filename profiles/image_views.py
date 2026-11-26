import warnings

from PIL import Image, UnidentifiedImageError
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from profiles.models import Profile
from profiles.services import (
    default_profile_full_name,
    delete_cloudinary_image,
    upload_profile_image,
)


class CloudinaryUnavailable(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "Image storage is temporarily unavailable. Please try again."
    default_code = "image_storage_unavailable"


def validate_profile_image(image: UploadedFile) -> None:
    max_bytes = settings.PROFILE_IMAGE_MAX_BYTES
    if image.size > max_bytes:
        limit_mb = max_bytes / (1024 * 1024)
        raise ValidationError({"image": f"Image must be no larger than {limit_mb:g} MB."})
    try:
        image.seek(0)
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(image) as decoded:
                actual_format = decoded.format
                width, height = decoded.size
                decoded.verify()
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise ValidationError({"image": "Upload a valid JPEG, PNG, or WebP image."})
    finally:
        image.seek(0)
    if actual_format not in {"JPEG", "PNG", "WEBP"}:
        raise ValidationError({"image": "Only JPEG, PNG, and WebP images are supported."})
    if width <= 0 or height <= 0 or width * height > 40_000_000:
        raise ValidationError({"image": "Image dimensions are too large."})


class MyProfileImageUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        image = request.FILES.get("image")
        if image is None:
            raise ValidationError({"image": "This multipart field is required."})
        validate_profile_image(image)

        profile, _ = Profile.objects.get_or_create(
            user=request.user,
            defaults={"full_name": default_profile_full_name(request.user)},
        )
        previous_public_id = profile.profile_image_public_id
        try:
            uploaded = upload_profile_image(image)
            secure_url = uploaded.get("secure_url")
            public_id = uploaded.get("public_id")
            if not secure_url or not secure_url.startswith("https://") or not public_id:
                raise RuntimeError("Cloudinary returned incomplete image metadata.")
        except Exception as exc:
            raise CloudinaryUnavailable() from exc

        profile.profile_image_url = secure_url
        profile.profile_image_public_id = public_id
        try:
            profile.save(update_fields=("profile_image_url", "profile_image_public_id", "updated_at"))
        except Exception:
            try:
                delete_cloudinary_image(public_id)
            except Exception:
                pass
            raise

        # Keep the new DB reference even if cleanup of an old Cloudinary asset fails.
        if previous_public_id and previous_public_id != public_id:
            try:
                delete_cloudinary_image(previous_public_id)
            except Exception:
                pass

        return Response({
            "success": True,
            "data": {
                "message": "Profile image uploaded successfully",
                "profile_image": secure_url,
            },
        }, status=status.HTTP_200_OK)
