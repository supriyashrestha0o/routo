from django.urls import path
from journeys.views import JourneyCancelView, JourneyCompleteView, JourneyDetailView, JourneyListCreateView

urlpatterns = [
    path("", JourneyListCreateView.as_view()),
    path("<int:pk>/", JourneyDetailView.as_view()),
    path("<int:pk>/cancel/", JourneyCancelView.as_view()),
    path("<int:pk>/complete/", JourneyCompleteView.as_view()),
]
