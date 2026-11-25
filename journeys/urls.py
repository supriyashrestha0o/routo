from django.urls import path
from journeys.views import JourneyCancelView, JourneyDetailView, JourneyListCreateView
urlpatterns = [path("", JourneyListCreateView.as_view()), path("<int:pk>/", JourneyDetailView.as_view()), path("<int:pk>/cancel/", JourneyCancelView.as_view())]
