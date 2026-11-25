from django.urls import path
from routo.profiles.image_views import MyProfileImageUploadView
from routo.profiles.views import MyProfileView
urlpatterns = [
    path("me/", MyProfileView.as_view()),
    path("me/image/", MyProfileImageUploadView.as_view()),
]
