
from django.urls import path

from journeys.views import (
    JourneyCancelView,
    JourneyCompleteView,
    JourneyDetailView,
    JourneyListCreateView,
    PassengerTravelPreferenceView,
)

urlpatterns = [
    # Driver journeys
    path("", JourneyListCreateView.as_view()),
    path("<int:pk>/", JourneyDetailView.as_view()),
    path("<int:pk>/cancel/", JourneyCancelView.as_view()),
    path("<int:pk>/complete/", JourneyCompleteView.as_view()),

    # Passenger registration travel preference
    path(
        "my-preference/",
        PassengerTravelPreferenceView.as_view(),
        name="my-travel-preference",
    ),
]
