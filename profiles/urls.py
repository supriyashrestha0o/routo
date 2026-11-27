
from django.urls import path

from profiles.image_views import MyProfileImageUploadView
from profiles.views import MyProfileView, CompleteRegistrationView

urlpatterns = [
    path("me/", MyProfileView.as_view()),
    path("me/image/", MyProfileImageUploadView.as_view()),
    path("register/", CompleteRegistrationView.as_view(), name="complete-registration"),
]
