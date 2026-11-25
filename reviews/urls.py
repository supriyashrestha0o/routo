from django.urls import path
from routo.reviews.views import ReviewListCreateView
urlpatterns = [path("", ReviewListCreateView.as_view())]
