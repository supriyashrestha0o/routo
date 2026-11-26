"""Cloudinary operations used by profile image uploads."""
from django.conf import settings
from cloudinary import uploader


ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


def default_profile_full_name(user):
    """Return a safe display-name default for a newly created profile."""
    return (user.email or "Student")[:120]


def upload_profile_image(image):
    """Upload an already validated image and return Cloudinary metadata."""
    if not all((settings.CLOUDINARY_CLOUD_NAME, settings.CLOUDINARY_API_KEY, settings.CLOUDINARY_API_SECRET)):
        raise RuntimeError("Cloudinary is not configured on the server.")
    return uploader.upload(
        image,
        folder="route/profile_images",
        resource_type="image",
        allowed_formats=["jpg", "jpeg", "png", "webp"],
        use_filename=False,
        unique_filename=True,
    )


def delete_cloudinary_image(public_id):
    if public_id:
        return uploader.destroy(public_id, resource_type="image", invalidate=True)
